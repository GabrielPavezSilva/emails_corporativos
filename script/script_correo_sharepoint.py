""""
Envía un correo el dia de ingreso los colaboradores con el link a sharepoint.  

NO DESPLEGAR DE MOMENTO!!!!!!!!

"""

import os
import pandas as pd
from dotenv import load_dotenv
from datetime import date, datetime
from sqlalchemy import create_engine
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
import logging
import sys

script_path = Path(__file__).resolve()

PROJECT_ROOT = script_path.parent.parent 

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from templates.email_templates import get_email_template


load_dotenv(override=True)


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent 
IMG_FOLDER = PROJECT_ROOT / "img"
RUTA_IMAGEN_BIENVENIDA = IMG_FOLDER / "imagen_bienvenida.gif"
ID_IMAGEN_BIENVENIDA = "welcome_cramer_img" 
PROJECT_ROOT = SCRIPT_DIR.parent
LOG_FOLDER = PROJECT_ROOT / "logs"
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
log_filename = LOG_FOLDER / f"email_guia.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_EMAIL")
SMTP_PASS = os.getenv("SMTP_PASSWORD")

#hoy = date.today()
hoy = datetime.strptime('2023-08-07', "%Y-%m-%d")
logger.info(f"Iniciando proceso. Fecha: {hoy}")

try:
    engine = create_engine(
        f"mssql+pyodbc://{os.getenv('SQL_SERVER')}/{os.getenv('SQL_DATABASE')}?trusted_connection=yes&driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    
    query_sql = f"""
    SELECT 
        e.[full_name],
        e.[first_name],
        e.[email],
        a.first_level_name AS empresa
    FROM [IARRHH].[dbo].[employees] AS e
    INNER JOIN [IARRHH].[dbo].[areas] AS a
        ON e.[area_id] = a.[id] 
            AND e.[cost_center] = a.[cost_center]
    WHERE 
        CONVERT(date, e.[active_since]) = '{hoy}'
        AND e.[status] = 'activo'
        AND e.[payment_method] = 'Transferencia Bancaria';
    """
    
    df_alertas = pd.read_sql_query(query_sql, engine)
    logger.info(f"Consulta SQL ejecutada. Registros encontrados: {len(df_alertas)}")
    
    if len(df_alertas) > 0:
        logger.info(f"Empleados nuevos:\n{df_alertas[['full_name', 'empresa']].to_string()}")
    else:
        logger.info("No se encontraron empleados nuevos para hoy")

except Exception as e:
    logger.error(f"Error al ejecutar consulta SQL: {e}", exc_info=True)
    raise


def send_email_smtp_advanced(to_email, subject, html_body, image_path=None, image_cid=None):
    """
    Envía un correo SMTP con archivos PDF adjuntos y una imagen EMBEBIDA (si se proporciona).
    """
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        logger.error("Faltan variables de entorno SMTP (HOST, PORT, EMAIL, PASSWORD)")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        # Cuerpo en texto simple (fallback)
        msg.set_content("Este es un correo automático. Activa la vista HTML para verlo correctamente.")

        # Cuerpo HTML
        msg.add_alternative(html_body, subtype="html")
        
        # LÓGICA DE EMBEBIDO DE IMAGEN (Similar a tu script que funciona)
        if image_path and image_cid:
            img_path = Path(image_path)
            if not img_path.exists():
                logger.warning(f"No se encontró la imagen para embeber en {img_path}. Se enviará sin imagen.")
            else:
                with open(img_path, "rb") as img_file:
                    img_data = img_file.read()
                    subtype = img_path.suffix.lstrip('.').lower()
                    if subtype == 'jpg': subtype = 'jpeg'

                    # El cuerpo HTML (alternativa 1) es el segundo payload (índice 1)
                    msg.get_payload()[1].add_related( 
                        img_data,
                        maintype="image",
                        subtype=subtype,
                        cid=image_cid 
                    )
                logger.info(f"Imagen embebida: {img_path.name} con CID: {image_cid}")

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info(f"Email enviado exitosamente a {to_email}")
        return True

    except smtplib.SMTPException as e:
        logger.error(f"Error de SMTP: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error general enviando correo: {e}", exc_info=True)
        return False
    
emails_enviados = 0
emails_fallidos = 0

# Iterar sobre el DataFrame
for idx, fila in df_alertas.iterrows():
    nombre = fila["first_name"]
    #correo = fila["email"]
    correo = 'gpavez@cramer.cl'
    empresa = fila["empresa"]
    
    if "CARLOS CRAMER PRODUCTOS AROMÁTICOS S.A. C.I." in empresa.upper():
        empresa_key = 'cramer'
    elif 'Sabores Y Fragancias.Cl Comercial Ltda.'in empresa.upper():
        empresa_key = 'syf'
    else:
        empresa_key = 'cramer'

    # PASAMOS EL CID COMO VALOR DE IMAGEN (Ej: "cid:welcome_cramer_img")
    cuerpo_html = get_email_template(empresa_key, nombre, f"cid:{ID_IMAGEN_BIENVENIDA}")
    
    asunto = f"¡TE DAMOS LA BIENVENIDA, {nombre}!"

    # LLAMADA A LA FUNCIÓN CON LOS PARÁMETROS DE EMBEBIDO
    exito = send_email_smtp_advanced(
        to_email=correo, 
        subject=asunto, 
        html_body=cuerpo_html,
        image_path=RUTA_IMAGEN_BIENVENIDA, # Ruta de archivo local para leerlo
        image_cid=ID_IMAGEN_BIENVENIDA    # El ID usado en el HTML
    )
    
    if exito:
        emails_enviados += 1
    else:
        emails_fallidos += 1

# Resumen final
logger.info("="*60)
logger.info("RESUMEN DE EJECUCIÓN")
logger.info(f"Total empleados procesados: {len(df_alertas)}")
logger.info(f"Emails enviados exitosamente: {emails_enviados}")
logger.info(f"Emails fallidos: {emails_fallidos}")
logger.info("="*60)
