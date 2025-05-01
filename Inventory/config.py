import os

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/inventory_db")
SQLALCHEMY_TRACK_MODIFICATIONS = False