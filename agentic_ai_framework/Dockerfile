FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure web-ui directory exists and has correct permissions
RUN mkdir -p data logs tools web-ui && \
    chmod -R 755 web-ui

# Verify web-ui files are present
RUN ls -la web-ui/ || echo "Warning: web-ui directory is empty"

EXPOSE 8000

CMD ["python", "main.py"]
