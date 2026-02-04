# Dockerfile - Script Notificación Contrato Indefinido
# Marco de Gobernanza - Células de Desarrollo Cramer

FROM python:3.11-slim

# Metadata
LABEL maintainer="Gerencia de Personas"
LABEL description="Script de notificación automática para contratos indefinidos"
LABEL version="1.0"

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema para pyodbc (SQL Server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY script/ ./script/
COPY img/ ./img/

# Crear directorio para logs
RUN mkdir -p /app/logs

# Usuario no-root por seguridad
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Comando por defecto
CMD ["python", "script/script_paso_indefinido.py"]
