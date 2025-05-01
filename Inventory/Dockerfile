# Usar uma imagem base com Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos necessários para o container
COPY . /app/src
COPY requirements.txt /app/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expor a porta da aplicação Flask (padrão 5000)
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "/app/src/app.py"]
