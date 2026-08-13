import logging
import os
import secrets
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

    # Signs the session cookie; must be a real secret (env var) in any shared/production environment.
    if not app.config.get('SECRET_KEY'):
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            if app.debug:
                secret_key = secrets.token_hex(32)
                app.logger.warning(
                    "SECRET_KEY is not set; generated a random ephemeral key for this "
                    "process. Sessions will not persist across restarts. Set the "
                    "SECRET_KEY environment variable to fix this."
                )
            else:
                raise RuntimeError(
                    "SECRET_KEY environment variable must be set when not running in debug mode."
                )
        app.config['SECRET_KEY'] = secret_key

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

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy"}

    @app.route("/", methods=["GET"])
    def index():
        return render_template("user.html")

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
