from datetime import datetime
from flask import Blueprint, jsonify, request
from app.db import db
from app.models import Book, Customer, Loan

loans_bp = Blueprint("loans", __name__)

@loans_bp.post("/loans")
def checkout_book():
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")
    customer_id = data.get("customer_id")

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


@loans_bp.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "loan not found"}), 404

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


@loans_bp.get("/loans")
def list_loans():
    query = Loan.query

    customer_id = request.args.get("customer_id", type=int)
    if customer_id is not None:
        query = query.filter(Loan.customer_id == customer_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Loan.status == status)

    return jsonify([l.to_dict() for l in query.all()])


@loans_bp.get("/loans/<int:loan_id>")
def get_loan(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "loan not found"}), 404
    return jsonify(loan.to_dict())
