import logging
import os
from flask import Flask, redirect, render_template, url_for
from app.db import db

def create_app(test_config=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///library.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        from app import models

    from app.routes.categories import categories_bp
    app.register_blueprint(categories_bp)

    from app.routes.books import books_bp
    app.register_blueprint(books_bp)

    from app.routes.customers import customers_bp
    app.register_blueprint(customers_bp)

    from app.routes.loans import loans_bp
    app.register_blueprint(loans_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy"}

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/admin", methods=["GET"])
    def admin_root():
        return redirect(url_for('admin_books'))

    @app.route("/admin/books", methods=["GET"])
    def admin_books():
        return render_template("admin/books.html", active_page="books")

    @app.route("/admin/customers", methods=["GET"])
    def admin_customers():
        return render_template("admin/customers.html", active_page="customers")

    @app.route("/admin/categories", methods=["GET"])
    def admin_categories():
        return render_template("admin/categories.html", active_page="categories")

    @app.route("/admin/loans", methods=["GET"])
    def admin_loans():
        return render_template("admin/loans.html", active_page="loans")

    return app
