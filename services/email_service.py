# services/email_service.py
"""
Servicio para envío de correos electrónicos con reportes adjuntos.
Maneja el envío de reportes Excel por correo usando configuración SMTP,
permitiendo plantillas de asunto diferentes para reportes diarios, semanales y mensuales.
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

from services.email_config import (
    FREQUENCY_DISPLAY_NAMES,
    FREQUENCY_LABELS,
    get_frequency_settings,
    normalize_recipients_config,
)


class EmailService:
    """Servicio para envío de correos electrónicos con soporte para tipos de reportes."""

    def __init__(self):
        """Inicializa el servicio de email."""
        self.smtp_config_file = Path("config") / "smtp_config.json"
        self.recipients_config_file = Path("config") / "email_recipients.json"

    def send_report(self, report_path, report_type="daily"):
        """
        Envía un reporte por correo electrónico.

        Args:
            report_path (str): Ruta del archivo de reporte a enviar
            report_type (str): Tipo de reporte ('daily', 'weekly' o 'monthly')

        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            # Cargar configuraciones
            smtp_config = self._load_smtp_config()
            recipients_config_raw = self._load_recipients_config()

            if not smtp_config:
                raise Exception("No se encontró configuración SMTP. Configure SMTP primero.")

            if recipients_config_raw is None:
                raise Exception("No se encontró configuración de destinatarios. Configure destinatarios primero.")

            recipients_config = normalize_recipients_config(recipients_config_raw)

            # Crear mensaje
            msg = self._create_message(smtp_config, recipients_config, report_path, report_type)

            # Enviar correo
            self._send_email(smtp_config, msg)

            return True

        except Exception as e:
            print(f"Error al enviar correo: {e}")
            return False

    def send_performance_alert(self, recipient_email, profiles_info, threshold=90):
        """Envía una alerta cuando los perfiles no alcanzan el porcentaje óptimo."""
        try:
            smtp_config = self._load_smtp_config()
            if not smtp_config:
                raise Exception("No se encontró configuración SMTP. Configure SMTP primero.")

            if not recipient_email:
                raise Exception("Debe especificar un destinatario para la alerta de rendimiento.")

            recipient = recipient_email.strip()
            if not recipient:
                raise Exception("El destinatario de alerta no puede estar vacío.")

            msg = MIMEMultipart()
            msg['From'] = smtp_config['username']
            msg['To'] = recipient

            current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
            msg['Subject'] = (
                f"Alerta de seguimiento: perfiles por debajo de {threshold}% ({current_date})"
            )

            body = self._create_alert_body(profiles_info, threshold)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            self._send_email(smtp_config, msg)
            return True

        except Exception as e:
            print(f"Error al enviar alerta de rendimiento: {e}")
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

    def _create_message(self, smtp_config, recipients_config, report_path, report_type="daily"):
        """
        Crea el mensaje de correo con el reporte adjunto.

        Args:
            smtp_config (dict): Configuración SMTP
            recipients_config (dict): Configuración de destinatarios
            report_path (str): Ruta del archivo de reporte
            report_type (str): Tipo de reporte ('daily', 'weekly' o 'monthly')

        Returns:
            MIMEMultipart: Mensaje de correo preparado
        """
        # Crear mensaje
        msg = MIMEMultipart()

        frequency = report_type if report_type in FREQUENCY_LABELS else "daily"
        settings = get_frequency_settings(recipients_config, frequency)

        recipient_email = settings.get('recipient', '')
        if not recipient_email:
            raise Exception(f"No hay destinatario configurado para el {FREQUENCY_DISPLAY_NAMES[frequency]}.")

        # Configurar destinatarios
        msg['From'] = smtp_config['username']
        msg['To'] = recipient_email

        # Agregar CC si existe
        cc_emails = settings.get('cc', '').strip()
        if cc_emails:
            msg['Cc'] = cc_emails

        subject_template = settings.get('subject_template')
        report_type_text = FREQUENCY_LABELS.get(frequency, 'diario')

        # Configurar asunto
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg['Subject'] = subject_template.format(date=current_date)

        # Crear cuerpo del mensaje
        body = self._create_email_body(report_path, report_type_text)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Adjuntar archivo de reporte
        if os.path.exists(report_path):
            self._attach_file(msg, report_path)

        return msg

    def _create_alert_body(self, profiles_info, threshold):
        """Genera el cuerpo del correo de alerta de rendimiento."""
        current_datetime = datetime.now().strftime("%d/%m/%Y a las %H:%M")

        if not profiles_info:
            profiles_info = []

        lines = [
            "Estimado/a,",
            "",
            (
                f"Se detectó que los siguientes perfiles con seguimiento óptimo"
                f" están por debajo del {threshold}% de éxito."
            ),
            "",
            f"Fecha de revisión: {current_datetime}",
            "",
            "Perfiles afectados:"
        ]

        for info in profiles_info:
            name = info.get('name', 'Perfil sin nombre')
            success = info.get('success_percentage')
            success_text = f"{success:.1f}%" if isinstance(success, (int, float)) else "N/D"
            optimal = info.get('optimal_executions')
            optimal_text = optimal if optimal is not None else "N/D"
            found = info.get('found_emails')
            found_text = found if found is not None else "N/D"
            last_search = info.get('last_search')
            if last_search:
                try:
                    last_search_dt = datetime.fromisoformat(last_search)
                    last_search_text = last_search_dt.strftime("%d/%m/%Y %H:%M")
                except (ValueError, TypeError):
                    last_search_text = str(last_search)
            else:
                last_search_text = "Sin registros recientes"

            lines.append(
                f"• {name}: {success_text} de éxito | Óptimo: {optimal_text} | "
                f"Ejecuciones: {found_text} | Última búsqueda: {last_search_text}"
            )

        lines.extend([
            "",
            "Se recomienda revisar la configuración de estos perfiles para ajustar criterios,",
            "remitentes o cantidad de ejecuciones óptimas según corresponda.",
            "",
            "Este mensaje se generó automáticamente desde el sistema de seguimiento de perfiles.",
            "Saludos cordiales,",
            "Sistema Automatizado de Alertas"
        ])

        return "\n".join(lines)

    def _create_email_body(self, report_path, report_type_text):
        """
        Crea el cuerpo del mensaje de correo.

        Args:
            report_path (str): Ruta del archivo de reporte
            report_type_text (str): Texto descriptivo del tipo de reporte

        Returns:
            str: Cuerpo del mensaje
        """
        filename = Path(report_path).name
        current_datetime = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")

        body = f"""Estimado/a,

Se adjunta el reporte {report_type_text} de búsqueda de correos generado automáticamente.

📋 INFORMACIÓN DEL REPORTE:
- Archivo: {filename}
- Generado el: {current_datetime}
- Tipo: Reporte {report_type_text}
- Sistema: Bot de Búsqueda de Correos

📊 CONTENIDO:
- Listado completo de perfiles de búsqueda
- Estadísticas de correos encontrados
- Fechas de última búsqueda por perfil
- Resumen ejecutivo con métricas clave
"""

        # Añadir información adicional según el tipo de reporte
        if report_type_text == "semanal":
            body += """
El reporte semanal contiene datos consolidados de toda la semana
con métricas acumuladas y análisis comparativo semanal.
"""
        elif report_type_text == "mensual":
            body += """
El reporte mensual contiene un análisis completo del rendimiento durante el mes,
con métricas acumuladas, tendencias mensuales y estadísticas comparativas.
"""

        body += """
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
            recipients_config_raw = self._load_recipients_config()

            if not smtp_config:
                return False, "No se encontró configuración SMTP"

            if recipients_config_raw is None:
                return False, "No se encontró configuración de destinatarios"

            normalized_recipients = normalize_recipients_config(recipients_config_raw)
            missing = [
                name
                for key, name in FREQUENCY_DISPLAY_NAMES.items()
                if not normalized_recipients.get(key, {}).get('recipient')
            ]

            if missing:
                return False, f"Falta destinatario para: {', '.join(missing)}"

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