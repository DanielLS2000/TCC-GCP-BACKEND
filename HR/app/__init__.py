from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from app.database import reset_db

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configurações para teste
    if config_overrides:
        app.config.update(config_overrides)

    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

        # Create database tables

        if app.config.get("TESTING", False):
            try:
                reset_db(db)
            except Exception as e:
                print(f"Error creating database tables (during test setup): {e}")
        else:
            db.create_all()

    # Importar e registrar Blueprints
    from app.routes.employees_routes import hr_bp
    app.register_blueprint(hr_bp, url_prefix='/api/employees')

    return app