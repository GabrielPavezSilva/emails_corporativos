""""
Envia un correo desde gerencia de personas al pasar a indefinido.  
"""
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
import logging
from pathlib import Path
from email.message import EmailMessage
import smtplib
import ssl

load_dotenv(override=True)

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent 
PROJECT_ROOT = SCRIPT_DIR.parent
LOG_FOLDER = PROJECT_ROOT / "logs"
IMG_FOLDER = PROJECT_ROOT / "img"
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
log_filename = LOG_FOLDER / f"correo_indefinido.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # muestra en consola
    ]
)

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_EMAIL")
SMTP_PASS = os.getenv("SMTP_PASSWORD")

#hoy = date.today()
hoy = datetime.strptime('2026-02-03', '%Y-%m-%d').date()
ingreso = hoy - relativedelta(months=3)

try:
    engine = create_engine(
    f"mssql+pyodbc://{os.getenv('SQL_USER')}:{os.getenv('SQL_PASSWORD')}@{os.getenv('SQL_SERVER')}/{os.getenv('SQL_DATABASE')}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )

    query_sql = f"""
    SELECT 
        [full_name]
        ,[first_name]
        ,[personal_email]
        ,[status]
        ,[active_since]
        ,[start_date]
    FROM [IARRHH].[dbo].[employees]
    WHERE 
        CONVERT(date, [start_date]) = '{hoy}'
        AND CONVERT (date, [active_since]) = '{ingreso}'
        AND [status] = 'activo'
        AND [payment_method] = 'Transferencia Bancaria'
        AND [contract_finishing_date_1] IS Null
        AND [contract_finishing_date_2] IS Null
    """

    df_alertas = pd.read_sql_query(query_sql, engine)
    logger.info(f"Consulta SQL ejecutada. Registros encontrados: {len(df_alertas)}")
    logger.info(f"Datos:\n{df_alertas.to_string()}") 

    if len(df_alertas) > 0:
        logger.info(f"Empleados a notificar:\n{df_alertas['full_name'].to_string()}")
    else:
        logger.info("No se encontraron empleados para notificar hoy")
except Exception as e:
    logger.error(f"Error al ejecutar consulta SQL: {e}", exc_info=True)
    raise

def send_embedded_email_smtp(to_email, subject, html_body, image_path, image_cid):
    """
    Envía un correo SMTP con una imagen EMBEBIDA en el cuerpo HTML.
    La imagen se referencia en el HTML como: <img src="cid:image_cid">
    """
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        logger.error("Faltan variables de entorno SMTP (HOST, PORT, EMAIL, PASSWORD)")
        return False

    try:
        # Crear mensaje
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        # Cuerpo en texto simple (fallback)
        msg.set_content("Este es un correo automático. Activa la vista HTML para verlo correctamente.")

        # Cuerpo HTML
        msg.add_alternative(html_body, subtype="html")

        # Verificar que existe la imagen
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"No se encontró la imagen en {image_path}")
            return False

        # Leer y embeber la imagen
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            
            # Obtenemos la extensión (ej: '.jpg') y la limpiamos (ej: 'jpg')
            subtype = image_path.suffix.lstrip('.').lower()
            if subtype == 'jpg':
                subtype = 'jpeg' # 'jpg' debe ser 'jpeg' para MIME

            # Adjuntar imagen como inline (embebida)

            msg.get_payload()[1].add_related(
                img_data,
                maintype="image",
                subtype=subtype,
                cid=image_cid 
            )

        logger.info(f"Imagen embebida: {image_path.name} con CID: {image_cid}")

        # Enviar correo
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info(f"Email con imagen embebida enviado a: {to_email}")
        return True

    except smtplib.SMTPException as e:
        logger.error(f"Error de SMTP: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error general enviando correo: {e}", exc_info=True)
        return False

ruta_imagen_felicitacion = IMG_FOLDER / "contrato_ind.png" 
id_imagen = "img_indefinido"

emails_enviados = 0
emails_fallidos = 0
for _, fila in df_alertas.iterrows():
    nombre = fila["first_name"]
    #correo = fila["personal_email"]
    correo = "gpavez@cramer.cl" #pruebas
    asunto = f"¡Felicitaciones por tu contrato indefinido, {nombre}!"
    
    cuerpo_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Calibri, sans-serif; }}
                p {{ font-size: 16px; }}
            </style>
        </head>
        <body>
            <p>Hola {nombre},</p>
            <p>Junto con saludarte, te escribimos desde RRHH para felicitarte por tu paso a <strong>contrato indefinido.</strong></p>
            <p>Estamos muy contentos de que continúes formando parte de nuestro equipo.</p>
            
            <div style="padding: 15px;">
                <a href="https://cramer.buk.cl/benefits" target="_blank" style="text-decoration: none;">
                    <img src="cid:{id_imagen}" alt="¡FELICITACIONES!" style="display: block; border: none; border-radius: 4px;">
                </a>
            </div>

            <p>Saludos!!</p>
        </body>
        </html>
        """

    exito = send_embedded_email_smtp(correo, asunto, cuerpo_html, ruta_imagen_felicitacion, id_imagen)
    
    if exito:
        emails_enviados += 1
    else:
        emails_fallidos += 1

logger.info("="*60)
logger.info("RESUMEN DE EJECUCIÓN")
logger.info(f"Total empleados procesados: {len(df_alertas)}")
logger.info(f"Emails enviados exitosamente: {emails_enviados}")
logger.info(f"Emails fallidos: {emails_fallidos}")
logger.info("="*60)
