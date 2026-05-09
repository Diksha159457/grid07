FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-deploy.txt && \
    pip install --no-cache-dir .

EXPOSE 8080

CMD ["python3", "-m", "grid07.cli", "serve", "--host", "0.0.0.0"]
