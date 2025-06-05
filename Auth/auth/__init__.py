from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config
from auth.utils import reset_db, init_db
from werkzeug.exceptions import BadRequest

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configurações para teste
    if config_overrides:
        app.config.update(config_overrides)

    # Manipulador de erro para BadRequest (como JSON malformado)
    @app.errorhandler(BadRequest)
    def handle_json_bad_request(e):
        message = "Bad Request"
        # A descrição do erro do Werkzeug é útil aqui
        if hasattr(e, 'description') and e.description:
            message = e.description
        return jsonify(msg=message), 400


    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        jwt.init_app(app)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

        # Create database tables

        try:
            reset_db(db)
        except Exception as e:
            print(f"Error creating database tables: {e}")
            reset_db(db)

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app