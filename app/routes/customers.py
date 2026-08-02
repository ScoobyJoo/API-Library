from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from app.models import Customer
from app.db import db

customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')

# List all customers
@customers_bp.route('', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers]), 200

# Create a new customer
@customers_bp.route('', methods=['POST'])
def create_customer():
    data = request.get_json(silent=True) or {}
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')

    # Validate required fields
    if not first_name or not last_name or not email:
        return jsonify({"error": "'first_name', 'last_name' and 'email' are required"}), 400

    membership_date = data.get('membership_date')
    if membership_date:
        try:
            membership_date = date.fromisoformat(membership_date)
        except ValueError:
            return jsonify({"error": "'membership_date' must be in YYYY-MM-DD format"}), 400

    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=data.get('phone'),
        **({"membership_date": membership_date} if membership_date else {}),
    )
    db.session.add(customer)
    try:
        db.session.commit()
        # Check for duplicate email
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A customer with that email already exists"}), 409

    return jsonify(customer.to_dict()), 201

# Get a specific customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    # Validate that the customer exists
    if customer is None:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer.to_dict()), 200

# Update an existing customer
@customers_bp.route('/<int:customer_id>', methods=['PUT', 'PATCH'])
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True) or {}

    if 'first_name' in data:
        if not data['first_name']:
            return jsonify({"error": "'first_name' cannot be empty"}), 400
        customer.first_name = data['first_name']
    if 'last_name' in data:
        if not data['last_name']:
            return jsonify({"error": "'last_name' cannot be empty"}), 400
        customer.last_name = data['last_name']
    if 'email' in data:
        if not data['email']:
            return jsonify({"error": "'email' cannot be empty"}), 400
        customer.email = data['email']
    if 'phone' in data:
        customer.phone = data['phone']
    if 'membership_date' in data:
        try:
            customer.membership_date = date.fromisoformat(data['membership_date'])
        except (TypeError, ValueError):
            return jsonify({"error": "'membership_date' must be in YYYY-MM-DD format"}), 400

    try:
        db.session.commit()
    # Check for duplicate email
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A customer with that email already exists"}), 409

    return jsonify(customer.to_dict()), 200

# Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return jsonify({"error": "Customer not found"}), 404

    db.session.delete(customer)
    try:
        db.session.commit()
        # Check for existing loans referencing this customer
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Cannot delete a customer that has existing loans"}), 409

    return '', 204
