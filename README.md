# 📧 Notificación Automática - Contrato Indefinido

Script automatizado que envía correos de felicitación a empleados que pasan a contrato indefinido.

## 📋 Descripción

Este script:
1. Consulta la base de datos de RRHH buscando empleados que cumplen 3 meses desde su ingreso
2. Filtra aquellos que pasan a contrato indefinido (sin fecha de término de contrato)
3. Envía un correo personalizado de felicitación con imagen embebida

## 🏗️ Estructura del Proyecto

```
proyecto_indefinido/
├── script/
│   └── script_paso_indefinido.py    # Script principal
├── img/
│   └── contrato_ind.png             # Imagen para el correo
├── logs/                            # Logs de ejecución (generado automáticamente)
├── Dockerfile                       # Definición del contenedor
├── docker-compose.yml               # Orquestación Docker
├── requirements.txt                 # Dependencias Python
├── .env.example                     # Template de variables de entorno
├── .gitignore                       # Archivos excluidos del repositorio
└── README.md                        # Este archivo
```

## ⚙️ Requisitos

- Python 3.11+
- Docker y Docker Compose
- Acceso a SQL Server (IARRHH)
- Servidor SMTP configurado

## 🚀 Instalación y Despliegue

### Opción 1: Con Docker (Recomendado - Marco de Gobernanza)

```bash
# 1. Clonar el repositorio
git clone <URL_REPOSITORIO_CORPORATIVO>
cd proyecto_indefinido

# 2. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con valores reales

# 3. Construir la imagen
docker-compose build

# 4. Ejecutar
docker-compose up
```

### Opción 2: Ejecución directa (Solo para desarrollo)

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux
# venv\Scripts\activate   # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables
cp .env.example .env
nano .env

# 4. Ejecutar
python script/script_paso_indefinido.py
```

## ⏰ Programación con Cron

Para ejecutar diariamente a las 8:00 AM:

```bash
# Editar crontab
crontab -e

# Agregar línea:
0 8 * * * cd /ruta/proyecto_indefinido && docker-compose up --build
```

## 📊 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SMTP_HOST` | Servidor SMTP | smtp.cramer.cl |
| `SMTP_PORT` | Puerto SMTP | 587 |
| `SMTP_EMAIL` | Correo remitente | rrhh@cramer.cl |
| `SMTP_PASSWORD` | Contraseña SMTP | ******** |
| `SQL_SERVER` | Servidor SQL | SERVIDOR_SQL |
| `SQL_DATABASE` | Base de datos | IARRHH |

## 📝 Logs

Los logs se guardan en `logs/correo_indefinido.log` con el formato:
```
2025-02-04 08:00:00 - INFO - Consulta SQL ejecutada. Registros encontrados: 3
2025-02-04 08:00:01 - INFO - Email con imagen embebida enviado a: usuario@email.com
```

## 🔒 Seguridad (Marco de Gobernanza)

Este proyecto cumple con el **Marco de Gobernanza para Células de Desarrollo**:

- ✅ Variables de entorno para credenciales (no hardcodeadas)
- ✅ Stack tecnológico estándar (Python, SQL Server, Docker)
- ✅ Código en repositorio corporativo
- ✅ Dependencias declaradas en requirements.txt
- ✅ Dockerizado para despliegue consistente

## 👥 Responsables

- **Célula de Desarrollo:** Gerencia de Personas
- **QA/DevOps:** Departamento de Informática
- **Soporte Nivel 1-2:** Gerencia de Personas
- **Soporte Nivel 3:** Informática

## 📄 Licencia

Uso interno - Cramer Chile

---
*Documento generado según Marco de Gobernanza para Células de Desarrollo v1.0*
