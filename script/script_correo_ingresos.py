""""
Envía un correo el dia de ingreso los colaboradores con el reglamento interno de Cramer o Syf desde Gerencia de Personas.  
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

load_dotenv(override=True)

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent 
PROJECT_ROOT = SCRIPT_DIR.parent
LOG_FOLDER = PROJECT_ROOT / "logs"
PDF_FOLDER = PROJECT_ROOT / "pdf"
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
log_filename = LOG_FOLDER / f"email_reglamento.log"

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
hoy = datetime.strptime('2023-08-07', '%Y-%m-%d').date()

logger.info(f"Iniciando proceso. Fecha: {hoy}")

try:
    engine = create_engine(
        f"mssql+pyodbc://{os.getenv('SQL_SERVER')}/{os.getenv('SQL_DATABASE')}?trusted_connection=yes&driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    
    query_sql = f"""
    SELECT 
        e.[full_name],
        e.[first_name],
        e.[personal_email],
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


def send_email_smtp_advanced(to_email, subject, html_body, attachment_path_list=None):
    """
    Envía un correo SMTP con uno o más archivos PDF adjuntos.
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

        # Adjuntar solo PDFs
        if attachment_path_list:
            for pdf_path_str in attachment_path_list:
                pdf_path = Path(pdf_path_str)

                if not pdf_path.exists():
                    logger.warning(f"No se encontró el archivo PDF en {pdf_path}")
                    continue

                try:
                    with open(pdf_path, "rb") as pdf_file:
                        msg.add_attachment(
                            pdf_file.read(),
                            maintype="application",
                            subtype="pdf",
                            filename=pdf_path.name
                        )
                    logger.info(f"Archivo adjuntado: {pdf_path.name}")
                except Exception as e:
                    logger.error(f"Error al adjuntar {pdf_path.name}: {e}")

        # Enviar correo
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

# Definir PDFs a adjuntar
ruta_pdf_cramer = PDF_FOLDER / "Reglamento_Interno_Cramer_2024.pdf"
ruta_pdf_syf = PDF_FOLDER / "Reglamento_Interno_SYF_2024.pdf"

# Templates de correo
cuerpo_html_cramer = """
    <html>
    <head>
        <style>
            body {{ font-family: Calibri, sans-serif; }}
            p {{ font-size: 16px; }}
        </style>
    </head>
    <body>
    <p>Buenos días {nombre}.</p>
    <p>¡Te damos la bienvenida a Cramer!</p>
    <p>Adjunto encontrarás el Reglamento Interno de Higiene y Seguridad, un documento clave que contiene las normas y medidas para garantizar un entorno de trabajo seguro para todos.</p>
    <p>Te invitamos a revisarlo.</p>
    <p>¡Bienvenido/a al equipo!</p>
    </body>
    </html>
    """

cuerpo_html_syf = """
    <html>
    <head>
        <style>
            body {{ font-family: Calibri, sans-serif; }}
            p {{ font-size: 16px; }}
        </style>
    </head>
    <body>
    <p>Buenos días {nombre}.</p>
    <p>¡Te damos la bienvenida a Sabores y Fragancias!</p>
    <p>Adjunto encontrarás el Reglamento Interno de Higiene y Seguridad, un documento clave que contiene las normas y medidas para garantizar un entorno de trabajo seguro para todos.</p>
    <p>Te invitamos a revisarlo.</p>
    <p>¡Bienvenido/a al equipo!</p>
    </body>
    </html>
    """

emails_enviados = 0
emails_fallidos = 0

# Iterar sobre el DataFrame
for idx, fila in df_alertas.iterrows():
    nombre = fila["first_name"]
    #correo = fila["personal_email"]
    correo = 'gpavez@cramer.cl'
    empresa = fila["empresa"]
    
    logger.info(f"Procesando empleado {idx+1}/{len(df_alertas)}: {fila['full_name']} - {empresa}")
    
    if empresa == "CARLOS CRAMER PRODUCTOS AROMÁTICOS S.A. C.I.":
        ruta_pdf = ruta_pdf_cramer
        cuerpo_html = cuerpo_html_cramer.format(nombre=nombre)
    elif empresa == "Sabores Y Fragancias.Cl Comercial Ltda.":
        ruta_pdf = ruta_pdf_syf
        cuerpo_html = cuerpo_html_syf.format(nombre=nombre)
    else:
        ruta_pdf = ruta_pdf_cramer
        cuerpo_html = cuerpo_html_cramer.format(nombre=nombre)
        logger.warning(f"Empresa no reconocida: {empresa}. Usando template de Cramer por defecto")

    asunto = "Reglamento interno de Higiene y Seguridad"
    lista_archivos_adjuntos = [ruta_pdf]
    
    # Enviar correo
    exito = send_email_smtp_advanced(
        correo, 
        asunto, 
        cuerpo_html, 
        lista_archivos_adjuntos
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
