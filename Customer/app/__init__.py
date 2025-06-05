from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import BadRequest

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    # Configurações para teste
    if config_overrides:
        app.config.update(config_overrides)

    with app.app_context():
        # Resetar o banco de dados
        from app.database import reset_db
        db.init_app(app)
        reset_db(db)

        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Importar e registrar Blueprints
    from app.routes.customer_routes import customer_bp
    app.register_blueprint(customer_bp, url_prefix='/api/customers')

    return app