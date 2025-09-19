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
import unicodedata
from pathlib import Path
from datetime import datetime, date, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from collections import defaultdict
from difflib import SequenceMatcher


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
        self.fuzzy_fields = {'subject', 'from'}  # Campos que permiten coincidencia difusa
        self.fuzzy_match_threshold = 0.75  # Umbral para coincidencias difusas
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

        sender_filters = []
        if hasattr(profile, 'sender_filters') and profile.sender_filters:
            sender_filters = [s for s in profile.sender_filters if isinstance(s, str) and s.strip()]

        if sender_filters:
            self._log(f"📮 Remitentes configurados: {len(sender_filters)}")
            for sender in sender_filters:
                self._log(f"  ↪ Remitente: {sender}")
        else:
            self._log("📮 Sin filtros de remitente específicos")

        start_time = datetime.now()

        try:
            # Cargar configuración SMTP
            smtp_config = self._load_smtp_config()
            if not smtp_config:
                self._log("❌ Error: No se encontró configuración SMTP")
                return 0

            # Generar clave de caché para toda la búsqueda
            cache_key = self._generate_cache_key(criterios, sender_filters)

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
            unique_emails = self._perform_enhanced_imap_search(smtp_config, criterios, sender_filters)

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
                cleaned = self._fix_text_encoding(criterio).strip()
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

    def _generate_cache_key(self, criterios, sender_filters=None):
        """
        Genera una clave única para el caché basada en los criterios y la fecha.

        Args:
            criterios (list): Lista de criterios de búsqueda
            sender_filters (list, optional): Lista de remitentes filtrados

        Returns:
            str: Clave de caché única
        """
        today_str = date.today().isoformat()
        criteria_str = "|".join(sorted([c.lower() for c in criterios]))
        sender_str = "|".join(sorted([s.lower() for s in sender_filters])) if sender_filters else ""
        combined = f"{today_str}:{criteria_str}:{sender_str}"
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

    def _perform_enhanced_imap_search(self, smtp_config, criterios, sender_filters):
        """
        Realiza búsqueda IMAP mejorada con múltiples criterios y deduplicación.

        Args:
            smtp_config (dict): Configuración SMTP/IMAP
            criterios (list): Lista de criterios de búsqueda
            sender_filters (list): Lista de remitentes filtrados

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
            unique_emails = self._analyze_messages(mail, message_ids, criterios, sender_filters)

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

    def _prepare_search_patterns(self, criterios):
        """Crea estructuras de patrones para coincidencias exactas y flexibles."""
        patterns = []

        for criterio in criterios:
            cleaned = self._fix_text_encoding(criterio)
            regex = re.compile(re.escape(cleaned), re.IGNORECASE | re.UNICODE)
            normalized = self._normalize_text(cleaned)
            tokens = self._tokenize(normalized)

            patterns.append({
                'original': cleaned,
                'regex': regex,
                'normalized': normalized,
                'tokens': tokens
            })

        return patterns

    def _normalize_text(self, text):
        """Normaliza texto eliminando acentos, signos y múltiples espacios."""
        if not text:
            return ""

        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fix_text_encoding(self, text):
        """Corrige secuencias mal decodificadas comunes en textos UTF-8."""
        if not text or not isinstance(text, str):
            return text

        suspicious_sequences = ('Ã', 'Â', 'Ð', 'Å', '¤')
        if not any(seq in text for seq in suspicious_sequences):
            return text

        try:
            fixed = text.encode('latin1').decode('utf-8')
            return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    def _tokenize(self, text):
        """Convierte el texto normalizado en un conjunto de tokens únicos."""
        if not text:
            return set()
        return set(text.split())
      
    def _analyze_messages(self, mail, message_ids, criterios, sender_filters):
        """
        Analiza mensajes para encontrar coincidencias con los criterios.

        Args:
            mail: Conexión IMAP
            message_ids: Lista de IDs de mensajes
            criterios: Lista de criterios de búsqueda
            sender_filters: Lista de remitentes filtrados

        Returns:
            set: Set de IDs únicos de correos que coinciden
        """
        unique_emails = set()
        today = date.today()

        # Crear patrones de búsqueda optimizados
        search_patterns = self._prepare_search_patterns(criterios)
        self._log(f"🎯 Patrones de búsqueda creados: {len(search_patterns)}")

        sender_patterns = self._prepare_search_patterns(sender_filters) if sender_filters else []
        if sender_patterns:
            self._log(f"✉️ Patrones de remitente activos: {len(sender_patterns)}")

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

                # Verificar coincidencias con cualquier criterio, remitente y combinación de título
                matched_criteria = set()
                sender_match_label = None

                if sender_patterns:
                    sender_match, sender_match_label = self._sender_matches(search_content, sender_patterns)
                    if not sender_match:
                        continue

                subject_match = self._subject_matches_all_keywords(
                    search_content,
                    search_patterns
                )

                for pattern_info in search_patterns:
                    criterio = pattern_info['original']
                    if criterio in matched_criteria:
                        continue
                    if self._matches_criteria(search_content, pattern_info):
                        matches_by_criteria[criterio] += 1
                        matched_criteria.add(criterio)

                if subject_match:
                    matches_by_criteria['subject_combination'] += 1

                message_matches = bool(matched_criteria or subject_match)

                if sender_match_label:
                    matches_by_criteria['sender_filter_total'] += 1
                    matches_by_criteria[f"sender:{sender_match_label}"] += 1
                    if not message_matches:
                        message_matches = True

                if message_matches:
                    unique_emails.add(msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id))

                processed += 1
                if processed % 50 == 0:
                    self._log(f"⏳ Procesados {processed}/{len(message_ids)} correos...")

            except Exception as e:
                self._log(f"⚠️ Error procesando mensaje {msg_id}: {e}")
                continue

        # Log de estadísticas por criterio
        if matches_by_criteria:
            self._log("📈 Estadísticas por criterio:")
            for criterio, count in matches_by_criteria.items():
                if criterio == 'subject_combination':
                    label = 'Todos los criterios presentes en el asunto'
                elif criterio == 'sender_filter_total':
                    label = 'Remitentes filtrados (total)'
                elif criterio.startswith('sender:'):
                    label = f"Remitente coincidió: {criterio.split(':', 1)[1]}"
                else:
                    label = criterio
                self._log(f"  📌 '{label}': {count} coincidencias")

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

        # Preparar variantes normalizadas y tokens para coincidencias flexibles
        for field in self.search_fields:
            value = content.get(field, '')
            normalized = self._normalize_text(value)
            content[f"{field}_normalized"] = normalized
            content[f"{field}_tokens"] = self._tokenize(normalized)

        combined = " ".join(content.get(field, '') for field in self.search_fields if content.get(field))
        content['combined_text'] = combined.strip()
        content['combined_normalized'] = self._normalize_text(combined)
        content['combined_tokens'] = self._tokenize(content['combined_normalized'])

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

            decoded_str = self._fix_text_encoding(decoded_str)
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

        return self._fix_text_encoding(body_content.strip())

    def _pattern_matches_field(self, pattern, field_value, normalized_field, field_tokens, allow_fuzzy=False):
        """Evalúa si un campo del correo coincide con un patrón determinado."""
        if not field_value and not normalized_field:
            return False

        regex = pattern.get('regex')
        if field_value and regex and regex.search(field_value):
            return True

        normalized_criterio = pattern.get('normalized')
        tokens = pattern.get('tokens')

        if normalized_field:
            if normalized_criterio and normalized_criterio in normalized_field:
                return True
            if tokens and field_tokens and tokens.issubset(field_tokens):
                return True
            if allow_fuzzy and normalized_criterio and self._is_fuzzy_match(normalized_field, normalized_criterio):
                return True

        return False

    def _matches_criteria(self, search_content, pattern):
        """Verifica si cualquier campo del correo coincide con el patrón proporcionado."""
        try:
            for field in self.search_fields:
                if self._pattern_matches_field(
                    pattern,
                    search_content.get(field, ''),
                    search_content.get(f"{field}_normalized"),
                    search_content.get(f"{field}_tokens"),
                    allow_fuzzy=field in self.fuzzy_fields
                ):
                    return True

            return self._pattern_matches_field(
                pattern,
                search_content.get('combined_text', ''),
                search_content.get('combined_normalized'),
                search_content.get('combined_tokens'),
                allow_fuzzy=False
            )
        except Exception:
            return False

    def _subject_matches_all_keywords(self, search_content, patterns):
        """Comprueba si el asunto contiene todos los patrones definidos."""
        if len(patterns) < 2:
            return False

        subject_value = search_content.get('subject', '')
        subject_normalized = search_content.get('subject_normalized')
        subject_tokens = search_content.get('subject_tokens')

        if not subject_value and not subject_normalized:
            return False

        for pattern in patterns:
            if not self._pattern_matches_field(
                pattern,
                subject_value,
                subject_normalized,
                subject_tokens,
                allow_fuzzy=True
            ):
                return False

        return True

    def _sender_matches(self, search_content, sender_patterns):
        """Verifica si el remitente coincide con alguno de los patrones configurados."""
        if not sender_patterns:
            return (False, None)

        sender_value = search_content.get('from', '')
        sender_normalized = search_content.get('from_normalized')
        sender_tokens = search_content.get('from_tokens')

        if not sender_value and not sender_normalized:
            return (False, None)

        for pattern in sender_patterns:
            if self._pattern_matches_field(
                pattern,
                sender_value,
                sender_normalized,
                sender_tokens,
                allow_fuzzy=True
            ):
                return True, pattern.get('original')

        return (False, None)

    def _is_fuzzy_match(self, normalized_field, normalized_criterio):
        """Evalúa coincidencias parciales para títulos similares."""
        if not normalized_field or not normalized_criterio:
            return False

        if len(normalized_criterio) <= 4:
            return normalized_criterio in normalized_field

        matcher = SequenceMatcher(None, normalized_criterio, normalized_field)
        if matcher.ratio() >= self.fuzzy_match_threshold:
            return True

        longest = matcher.find_longest_match(0, len(normalized_criterio), 0, len(normalized_field))
        if longest.size == 0:
            return False

        partial_ratio = longest.size / len(normalized_criterio)
        return partial_ratio >= self.fuzzy_match_threshold

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