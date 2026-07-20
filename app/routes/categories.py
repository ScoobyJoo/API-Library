from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from app.models import Category
from app.db import db

# Creates a Blueprint for category-related routes with a URL prefix of '/api/categories'
categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

# List all categories
@categories_bp.route('', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories]), 200

# Create a new category
@categories_bp.route('', methods=['POST'])
def create_category():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    # Validate that 'name' is provided
    if not name:
        return jsonify({"error": "'name' is required"}), 400

    category = Category(name=name, description=data.get('description'))
    db.session.add(category)
    try:
        db.session.commit()
        # Check for duplicate
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A category with that name already exists"}), 409

    return jsonify(category.to_dict()), 201

# Get a specific category by ID
@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category = db.session.get(Category, category_id)
    # Validate that the category exists
    if category is None:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(category.to_dict()), 200

# Update an existing category
@categories_bp.route('/<int:category_id>', methods=['PUT', 'PATCH'])
def update_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        if not data['name']:
            return jsonify({"error": "'name' cannot be empty"}), 400
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']

    try:
        db.session.commit()
    # Check for duplicate
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A category with that name already exists"}), 409

    return jsonify(category.to_dict()), 200

# Delete a category
@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    db.session.delete(category)
    db.session.commit()
    return '', 204
