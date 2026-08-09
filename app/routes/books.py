from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError
from app.models import Book, Category, Loan
from app.db import db

books_bp = Blueprint('books', __name__, url_prefix='/api/books')

# List all books
@books_bp.route('', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([b.to_dict() for b in books]), 200

# Create a new book
@books_bp.route('', methods=['POST'])
def create_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    category_id = data.get('category_id')

    # Validate required fields
    if not title or not author or not isbn or category_id is None:
        return jsonify({"error": "'title', 'author', 'isbn' and 'category_id' are required"}), 400

    if db.session.get(Category, category_id) is None:
        return jsonify({"error": "Category not found"}), 404

    total_copies = data.get('total_copies', 0)
    available_copies = data.get('available_copies', total_copies)

    if not isinstance(total_copies, int) or not isinstance(available_copies, int):
        return jsonify({"error": "'total_copies' and 'available_copies' must be integers"}), 400
    if total_copies < 0 or available_copies < 0:
        return jsonify({"error": "'total_copies' and 'available_copies' cannot be negative"}), 400
    if available_copies > total_copies:
        return jsonify({"error": "'available_copies' cannot exceed 'total_copies'"}), 400

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        category_id=category_id,
        total_copies=total_copies,
        available_copies=available_copies,
        published_year=data.get('published_year'),
    )
    db.session.add(book)
    try:
        db.session.commit()
        # Check for duplicate isbn
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A book with that ISBN already exists"}), 409

    return jsonify(book.to_dict()), 201

# Get a specific book by ID
@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = db.session.get(Book, book_id)
    # Validate that the book exists
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book.to_dict()), 200

# Update an existing book
@books_bp.route('/<int:book_id>', methods=['PUT', 'PATCH'])
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json(silent=True) or {}

    if 'category_id' in data:
        if db.session.get(Category, data['category_id']) is None:
            return jsonify({"error": "Category not found"}), 404
        book.category_id = data['category_id']

    if 'title' in data:
        if not data['title']:
            return jsonify({"error": "'title' cannot be empty"}), 400
        book.title = data['title']
    if 'author' in data:
        if not data['author']:
            return jsonify({"error": "'author' cannot be empty"}), 400
        book.author = data['author']
    if 'isbn' in data:
        if not data['isbn']:
            return jsonify({"error": "'isbn' cannot be empty"}), 400
        book.isbn = data['isbn']
    if 'published_year' in data:
        book.published_year = data['published_year']

    total_copies = data.get('total_copies', book.total_copies)
    available_copies = data.get('available_copies', book.available_copies)

    if not isinstance(total_copies, int) or not isinstance(available_copies, int):
        return jsonify({"error": "'total_copies' and 'available_copies' must be integers"}), 400
    if total_copies < 0 or available_copies < 0:
        return jsonify({"error": "'total_copies' and 'available_copies' cannot be negative"}), 400
    if available_copies > total_copies:
        return jsonify({"error": "'available_copies' cannot exceed 'total_copies'"}), 400

    book.total_copies = total_copies
    book.available_copies = available_copies

    try:
        db.session.commit()
    # Check for duplicate isbn
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A book with that ISBN already exists"}), 409

    return jsonify(book.to_dict()), 200

# Delete a book
@books_bp.route('/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    has_active_loan = db.session.query(Loan.id).filter(
        Loan.book_id == book_id,
        Loan.status != 'returned',
    ).first() is not None
    current_app.logger.debug("book %s has_active_loan=%s", book_id, has_active_loan)
    if has_active_loan:
        return jsonify({"error": "Cannot delete a book that has active loans"}), 409

    Loan.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()

    return '', 204
