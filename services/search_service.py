# search_service.py
"""
Servicio para búsqueda de correos electrónicos en bandejas de entrada reales.
Implementa búsqueda IMAP mejorada con múltiples criterios de asunto, detección precisa
de correos por timestamp y suma de resultados con rango de fechas expandido.
"""

import imaplib
import email
import ssl
import json
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime


class SearchService:
    """Servicio para buscar correos electrónicos reales vía IMAP con detección mejorada por timestamp."""

    # Mapeo de servidores SMTP a IMAP
    IMAP_SERVERS = {
        "smtp.gmail.com": {"server": "imap.gmail.com", "port": 993},
        "smtp-mail.outlook.com": {"server": "outlook.office365.com", "port": 993}
    }

    def __init__(self, data_dir=None, log_callback=None):
        """
        Inicializa el servicio de búsqueda IMAP mejorada.

        Args:
            data_dir (str, optional): Directorio de datos para caché. Por defecto "data".
            log_callback (callable, optional): Función para registrar logs.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.log_callback = log_callback
        self.smtp_config_file = Path("config") / "smtp_config.json"

        # Crear directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)

        # Sistema de caché por día mejorado
        self.cache_file = self.data_dir / "daily_email_cache.json"
        self.email_cache = {}
        self._load_cache()

    def search_emails(self, profile):
        """
        Busca correos electrónicos del día actual con detección mejorada por timestamp.
        Utiliza rango de fechas expandido y verificación manual de timestamps.

        Args:
            profile: Perfil de búsqueda con los criterios (puede tener hasta 3)

        Returns:
            int: Número total de correos encontrados sumando todos los criterios
        """
        self._log(f"🔍 Iniciando búsqueda mejorada con perfil: {profile.name}")

        # Verificar que el perfil tenga criterios válidos
        if not hasattr(profile, 'search_criteria') or not profile.search_criteria:
            self._log("❌ Error: El perfil no tiene criterios de búsqueda válidos")
            return 0

        # Compatibilidad hacia atrás: convertir string a lista si es necesario
        criterios = profile.search_criteria
        if isinstance(criterios, str):
            criterios = [criterios]

        self._log(f"📋 Criterios configurados: {len(criterios)}")
        for i, criterio in enumerate(criterios, 1):
            self._log(f"  └── Criterio {i}: '{criterio}'")

        start_time = datetime.now()
        total_found = 0

        try:
            # Cargar configuración SMTP
            smtp_config = self._load_smtp_config()
            if not smtp_config:
                self._log("❌ Error: No se encontró configuración SMTP")
                return 0

            # Buscar correos para cada criterio con método mejorado
            for i, criterio in enumerate(criterios, 1):
                self._log(f"🎯 Procesando criterio {i}/{len(criterios)}: '{criterio}'")

                # Crear clave de caché única para hoy y este criterio específico
                today_str = date.today().isoformat()
                cache_key = f"{today_str}_{criterio.strip().lower()}"

                # Verificar caché para este criterio específico
                if cache_key in self.email_cache:
                    count = self.email_cache[cache_key]
                    self._log(f"💾 Usando resultados en caché para '{criterio}': {count} correos")
                else:
                    # Realizar búsqueda IMAP mejorada para este criterio
                    count = self._perform_enhanced_imap_search(smtp_config, criterio.strip())

                    # Guardar en caché
                    self.email_cache[cache_key] = count
                    self._save_cache()

                self._log(f"✅ Criterio '{criterio}': {count} correos encontrados")
                total_found += count

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._log(f"🏁 Búsqueda mejorada completada en {duration:.2f} segundos")
            self._log(f"📊 TOTAL de correos encontrados: {total_found} (suma de {len(criterios)} criterios)")

            return total_found

        except Exception as e:
            self._log(f"💥 Error durante la búsqueda mejorada: {e}")
            return 0

    def _perform_enhanced_imap_search(self, smtp_config, search_criteria):
        """
        Realiza búsqueda IMAP mejorada con rango de fechas expandido y verificación de timestamp.

        Args:
            smtp_config (dict): Configuración SMTP/IMAP
            search_criteria (str): Criterio de búsqueda para el asunto

        Returns:
            int: Número de correos que coinciden con este criterio específico
        """
        mail = None
        try:
            # Obtener configuración IMAP del servidor SMTP
            smtp_server = smtp_config.get('server')
            imap_config = self.IMAP_SERVERS.get(smtp_server)

            if not imap_config:
                self._log(f"❌ Servidor IMAP no soportado: {smtp_server}")
                return 0

            self._log(f"🔗 Conectando a {imap_config['server']} para criterio '{search_criteria}'...")

            # Crear conexión IMAP con SSL
            mail = imaplib.IMAP4_SSL(imap_config['server'], imap_config['port'])

            # Autenticar con las mismas credenciales SMTP
            mail.login(smtp_config['username'], smtp_config['password'])

            # Seleccionar bandeja de entrada
            mail.select('inbox')

            # BÚSQUEDA MEJORADA: Usar rango de fechas expandido
            today = date.today()
            yesterday = today - timedelta(days=1)

            # Buscar correos desde ayer para capturar correos en el límite del día
            yesterday_str = yesterday.strftime("%d-%b-%Y")
            search_criteria_imap = f'(SINCE "{yesterday_str}")'

            self._log(f"📅 Buscando correos desde {yesterday_str} para filtrar por timestamp")

            status, messages = mail.search(None, search_criteria_imap)

            if status != 'OK':
                self._log(f"❌ Error al buscar correos para criterio '{search_criteria}'")
                return 0

            message_ids = messages[0].split()
            total_candidates = len(message_ids)

            if total_candidates == 0:
                self._log(f"📭 No hay correos candidatos para analizar")
                return 0

            self._log(f"📬 Analizando {total_candidates} correos candidatos para el criterio '{search_criteria}'...")

            # Filtrar por criterio de búsqueda y verificar timestamp del día actual
            matching_count = 0
            search_term = search_criteria.lower()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            for msg_id in message_ids:
                try:
                    # Obtener el correo con headers
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parsear el mensaje
                    email_message = email.message_from_bytes(msg_data[0][1])

                    # Verificar timestamp del correo
                    date_header = email_message.get('Date')
                    if not date_header:
                        continue

                    try:
                        # Convertir fecha del correo a datetime
                        email_datetime = parsedate_to_datetime(date_header)

                        # Convertir a fecha local si tiene zona horaria
                        if email_datetime.tzinfo is not None:
                            email_datetime = email_datetime.astimezone()
                            # Remover zona horaria para comparación
                            email_datetime = email_datetime.replace(tzinfo=None)

                        # VERIFICACIÓN MEJORADA: Solo correos del día actual
                        if not (today_start <= email_datetime <= today_end):
                            continue

                    except (ValueError, TypeError) as e:
                        self._log(f"⚠️ Error procesando fecha del correo {msg_id}: {e}")
                        continue

                    # Verificar el criterio de búsqueda en el asunto
                    subject = email_message['subject']
                    if subject:
                        # Decodificar el asunto si está codificado
                        decoded_subject = self._decode_subject(subject)

                        # Verificar si el criterio de búsqueda está en el asunto
                        if search_term in decoded_subject.lower():
                            matching_count += 1
                            timestamp_str = email_datetime.strftime("%H:%M:%S")
                            self._log(f"✨ Match encontrado [{timestamp_str}]: {decoded_subject[:60]}...")

                except Exception as e:
                    self._log(f"⚠️ Error procesando mensaje {msg_id}: {e}")
                    continue

            self._log(
                f"🎯 Criterio '{search_criteria}': {matching_count}/{total_candidates} correos válidos del día actual")
            return matching_count

        except imaplib.IMAP4.error as e:
            self._log(f"❌ Error IMAP para criterio '{search_criteria}': {e}")
            return 0
        except Exception as e:
            self._log(f"💥 Error inesperado en búsqueda IMAP para '{search_criteria}': {e}")
            return 0
        finally:
            # Cerrar conexión IMAP
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass

    def _decode_subject(self, subject):
        """
        Decodifica el asunto del correo si está codificado.

        Args:
            subject (str): Asunto codificado

        Returns:
            str: Asunto decodificado
        """
        try:
            decoded_parts = decode_header(subject)
            decoded_subject = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_subject += part.decode(encoding)
                    else:
                        decoded_subject += part.decode('utf-8', errors='ignore')
                else:
                    decoded_subject += part

            return decoded_subject
        except Exception as e:
            self._log(f"⚠️ Error decodificando asunto: {e}")
            return subject if isinstance(subject, str) else str(subject)

    def _load_smtp_config(self):
        """
        Carga la configuración SMTP desde el archivo.

        Returns:
            dict: Configuración SMTP o None si no existe
        """
        try:
            if self.smtp_config_file.exists():
                with open(self.smtp_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self._log("⚙️ Configuración SMTP cargada para búsqueda IMAP")
                return config
        except Exception as e:
            self._log(f"❌ Error cargando configuración SMTP: {e}")
        return None

    def _load_cache(self):
        """Carga la caché de correos desde el archivo."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    all_cache = json.load(f)

                # Limpiar caché antigua (solo mantener del día actual)
                today_str = date.today().isoformat()
                self.email_cache = {
                    key: value for key, value in all_cache.items()
                    if key.startswith(today_str)
                }

                self._log(f"💾 Caché de correos cargada: {len(self.email_cache)} entradas del día actual")
            except Exception as e:
                self._log(f"⚠️ Error al cargar caché: {e}")
                self.email_cache = {}
        else:
            self.email_cache = {}

    def _save_cache(self):
        """Guarda la caché de correos en el archivo."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.email_cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self._log(f"⚠️ Error al guardar caché: {e}")

    def _log(self, message):
        """
        Registra mensaje en el log.

        Args:
            message (str): Mensaje a registrar
        """
        if self.log_callback:
            self.log_callback(message)

    def clear_cache(self):
        """Limpia la caché de búsquedas."""
        self.email_cache = {}
        try:
            if self.cache_file.exists():
                os.remove(self.cache_file)
            self._log("🗑️ Caché de correos limpiada")
        except Exception as e:
            self._log(f"⚠️ Error al limpiar caché: {e}")

    def get_cache_info(self):
        """
        Obtiene información sobre la caché actual.

        Returns:
            dict: Información de la caché
        """
        today_str = date.today().isoformat()
        today_entries = len([k for k in self.email_cache.keys() if k.startswith(today_str)])

        return {
            "total_entries": len(self.email_cache),
            "today_entries": today_entries,
            "cache_date": today_str,
            "enhanced_search": True  # Indicador de que usa búsqueda mejorada
        }