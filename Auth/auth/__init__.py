from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config
from auth.utils import reset_db, init_db

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

        # Create database tables

        try:
            reset_db(db)
        except Exception as e:
            print(f"Error creating database tables: {e}")
            reset_db(db)

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app