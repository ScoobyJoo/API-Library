from datetime import datetime
from flask import Blueprint, jsonify, request, session
from app.db import db
from app.models import Book, Customer, Loan

loans_bp = Blueprint("loans", __name__, url_prefix='/api/loans')

# Create a loan
@loans_bp.route("", methods=["POST"])
def checkout_book():
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")

    # A logged-in customer can only ever check out books for themselves —
    # the session's customer_id wins over whatever the client sent. With no
    # session (the staff/admin flow, which has no login of its own yet),
    # fall back to the client-supplied customer_id so staff can still check
    # a book out on behalf of any customer.
    session_customer_id = session.get('customer_id')
    customer_id = session_customer_id if session_customer_id is not None else data.get("customer_id")

    if book_id is None or customer_id is None:
        return jsonify({"error": "book_id and customer_id are required"}), 400

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": f"book {book_id} not found"}), 404

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": f"customer {customer_id} not found"}), 404

    # Business rule 1: no checkout without an available copy.
    if book.available_copies < 1:
        return jsonify({"error": f"No available copies for book {book_id}"}), 409

    loan = Loan(
        book_id=book_id,
        customer_id=customer_id,
        status="active",
    )
    # Business rule 2: checkout decrements available_copies.
    book.available_copies -= 1

    db.session.add(loan)
    db.session.commit()
    return jsonify(loan.to_dict()), 201

# Return a loan
@loans_bp.route("/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "loan not found"}), 404

    # A logged-in customer can only return their own loans. No session (the
    # staff/admin flow) can still return any loan, same as before.
    session_customer_id = session.get('customer_id')
    if session_customer_id is not None and loan.customer_id != session_customer_id:
        return jsonify({"error": "You can only return your own loans"}), 403

    # Business rule 4: an already-returned loan can't be returned again.
    if loan.status == "returned":
        return jsonify({"error": f"loan {loan_id} has already been returned"}), 409

    # Business rule 3: returning sets return_date and increments availability.
    loan.return_date = datetime.utcnow()
    loan.status = "returned"

    book = Book.query.get(loan.book_id)
    if book and book.available_copies < book.total_copies:
        book.available_copies += 1

    db.session.commit()
    return jsonify(loan.to_dict())

# List loans with optional filters
@loans_bp.route("", methods=["GET"])
def list_loans():
    query = Loan.query

    customer_id = request.args.get("customer_id", type=int)
    if customer_id is not None:
        # A logged-in customer can only list their own loans. No session
        # (the staff/admin flow) can still filter by any customer_id.
        session_customer_id = session.get('customer_id')
        if session_customer_id is not None and customer_id != session_customer_id:
            return jsonify({"error": "You can only view your own loans"}), 403
        query = query.filter(Loan.customer_id == customer_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Loan.status == status)

    return jsonify([l.to_dict() for l in query.all()])

# Get a specific loan
@loans_bp.route("/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "loan not found"}), 404
    return jsonify(loan.to_dict())
