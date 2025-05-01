import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-super-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 minutos
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 dias