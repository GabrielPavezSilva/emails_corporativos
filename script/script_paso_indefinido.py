""""
Envia un correo desde gerencia de personas al pasar a indefinido.
"""
import os
import re
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
import logging
from pathlib import Path
from email.message import EmailMessage
import smtplib
import ssl

# ===========================================
# CONFIGURACIÓN INICIAL
# ===========================================
load_dotenv(override=True)

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
PROJECT_ROOT = SCRIPT_DIR.parent
LOG_FOLDER = PROJECT_ROOT / "logs"
IMG_FOLDER = PROJECT_ROOT / "img"
PDF_FOLDER = PROJECT_ROOT / "pdf"
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

ruta_pdf_cramer_1 = PDF_FOLDER / "Beneficios.pdf"
ruta_pdf_cramer_2 = PDF_FOLDER / "Formulario_Reembolsos_Nuevo.pdf"
ruta_pdf_cramer_3 = PDF_FOLDER / "Instructivo_seguro.pdf"

# Log con fecha para rotación mensual
log_filename = LOG_FOLDER / f"correo_indefinido_{date.today().strftime('%Y%m')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===========================================
# VARIABLES DE ENTORNO
# ===========================================
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_EMAIL")
SMTP_PASS = os.getenv("SMTP_PASSWORD")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # segundos

# ===========================================
# MODO PRUEBA
# Cambiar a False para enviar a los destinatarios reales
# ===========================================
MODO_PRUEBA   = True
CORREO_PRUEBA = "gpavez@cramer.cl"


# ===========================================
# FUNCIONES DE VALIDACIÓN
# ===========================================
def validar_email(email: str) -> bool:
    """Valida formato básico de email."""
    if not email:
        return False
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))


def verificar_imagen(ruta: Path) -> bool:
    """Verifica que la imagen exista antes de procesar."""
    if not ruta.exists():
        logger.error(f"❌ Imagen no encontrada: {ruta}")
        logger.error("   Asegúrate de copiar 'contrato_ind.png' a la carpeta 'img/'")
        return False
    logger.info(f"✅ Imagen encontrada: {ruta.name}")
    return True


# ===========================================
# PLANTILLA HTML
# ===========================================
def generar_html_correo(nombre: str, id_imagen: str) -> str:
    """Genera el cuerpo HTML del correo de paso a indefinido."""
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Calibri, Arial, sans-serif; line-height: 1.6; }}
            p {{ font-size: 16px; margin: 10px 0; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .imagen-container {{ padding: 15px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <p>Hola {nombre},</p>

            <p>
            <strong>¡Tenemos una excelente noticia para compartir contigo!</strong>
            </p>

            <div class="imagen-container">
                <a href="https://cramer.buk.cl/benefits" target="_blank">
                    <img src="cid:{id_imagen}" alt="¡FELICITACIONES!"
                         style="max-width: 100%; border-radius: 4px; border: none;">
                </a>
            </div>

            <p>
            <strong>Adjunto</strong> encontrarás los <strong>beneficios</strong> que revisamos en el cierre de tu proceso,
            <strong>formulario</strong> para futuros reembolsos dentales y un <strong>instructivo</strong> del funcionamiento del seguro.
            </p>

            <p>
            Felicitaciones por este importante hito y gracias por seguir construyendo este camino junto a nosotros.<br><br>
            ¡Saludos!
            </p>
        </div>
    </body>
    </html>
    """


# ===========================================
# ENVÍO DE CORREOS
# ===========================================
def send_embedded_email_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    image_path: Path,
    image_cid: str,
    pdf_adjuntos: list = None,
    max_retries: int = MAX_RETRIES
) -> bool:
    """
    Envía correo con imagen embebida y PDFs adjuntos.
    Implementa reintentos automáticos en caso de fallo.
    """
    if not validar_email(to_email):
        logger.warning(f"⚠️ Email inválido, saltando: {to_email}")
        return False

    for intento in range(1, max_retries + 1):
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = SMTP_USER
            msg["To"] = to_email

            msg.set_content("Este correo requiere un cliente compatible con HTML.")
            msg.add_alternative(html_body, subtype="html")

            # Embeber imagen
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
                subtype = image_path.suffix.lstrip('.').lower()
                if subtype == 'jpg':
                    subtype = 'jpeg'

                msg.get_payload()[1].add_related(
                    img_data,
                    maintype="image",
                    subtype=subtype,
                    cid=image_cid
                )

            # Adjuntar PDFs
            if pdf_adjuntos:
                for pdf_path in pdf_adjuntos:
                    if pdf_path.exists():
                        with open(pdf_path, "rb") as pdf_file:
                            msg.add_attachment(
                                pdf_file.read(),
                                maintype="application",
                                subtype="pdf",
                                filename=pdf_path.name
                            )
                    else:
                        logger.warning(f"⚠️ PDF no encontrado, se omite: {pdf_path.name}")

            # Enviar
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=30) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)

            logger.info(f"✅ Email enviado a: {to_email}")
            return True

        except smtplib.SMTPException as e:
            logger.warning(f"⚠️ Intento {intento}/{max_retries} fallido para {to_email}: {e}")
            if intento < max_retries:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando a {to_email}: {e}")
            break

    logger.error(f"❌ No se pudo enviar email a {to_email} después de {max_retries} intentos")
    return False


# ===========================================
# FUNCIÓN PRINCIPAL
# ===========================================
def main():
    """Función principal del script."""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO SCRIPT DE PASO A INDEFINIDO")
    logger.info(f"📅 Fecha de ejecución: {date.today()}")
    if MODO_PRUEBA:
        logger.info(f"*** MODO PRUEBA ACTIVO — todos los correos se enviarán a: {CORREO_PRUEBA} ***")
    logger.info("=" * 60)

    # 1. Verificar imagen
    ruta_imagen = IMG_FOLDER / "contrato_ind.png"
    if not verificar_imagen(ruta_imagen):
        sys.exit(1)

    # 2. Definir fechas
    hoy = date.today()
    #hoy = datetime.strptime('2026-02-03', '%Y-%m-%d').date()
    ingreso = hoy - relativedelta(months=3)

    logger.info(f"📆 Buscando empleados con start_date={hoy} y active_since={ingreso}")

    # 3. Conectar por SSH tunnel y ejecutar query
    try:
        tunnel = SSHTunnelForwarder(
            (os.getenv('SSH_HOST'), int(os.getenv('SSH_PORT', '22'))),
            ssh_username=os.getenv('SSH_USER'),
            ssh_password=os.getenv('SSH_PASSWORD'),
            remote_bind_address=('localhost', int(os.getenv('PG_PORT', '5432')))
        )
        tunnel.start()
        logger.info(f"Túnel SSH establecido — puerto local: {tunnel.local_bind_port}")

        engine = create_engine(
            f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}@127.0.0.1:{tunnel.local_bind_port}/{os.getenv('PG_DATABASE')}"
        )

        query_sql = f"""
        SELECT
            full_name,
            first_name,
            personal_email,
            status,
            active_since,
            start_date
        FROM rh.employees
        WHERE
            start_date::date = '{hoy}'
            AND active_since::date = '{ingreso}'
            AND status = 'activo'
            AND payment_method = 'Transferencia Bancaria'
            AND contract_finishing_date_1 IS NULL
            AND contract_finishing_date_2 IS NULL
        """

        df_alertas = pd.read_sql_query(query_sql, engine)
        logger.info(f"📊 Consulta SQL ejecutada. Registros encontrados: {len(df_alertas)}")
        logger.info(f"Datos:\n{df_alertas.to_string()}")

    except Exception as e:
        logger.error(f"❌ Error al ejecutar consulta SQL: {e}", exc_info=True)
        raise
    finally:
        if 'tunnel' in locals() and tunnel.is_active:
            tunnel.stop()
            logger.info("Túnel SSH cerrado")

    # 4. Verificar si hay empleados
    if df_alertas.empty:
        logger.info("ℹ️ No hay empleados para notificar hoy")
        logger.info("=" * 60)
        return

    logger.info("👥 Empleados a notificar:")
    for _, row in df_alertas.iterrows():
        logger.info(f"   - {row['full_name']} | {row['personal_email']}")

    # 5. Enviar correos
    id_imagen = "img_indefinido"
    emails_enviados  = 0
    emails_fallidos  = 0
    emails_invalidos = 0

    for _, fila in df_alertas.iterrows():
        nombre      = fila["first_name"]
        correo_real = fila["personal_email"]
        correo      = CORREO_PRUEBA if MODO_PRUEBA else correo_real

        if not validar_email(correo):
            logger.warning(f"⚠️ Email inválido para {fila['full_name']}: {correo}")
            emails_invalidos += 1
            continue

        asunto      = f"¡Felicitaciones por tu contrato indefinido, {nombre}!"
        cuerpo_html = generar_html_correo(nombre, id_imagen)

        destino_log = f"{correo} (prueba → real: {correo_real})" if MODO_PRUEBA else correo
        logger.info(f"   📧 Enviando a: {destino_log}")

        if send_embedded_email_smtp(
            correo, asunto, cuerpo_html, ruta_imagen, id_imagen,
            pdf_adjuntos=[ruta_pdf_cramer_1, ruta_pdf_cramer_2, ruta_pdf_cramer_3]
        ):
            emails_enviados += 1
        else:
            emails_fallidos += 1

    # 6. Resumen
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE EJECUCIÓN")
    logger.info(f"   Total empleados encontrados: {len(df_alertas)}")
    logger.info(f"   ✅ Emails enviados:  {emails_enviados}")
    logger.info(f"   ❌ Emails fallidos:  {emails_fallidos}")
    logger.info(f"   ⚠️ Emails inválidos: {emails_invalidos}")
    logger.info("=" * 60)

    if emails_fallidos > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
