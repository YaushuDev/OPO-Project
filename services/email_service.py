# services/email_service.py
"""
Servicio para envío de correos electrónicos con reportes adjuntos.
Maneja el envío de reportes Excel por correo usando configuración SMTP.
"""

import os
import json
import smtplib
import ssl
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailService:
    """Servicio para envío de correos electrónicos."""

    def __init__(self):
        """Inicializa el servicio de email."""
        self.smtp_config_file = Path("config") / "smtp_config.json"
        self.recipients_config_file = Path("config") / "email_recipients.json"

    def send_report(self, report_path):
        """
        Envía un reporte por correo electrónico.

        Args:
            report_path (str): Ruta del archivo de reporte a enviar

        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            # Cargar configuraciones
            smtp_config = self._load_smtp_config()
            recipients_config = self._load_recipients_config()

            if not smtp_config:
                raise Exception("No se encontró configuración SMTP. Configure SMTP primero.")

            if not recipients_config:
                raise Exception("No se encontró configuración de destinatarios. Configure destinatarios primero.")

            # Crear mensaje
            msg = self._create_message(smtp_config, recipients_config, report_path)

            # Enviar correo
            self._send_email(smtp_config, msg)

            return True

        except Exception as e:
            print(f"Error al enviar correo: {e}")
            return False

    def _load_smtp_config(self):
        """
        Carga configuración SMTP.

        Returns:
            dict: Configuración SMTP o None si no existe
        """
        try:
            if self.smtp_config_file.exists():
                with open(self.smtp_config_file, "r", encoding="utf-8") as file:
                    return json.load(file)
        except Exception:
            pass
        return None

    def _load_recipients_config(self):
        """
        Carga configuración de destinatarios.

        Returns:
            dict: Configuración de destinatarios o None si no existe
        """
        try:
            if self.recipients_config_file.exists():
                with open(self.recipients_config_file, "r", encoding="utf-8") as file:
                    return json.load(file)
        except Exception:
            pass
        return None

    def _create_message(self, smtp_config, recipients_config, report_path):
        """
        Crea el mensaje de correo con el reporte adjunto.

        Args:
            smtp_config (dict): Configuración SMTP
            recipients_config (dict): Configuración de destinatarios
            report_path (str): Ruta del archivo de reporte

        Returns:
            MIMEMultipart: Mensaje de correo preparado
        """
        # Crear mensaje
        msg = MIMEMultipart()

        # Configurar destinatarios
        msg['From'] = smtp_config['username']
        msg['To'] = recipients_config['recipient']

        # Agregar CC si existe
        cc_emails = recipients_config.get('cc', '').strip()
        if cc_emails:
            msg['Cc'] = cc_emails

        # Configurar asunto
        subject_template = recipients_config.get('subject_template', 'Reporte de Búsqueda de Correos - {date}')
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg['Subject'] = subject_template.format(date=current_date)

        # Crear cuerpo del mensaje
        body = self._create_email_body(report_path)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Adjuntar archivo de reporte
        if os.path.exists(report_path):
            self._attach_file(msg, report_path)

        return msg

    def _create_email_body(self, report_path):
        """
        Crea el cuerpo del mensaje de correo.

        Args:
            report_path (str): Ruta del archivo de reporte

        Returns:
            str: Cuerpo del mensaje
        """
        filename = Path(report_path).name
        current_datetime = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")

        body = f"""Estimado/a,

Se adjunta el reporte de búsqueda de correos generado automáticamente.

📋 INFORMACIÓN DEL REPORTE:
• Archivo: {filename}
• Generado el: {current_datetime}
• Sistema: Bot de Búsqueda de Correos

📊 CONTENIDO:
• Listado completo de perfiles de búsqueda
• Estadísticas de correos encontrados
• Fechas de última búsqueda por perfil
• Resumen ejecutivo con métricas clave

Este reporte ha sido generado automáticamente por el sistema de búsqueda de correos.

Saludos cordiales,
Sistema Automatizado de Reportes
"""
        return body

    def _attach_file(self, msg, file_path):
        """
        Adjunta un archivo al mensaje de correo.

        Args:
            msg (MIMEMultipart): Mensaje de correo
            file_path (str): Ruta del archivo a adjuntar
        """
        filename = Path(file_path).name

        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}',
        )

        msg.attach(part)

    def _send_email(self, smtp_config, msg):
        """
        Envía el mensaje de correo usando SMTP.

        Args:
            smtp_config (dict): Configuración SMTP
            msg (MIMEMultipart): Mensaje de correo

        Raises:
            Exception: Si hay error en el envío
        """
        server = None
        try:
            # Crear contexto SSL seguro
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Establecer conexión SMTP
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])

            if smtp_config.get('use_tls', False):
                server.starttls(context=context)

            # Autenticar
            server.login(smtp_config['username'], smtp_config['password'])

            # Obtener lista de destinatarios
            recipients = [msg['To']]
            if msg.get('Cc'):
                cc_list = [email.strip() for email in msg['Cc'].split(',')]
                recipients.extend(cc_list)

            # Enviar mensaje
            text = msg.as_string()
            server.sendmail(smtp_config['username'], recipients, text)

        finally:
            if server:
                server.quit()

    def test_configuration(self):
        """
        Prueba la configuración de correo actual.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            smtp_config = self._load_smtp_config()
            recipients_config = self._load_recipients_config()

            if not smtp_config:
                return False, "No se encontró configuración SMTP"

            if not recipients_config:
                return False, "No se encontró configuración de destinatarios"

            # Intentar conexión SMTP básica
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls(context=context)
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()

            return True, "Configuración de correo válida"

        except Exception as e:
            return False, f"Error en configuración: {e}"