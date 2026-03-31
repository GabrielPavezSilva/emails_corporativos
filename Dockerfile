# Dockerfile - Script Notificación Contrato Indefinido
FROM python:3.11-slim-bookworm

LABEL maintainer="Gerencia de Personas"
LABEL description="Script de notificación automática para contratos indefinidos"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario primero
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY script/ ./script/
COPY img/ ./img/
COPY pdf/ ./pdf/
COPY templates/ ./templates/

# Crear carpeta logs y dar permisos al usuario
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

CMD ["python", "script/script_paso_indefinido.py"]
