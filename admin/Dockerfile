FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user
RUN useradd --create-home --shell /bin/bash admin
RUN mkdir -p /app/audio /app/data && chown -R admin:admin /app
USER admin

EXPOSE 8080

CMD ["python", "app.py"]
