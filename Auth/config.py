import os

class Config:
    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-super-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 minutos
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 dias
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/auth_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
