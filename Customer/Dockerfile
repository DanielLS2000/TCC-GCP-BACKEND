FROM python:3.10-slim

WORKDIR /workdir

COPY . /workdir/src
COPY requirements.txt /workdir/requirements.txt
RUN pip install --no-cache-dir -r /workdir/requirements.txt

EXPOSE 5000

CMD ["python", "/workdir/src/app.py"]