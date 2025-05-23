from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from auth.routes import auth_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Habilita CORS
    jwt = JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app