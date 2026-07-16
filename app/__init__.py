import os
from flask import Flask
from app.db import db

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///library.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from app import models 
    
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy"}

    return app
