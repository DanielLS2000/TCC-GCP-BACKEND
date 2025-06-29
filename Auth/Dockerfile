FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the working directory
# This assumes the Dockerfile is located in the 'Auth' directory,
# so '.' refers to the 'Auth' directory content.
COPY . .

# Specify the Flask application entry point for Gunicorn
# 'auth:create_app' significa que Gunicorn deve importar o pacote 'auth'
# e chamar a função 'create_app()' dentro dele para obter a instância do Flask app.
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the port your Flask app runs on
EXPOSE 5000

# Command to run the Flask application using Gunicorn
# -w: número de workers (escolha um valor adequado, geralmente 2*CPU_CORES + 1)
# -b: endereço de bind (0.0.0.0:5000 para escutar em todas as interfaces)
# auth:create_app: indica que a aplicação Flask está na função 'create_app'
#                   dentro do pacote 'auth'.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]