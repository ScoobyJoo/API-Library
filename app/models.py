from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    books = db.relationship('Book', backref='category', lazy=True)

    # Method to convert the model instance to a dictionary for easy serialization
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    total_copies = db.Column(db.Integer, nullable=False, default=0)
    available_copies = db.Column(db.Integer, nullable=False, default=0)
    published_year = db.Column(db.Integer, nullable=True)

    loans = db.relationship('Loan', backref='book', lazy=True)

    # Checking the constaints
    __table_args__ = (
        db.CheckConstraint('total_copies >= 0', name='check_total_copies_non_negative'),
        db.CheckConstraint('available_copies >= 0', name='check_available_copies_non_negative'),
        # Available_copies may never exceed total_copies or drop below 0.
        db.CheckConstraint('available_copies <= total_copies', name='check_available_copies_not_exceed_total')
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "category_id": self.category_id,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "published_year": self.published_year,
        }

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    membership_date = db.Column(db.Date, nullable=False, default=date.today)

    loans = db.relationship('Loan', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "membership_date": self.membership_date.isoformat(),
        }

class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    checkout_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False, default=lambda: date.today() + timedelta(days=14))
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False) # active, returned, overdue (lowercase)

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "customer_id": self.customer_id,
            "checkout_date": self.checkout_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "status": self.status,
        }