import os
import tempfile

import pytest

from app import create_app
from app.db import db
from app.models import Book, Category, Customer


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
    })

    with flask_app.app_context():
        db.create_all()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        # Windows keeps the sqlite file locked until pooled connections are
        # closed, so the engine must be disposed before unlinking below.
        db.engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def category(app):
    # Keep the app context alive for the whole test, not just the insert,
    # so the returned instance isn't detached (SQLAlchemy expires
    # attributes on commit and needs a live session to re-fetch them).
    with app.app_context():
        category = Category(name="Fiction", description="Fiction books")
        db.session.add(category)
        db.session.commit()
        yield category


@pytest.fixture()
def book(app, category):
    with app.app_context():
        book = Book(
            title="Dune",
            author="Frank Herbert",
            isbn="9780441013593",
            category_id=category.id,
            total_copies=3,
            available_copies=3,
            published_year=1965,
        )
        db.session.add(book)
        db.session.commit()
        yield book


@pytest.fixture()
def customer(app):
    with app.app_context():
        customer = Customer(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="555-1234",
        )
        db.session.add(customer)
        db.session.commit()
        yield customer
