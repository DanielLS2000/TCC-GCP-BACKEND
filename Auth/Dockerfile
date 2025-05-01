# Usa uma imagem oficial do Python como base
FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do projeto para dentro do container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Flask vai usar
EXPOSE 5000

# Define a variável de ambiente para dizer ao Flask que estamos no modo de desenvolvimento
ENV FLASK_APP=auth_service.py
ENV FLASK_RUN_HOST=0.0.0.0

# Comando para iniciar o Flask
CMD ["python", "./app.py"]