# Dockerfile
FROM python:3.12.5-slim-bullseye

RUN apt-get update && apt-get install -y ca-certificates curl openssl dnsutils
RUN update-ca-certificates

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5001

# Ensure SSL certificates are correctly installed
RUN python -c "import certifi; print(certifi.where())"


ENV PYTHONHTTPSVERIFY=0
CMD ["python", "app/app.py"]