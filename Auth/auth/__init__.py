from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config
from auth.utils import reset_db, init_db
from werkzeug.exceptions import BadRequest
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
oauth = OAuth()

def create_app(config_overrides=None):
    print("Inicializando Aplicação...")
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
        oauth.init_app(app)

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

        # Register OAuth Client
        oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url=app.config.get('GOOGLE_DISCOVERY_URL'),
            client_kwargs={'scope': 'openid email profile'},
            redirect_uri=app.config.get('GOOGLE_REDIRECT_URI')
        )

        # Create database tables

        if app.config.get("TESTING", False):
            try:
                reset_db(db)
            except Exception as e:
                print(f"Error creating database tables (during test setup): {e}")
        else:
            print("Attempting to create database tables if they don't exist...") # NOVO LOG
            try:
                init_db(db=db)
                print("Database tables created successfully or already exist.") # NOVO LOG
            except Exception as e:
                print(f"ERROR: Failed to create database tables: {e}") # NOVO LOG DE ERRO
                # Opcional: Você pode querer relançar o erro ou fazer algo mais robusto em produção
                # raise # Descomente para que o pod falhe se a criação da tabela falhar

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    from auth.health import health_bp
    app.register_blueprint(health_bp)

    return app