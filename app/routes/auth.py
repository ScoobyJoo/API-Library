from flask import Blueprint, jsonify, request, session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.db import db
from app.models import Customer

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

MIN_PASSWORD_LENGTH = 8

# Register a new customer account. Fully separate from the staff-facing
# POST /api/customers used by the admin panel - if a customer record with
# this email already exists (created by staff), this fails with 409 rather
# than attaching a password to that record.
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not first_name or not last_name or not email or not password:
        return jsonify({"error": "'first_name', 'last_name', 'email' and 'password' are required"}), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"'password' must be at least {MIN_PASSWORD_LENGTH} characters"}), 400

    customer = Customer(first_name=first_name, last_name=last_name, email=email)
    customer.set_password(password)
    db.session.add(customer)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An account with that email already exists"}), 409

    session['customer_id'] = customer.id
    return jsonify(customer.to_dict()), 201

# Log in with email + password
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({"error": "'email' and 'password' are required"}), 400

    customer = Customer.query.filter(func.lower(Customer.email) == email.lower()).first()

    if customer is None or not customer.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    session['customer_id'] = customer.id
    return jsonify(customer.to_dict()), 200

# Clear the session when the user logs out
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('customer_id', None)
    return '', 204

# Return the logged-in customer's own record
@auth_bp.route('/me', methods=['GET'])
def me():
    customer_id = session.get('customer_id')
    if customer_id is None:
        return jsonify({"error": "Not logged in"}), 401

    customer = db.session.get(Customer, customer_id)
    if customer is None:
        session.pop('customer_id', None)
        return jsonify({"error": "Not logged in"}), 401

    return jsonify(customer.to_dict()), 200
