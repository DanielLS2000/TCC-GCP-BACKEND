from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from auth.routes import auth_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)  # Habilita CORS
    jwt = JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
