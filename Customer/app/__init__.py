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

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    with app.app_context():
        # Resetar o banco de dados
        from app.database import reset_db
        db.init_app(app)
        reset_db(db)

        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Importar e registrar Blueprints
    from app.routes.customer_routes import customer_bp
    app.register_blueprint(customer_bp, url_prefix='/api/customers')

    return app