from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from inventory.database import reset_db, init_db

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
        
        # Config do CORS
        allowed_origins = [
            "http://34.95.123.94", # IP do Ingress
            "http://localhost:4200" # Rodando local
        ]

        cors.init_app(
            app,
            resources={r"/api/*": {"origins": allowed_origins}},
            supports_credentials=True
        )
        
        # Create database tables

        if app.config.get("TESTING", False):
            try:
                reset_db(db)
            except Exception as e:
                print(f"Error creating database tables (during test setup): {e}")
        else:
            print("Attempting to create database tables if they don't exist...")
            try:
                init_db(db=db)
                print("Database tables created successfully or already exist.")
            except Exception as e:
                print(f"ERROR: Failed to create database tables: {e}")

    # Importar e registrar Blueprints
    from inventory.routes.product_routes import product_bp
    from inventory.routes.category_routes import category_bp
    from inventory.routes.stock_routes import stock_bp
    from inventory.routes.inventory_routes import inventory_bp

    app.register_blueprint(product_bp, url_prefix='/api/inventory/products')
    app.register_blueprint(category_bp, url_prefix='/api/inventory/categories')
    app.register_blueprint(stock_bp, url_prefix='/api/inventory/stock')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory/locations')

    from inventory.routes.health_routes import health_bp
    app.register_blueprint(health_bp)

    return app