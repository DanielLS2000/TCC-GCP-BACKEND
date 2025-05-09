import os
from dotenv import load_dotenv

# Set base directory of the app
basedir = os.path.abspath(os.path.dirname(__file__))

# Load the .env and .flaskenv variables
load_dotenv(os.path.join(basedir, ".env"))


SECRET_KEY = os.environ.get("SECRET_KEY", 'super-secret-key')

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/sales_db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", 'jwt-super-secret-key')
JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]