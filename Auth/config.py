import os
from google.cloud import secretmanager

def get_secret(secret_name):
    project_id = os.environ.get('GCP_PROJECT_ID') # Será definida no Deployment YAML
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

class Config:
    # Obter secrets do Secret Manager
    # Isso requer que a conta de serviço do Kubernetes tenha permissão para acessar esses secrets
    SECRET_KEY = get_secret('tcc-app-secret') if os.environ.get('KUBERNETES_DEPLOYMENT') else os.environ.get('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = get_secret('tcc-jwt-secret') if os.environ.get('KUBERNETES_DEPLOYMENT') else os.environ.get('JWT_SECRET_KEY', 'jwt-super-secret-key')
    
    # A URL do DB pode ser construída ou também vir do Secret Manager
    SQLALCHEMY_DATABASE_URI = get_secret('AUTH_DB_URL') if os.environ.get('KUBERNETES_DEPLOYMENT') else os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/auth_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = 900
    JWT_REFRESH_TOKEN_EXPIRES = 2592000
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]