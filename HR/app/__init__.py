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
        cors.init_app(app)

    # Importar e registrar Blueprints
    from app.routes.employees_routes import hr_bp
    app.register_blueprint(hr_bp, url_prefix='/api/hr')

    return app