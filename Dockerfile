# Dockerfile - Script Notificación Contrato Indefinido
FROM python:3.11-slim-bookworm

LABEL maintainer="Gerencia de Personas"
LABEL description="Script de notificación automática para contratos indefinidos"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema para pyodbc (SQL Server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario primero
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY script/ ./script/
COPY img/ ./img/

# Crear carpeta logs y dar permisos al usuario
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

CMD ["python", "script/script_paso_indefinido.py"]
