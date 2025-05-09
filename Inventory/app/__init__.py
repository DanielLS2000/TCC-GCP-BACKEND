from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.database import Base, reset_db
import os

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    with app.app_context():
        db.init_app(app)
        reset_db(db)

        jwt.init_app(app)
        cors.init_app(app)

    # Importar e registrar Blueprints
    from routes.product_routes import product_bp
    from routes.category_routes import category_bp
    from routes.stock_routes import stock_bp
    from routes.inventory_routes import inventory_bp

    app.register_blueprint(product_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(inventory_bp)

    return app