from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    with app.app_context():
        # Resetar o banco de dados
        from app.database import reset_db
        db.init_app(app)
        reset_db(db)

        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Importar e registrar Blueprints
    from app.routes.product_routes import product_bp
    from app.routes.category_routes import category_bp
    from app.routes.stock_routes import stock_bp
    from app.routes.inventory_routes import inventory_bp

    app.register_blueprint(product_bp, url_prefix='/api/inventory/products')
    app.register_blueprint(category_bp, url_prefix='/api/inventory/categories')
    app.register_blueprint(stock_bp, url_prefix='/api/inventory/stock')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory/locations')

    return app