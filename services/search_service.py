# search_service.py
"""
Servicio mejorado para búsqueda de correos electrónicos en bandejas de entrada reales.
Implementa búsqueda IMAP robusta con múltiples criterios, deduplicación de resultados,
búsqueda en múltiples campos y sistema de caché optimizado.
IMPORTANTE: No marca los correos como leídos usando BODY.PEEK.
"""

import imaplib
import email
import ssl
import json
import os
import hashlib
import re
from pathlib import Path
from datetime import datetime, date, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from collections import defaultdict


class SearchService:
    """Servicio mejorado para buscar correos electrónicos con múltiples criterios robustos."""

    # Mapeo de servidores SMTP a IMAP
    IMAP_SERVERS = {
        "smtp.gmail.com": {"server": "imap.gmail.com", "port": 993},
        "smtp-mail.outlook.com": {"server": "outlook.office365.com", "port": 993}
    }

    def __init__(self, data_dir=None, log_callback=None):
        """
        Inicializa el servicio de búsqueda IMAP mejorado.

        Args:
            data_dir (str, optional): Directorio de datos para caché. Por defecto "data".
            log_callback (callable, optional): Función para registrar logs.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.log_callback = log_callback
        self.smtp_config_file = Path("config") / "smtp_config.json"

        # Crear directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)

        # Sistema de caché mejorado
        self.cache_file = self.data_dir / "enhanced_email_cache.json"
        self.search_cache = {}
        self._load_cache()

        # Configuraciones de búsqueda
        self.search_fields = ['subject', 'from', 'body']  # Campos donde buscar
        self.max_search_days = 3  # Buscar en los últimos N días para mayor robustez

    def search_emails(self, profile):
        """
        Busca correos electrónicos del día actual basados en todos los criterios del perfil.
        Implementa búsqueda robusta con deduplicación y múltiples campos.

        Args:
            profile: Perfil de búsqueda con los criterios (puede tener hasta 3)

        Returns:
            int: Número total de correos únicos encontrados
        """
        self._log(f"🔍 Iniciando búsqueda mejorada: {profile.name}")

        # Verificar que el perfil tenga criterios válidos
        if not hasattr(profile, 'search_criteria') or not profile.search_criteria:
            self._log("❌ Error: El perfil no tiene criterios de búsqueda válidos")
            return 0

        # Normalizar criterios
        criterios = self._normalize_criteria(profile.search_criteria)

        if not criterios:
            self._log("❌ Error: No hay criterios válidos después de la normalización")
            return 0

        self._log(f"📋 Criterios normalizados: {len(criterios)}")
        for i, criterio in enumerate(criterios, 1):
            self._log(f"  ✓ Criterio {i}: '{criterio}'")

        start_time = datetime.now()

        try:
            # Cargar configuración SMTP
            smtp_config = self._load_smtp_config()
            if not smtp_config:
                self._log("❌ Error: No se encontró configuración SMTP")
                return 0

            # Generar clave de caché para toda la búsqueda
            cache_key = self._generate_cache_key(criterios)

            # Verificar caché
            if cache_key in self.search_cache:
                cached_result = self.search_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    count = cached_result['count']
                    self._log(f"⚡ Usando resultado en caché: {count} correos únicos")
                    return count
                else:
                    # Limpiar caché expirado
                    del self.search_cache[cache_key]

            # Realizar búsqueda IMAP mejorada
            unique_emails = self._perform_enhanced_imap_search(smtp_config, criterios)

            # Guardar en caché
            cache_data = {
                'count': len(unique_emails),
                'timestamp': datetime.now().isoformat(),
                'emails_hash': self._generate_emails_hash(unique_emails)
            }
            self.search_cache[cache_key] = cache_data
            self._save_cache()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._log(f"✅ Búsqueda completada en {duration:.2f} segundos")
            self._log(f"📊 TOTAL de correos únicos encontrados: {len(unique_emails)}")
            self._log(f"🔍 Método: Búsqueda mejorada con deduplicación")

            return len(unique_emails)

        except Exception as e:
            self._log(f"💥 Error durante la búsqueda: {e}")
            return 0

    def _normalize_criteria(self, search_criteria):
        """
        Normaliza y limpia los criterios de búsqueda.

        Args:
            search_criteria: Lista o string con criterios

        Returns:
            list: Lista de criterios normalizados y únicos
        """
        if isinstance(search_criteria, str):
            criterios = [search_criteria]
        elif isinstance(search_criteria, list):
            criterios = search_criteria
        else:
            return []

        # Limpiar y normalizar
        normalized = []
        for criterio in criterios:
            if isinstance(criterio, str):
                cleaned = criterio.strip()
                if cleaned and len(cleaned) >= 2:  # Mínimo 2 caracteres
                    normalized.append(cleaned)

        # Eliminar duplicados preservando orden
        unique_criteria = []
        seen = set()
        for criterio in normalized:
            criterio_lower = criterio.lower()
            if criterio_lower not in seen:
                seen.add(criterio_lower)
                unique_criteria.append(criterio)

        return unique_criteria

    def _generate_cache_key(self, criterios):
        """
        Genera una clave única para el caché basada en los criterios y la fecha.

        Args:
            criterios (list): Lista de criterios de búsqueda

        Returns:
            str: Clave de caché única
        """
        today_str = date.today().isoformat()
        criteria_str = "|".join(sorted([c.lower() for c in criterios]))
        combined = f"{today_str}:{criteria_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _is_cache_valid(self, cache_data):
        """
        Verifica si los datos en caché son válidos (no han expirado).

        Args:
            cache_data (dict): Datos del caché

        Returns:
            bool: True si el caché es válido
        """
        try:
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            now = datetime.now()

            # El caché es válido por 30 minutos
            return (now - cache_time).total_seconds() < 1800
        except:
            return False

    def _generate_emails_hash(self, emails):
        """
        Genera un hash de los emails para verificar integridad del caché.

        Args:
            emails (set): Set de IDs de emails

        Returns:
            str: Hash de los emails
        """
        emails_str = "|".join(sorted(emails))
        return hashlib.md5(emails_str.encode()).hexdigest()

    def _perform_enhanced_imap_search(self, smtp_config, criterios):
        """
        Realiza búsqueda IMAP mejorada con múltiples criterios y deduplicación.

        Args:
            smtp_config (dict): Configuración SMTP/IMAP
            criterios (list): Lista de criterios de búsqueda

        Returns:
            set: Set de IDs únicos de correos que coinciden
        """
        mail = None
        unique_emails = set()

        try:
            # Obtener configuración IMAP
            smtp_server = smtp_config.get('server')
            imap_config = self.IMAP_SERVERS.get(smtp_server)

            if not imap_config:
                self._log(f"❌ Servidor IMAP no soportado: {smtp_server}")
                return unique_emails

            self._log(f"🔗 Conectando a {imap_config['server']}...")

            # Crear conexión IMAP con SSL
            mail = imaplib.IMAP4_SSL(imap_config['server'], imap_config['port'])
            mail.login(smtp_config['username'], smtp_config['password'])
            mail.select('inbox', readonly=True)

            # Buscar correos en un rango de fechas más amplio para mayor robustez
            date_criteria = self._build_date_criteria()
            self._log(f"📅 Criterio de fecha: {date_criteria}")

            status, messages = mail.search(None, date_criteria)

            if status != 'OK':
                self._log("❌ Error al buscar correos por fecha")
                return unique_emails

            message_ids = messages[0].split()
            total_candidates = len(message_ids)

            if total_candidates == 0:
                self._log("📭 No hay correos en el rango de fechas para analizar")
                return unique_emails

            self._log(f"📧 Analizando {total_candidates} correos candidatos...")

            # Analizar cada mensaje con todos los criterios
            unique_emails = self._analyze_messages(mail, message_ids, criterios)

            self._log(f"✅ Análisis completado: {len(unique_emails)} correos únicos coinciden")

        except imaplib.IMAP4.error as e:
            self._log(f"❌ Error IMAP: {e}")
        except Exception as e:
            self._log(f"💥 Error inesperado en búsqueda IMAP: {e}")
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass

        return unique_emails

    def _build_date_criteria(self):
        """
        Construye criterio de fecha más robusto para IMAP.

        Returns:
            str: Criterio de fecha para IMAP
        """
        today = date.today()

        # Buscar desde ayer hasta mañana para capturar diferencias de zona horaria
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        yesterday_str = yesterday.strftime("%d-%b-%Y")
        tomorrow_str = tomorrow.strftime("%d-%b-%Y")

        # Criterio más amplio pero filtraremos por fecha exacta después
        return f'(SINCE "{yesterday_str}" BEFORE "{tomorrow_str}")'

    def _analyze_messages(self, mail, message_ids, criterios):
        """
        Analiza mensajes para encontrar coincidencias con los criterios.

        Args:
            mail: Conexión IMAP
            message_ids: Lista de IDs de mensajes
            criterios: Lista de criterios de búsqueda

        Returns:
            set: Set de IDs únicos de correos que coinciden
        """
        unique_emails = set()
        today = date.today()

        # Crear patrones de búsqueda optimizados
        search_patterns = []
        for criterio in criterios:
            # Escapar caracteres especiales y crear patrón case-insensitive
            escaped = re.escape(criterio.lower())
            pattern = re.compile(escaped, re.IGNORECASE | re.UNICODE)
            search_patterns.append((criterio, pattern))

        self._log(f"🎯 Patrones de búsqueda creados: {len(search_patterns)}")

        processed = 0
        matches_by_criteria = defaultdict(int)

        for msg_id in message_ids:
            try:
                # Usar BODY.PEEK para no marcar como leído
                status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[])')

                if status != 'OK' or not msg_data or not msg_data[0]:
                    continue

                # Parsear mensaje completo
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # Verificar que sea del día actual
                if not self._is_today_email(email_message, today):
                    continue

                # Extraer contenido para búsqueda
                search_content = self._extract_search_content(email_message)

                # Verificar coincidencias con cualquier criterio
                email_matches = False
                for criterio, pattern in search_patterns:
                    if self._matches_criteria(search_content, pattern):
                        matches_by_criteria[criterio] += 1
                        email_matches = True
                        break  # Un email solo cuenta una vez, aunque coincida con múltiples criterios

                if email_matches:
                    unique_emails.add(msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id))

                processed += 1
                if processed % 50 == 0:
                    self._log(f"⏳ Procesados {processed}/{len(message_ids)} correos...")

            except Exception as e:
                self._log(f"⚠️ Error procesando mensaje {msg_id}: {e}")
                continue

        # Log de estadísticas por criterio
        self._log(f"📈 Estadísticas por criterio:")
        for criterio, count in matches_by_criteria.items():
            self._log(f"  📌 '{criterio}': {count} coincidencias")

        return unique_emails

    def _is_today_email(self, email_message, today):
        """
        Verifica si el email es del día actual de manera robusta.

        Args:
            email_message: Mensaje de email parseado
            today: Fecha de hoy

        Returns:
            bool: True si el email es de hoy
        """
        try:
            # Intentar obtener fecha del header Date
            date_header = email_message.get('Date')
            if date_header:
                email_date = parsedate_to_datetime(date_header)
                if email_date:
                    # Comparar solo la fecha (sin hora) para manejar zonas horarias
                    return email_date.date() == today

            # Fallback: usar Received headers si Date no está disponible
            received_headers = email_message.get_all('Received')
            if received_headers:
                for received in received_headers:
                    # Buscar timestamp en el header Received
                    try:
                        # Los headers Received suelen terminar con "; fecha"
                        if ';' in received:
                            date_part = received.split(';')[-1].strip()
                            email_date = parsedate_to_datetime(date_part)
                            if email_date and email_date.date() == today:
                                return True
                    except:
                        continue

        except Exception as e:
            self._log(f"⚠️ Error verificando fecha del email: {e}")

        return False

    def _extract_search_content(self, email_message):
        """
        Extrae todo el contenido searcheable del email.

        Args:
            email_message: Mensaje de email parseado

        Returns:
            dict: Diccionario con contenido por campo
        """
        content = {
            'subject': '',
            'from': '',
            'body': ''
        }

        try:
            # Extraer y decodificar asunto
            subject = email_message.get('subject', '')
            if subject:
                content['subject'] = self._decode_header_robust(subject)

            # Extraer From
            from_header = email_message.get('from', '')
            if from_header:
                content['from'] = self._decode_header_robust(from_header)

            # Extraer cuerpo del mensaje
            content['body'] = self._extract_body_content(email_message)

        except Exception as e:
            self._log(f"⚠️ Error extrayendo contenido: {e}")

        return content

    def _decode_header_robust(self, header_value):
        """
        Decodifica headers de email de manera robusta.

        Args:
            header_value (str): Valor del header a decodificar

        Returns:
            str: Header decodificado
        """
        try:
            decoded_parts = decode_header(header_value)
            decoded_str = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            decoded_str += part.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            # Fallback a utf-8 con manejo de errores
                            decoded_str += part.decode('utf-8', errors='ignore')
                    else:
                        # Probar diferentes encodings comunes
                        for enc in ['utf-8', 'latin1', 'ascii']:
                            try:
                                decoded_str += part.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # Si todo falla, usar ignore
                            decoded_str += part.decode('utf-8', errors='ignore')
                else:
                    decoded_str += str(part)

            return decoded_str.strip()

        except Exception as e:
            self._log(f"⚠️ Error decodificando header: {e}")
            return str(header_value) if header_value else ""

    def _extract_body_content(self, email_message):
        """
        Extrae el contenido del cuerpo del email.

        Args:
            email_message: Mensaje de email parseado

        Returns:
            str: Contenido del cuerpo
        """
        body_content = ""

        try:
            if email_message.is_multipart():
                # Email multiparte
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type in ['text/plain', 'text/html']:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                try:
                                    body_content += payload.decode(charset, errors='ignore') + " "
                                except (UnicodeDecodeError, LookupError):
                                    body_content += payload.decode('utf-8', errors='ignore') + " "
                        except Exception:
                            continue
            else:
                # Email simple
                try:
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        charset = email_message.get_content_charset() or 'utf-8'
                        try:
                            body_content = payload.decode(charset, errors='ignore')
                        except (UnicodeDecodeError, LookupError):
                            body_content = payload.decode('utf-8', errors='ignore')
                except Exception:
                    pass

        except Exception as e:
            self._log(f"⚠️ Error extrayendo cuerpo: {e}")

        return body_content.strip()

    def _matches_criteria(self, search_content, pattern):
        """
        Verifica si el contenido coincide con el patrón de búsqueda.

        Args:
            search_content (dict): Contenido extraído del email
            pattern: Patrón regex compilado

        Returns:
            bool: True si hay coincidencia
        """
        try:
            # Buscar en todos los campos configurados
            for field in self.search_fields:
                content = search_content.get(field, '')
                if content and pattern.search(content):
                    return True
            return False
        except Exception:
            return False

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
                self._log("⚙️ Configuración SMTP cargada")
                return config
        except Exception as e:
            self._log(f"❌ Error cargando configuración SMTP: {e}")
        return None

    def _load_cache(self):
        """Carga la caché desde el archivo."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.search_cache = json.load(f)

                # Limpiar caché expirado
                self._clean_expired_cache()

                self._log(f"💾 Caché cargado: {len(self.search_cache)} entradas")
            except Exception as e:
                self._log(f"⚠️ Error al cargar caché: {e}")
                self.search_cache = {}
        else:
            self.search_cache = {}

    def _clean_expired_cache(self):
        """Limpia entradas expiradas del caché."""
        expired_keys = []
        for key, data in self.search_cache.items():
            if not self._is_cache_valid(data):
                expired_keys.append(key)

        for key in expired_keys:
            del self.search_cache[key]

        if expired_keys:
            self._log(f"🧹 Limpiado caché expirado: {len(expired_keys)} entradas")

    def _save_cache(self):
        """Guarda la caché en el archivo."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2, ensure_ascii=False)
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
        """Limpia toda la caché de búsquedas."""
        self.search_cache = {}
        try:
            if self.cache_file.exists():
                os.remove(self.cache_file)
            self._log("🧹 Caché de correos limpiado completamente")
        except Exception as e:
            self._log(f"⚠️ Error al limpiar caché: {e}")

    def get_cache_info(self):
        """
        Obtiene información sobre la caché actual.

        Returns:
            dict: Información de la caché
        """
        valid_entries = 0
        total_entries = len(self.search_cache)

        for data in self.search_cache.values():
            if self._is_cache_valid(data):
                valid_entries += 1

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_file": str(self.cache_file)
        }

    def force_refresh(self):
        """Fuerza una actualización eliminando toda la caché."""
        self.clear_cache()
        self._log("🔄 Forzada actualización: caché eliminado")