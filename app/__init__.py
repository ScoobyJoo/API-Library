import os
from flask import Flask
from app.db import db

def create_app(test_config=None):
    app = Flask(__name__)

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

    return app
