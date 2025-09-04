# services/search_service.py
"""
Servicio para búsqueda de correos electrónicos en bandejas de entrada reales.
Implementa búsqueda IMAP en correos del día actual basada en criterios de asunto.
"""

import imaplib
import email
import ssl
import json
import os
from pathlib import Path
from datetime import datetime, date
from email.header import decode_header


class SearchService:
    """Servicio para buscar correos electrónicos reales vía IMAP."""

    # Mapeo de servidores SMTP a IMAP
    IMAP_SERVERS = {
        "smtp.gmail.com": {"server": "imap.gmail.com", "port": 993},
        "smtp-mail.outlook.com": {"server": "outlook.office365.com", "port": 993}
    }

    def __init__(self, data_dir=None, log_callback=None):
        """
        Inicializa el servicio de búsqueda IMAP.

        Args:
            data_dir (str, optional): Directorio de datos para caché. Por defecto "data".
            log_callback (callable, optional): Función para registrar logs.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.log_callback = log_callback
        self.smtp_config_file = Path("config") / "smtp_config.json"

        # Crear directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)

        # Sistema de caché por día
        self.cache_file = self.data_dir / "daily_email_cache.json"
        self.email_cache = {}
        self._load_cache()

    def search_emails(self, profile):
        """
        Busca correos electrónicos del día actual basados en los criterios del perfil.

        Args:
            profile: Perfil de búsqueda con los criterios

        Returns:
            int: Número de correos encontrados
        """
        self._log(f"Iniciando búsqueda con perfil: {profile.name}")
        start_time = datetime.now()

        try:
            # Crear clave de caché única para hoy y este criterio
            today_str = date.today().isoformat()
            cache_key = f"{today_str}_{profile.search_criteria}"

            # Verificar caché
            if cache_key in self.email_cache:
                count = self.email_cache[cache_key]
                self._log(f"Utilizando resultados en caché para '{profile.search_criteria}': {count} correos")
                return count

            # Cargar configuración SMTP
            smtp_config = self._load_smtp_config()
            if not smtp_config:
                self._log("Error: No se encontró configuración SMTP")
                return 0

            # Realizar búsqueda IMAP real
            found_count = self._perform_imap_search(smtp_config, profile.search_criteria)

            # Guardar en caché
            self.email_cache[cache_key] = found_count
            self._save_cache()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._log(f"Búsqueda completada en {duration:.2f} segundos")
            self._log(f"Correos encontrados: {found_count}")

            return found_count

        except Exception as e:
            self._log(f"Error durante la búsqueda: {e}")
            return 0

    def _perform_imap_search(self, smtp_config, search_criteria):
        """
        Realiza la búsqueda IMAP en el correo configurado.

        Args:
            smtp_config (dict): Configuración SMTP/IMAP
            search_criteria (str): Criterio de búsqueda para el asunto

        Returns:
            int: Número de correos que coinciden
        """
        mail = None
        try:
            # Obtener configuración IMAP del servidor SMTP
            smtp_server = smtp_config.get('server')
            imap_config = self.IMAP_SERVERS.get(smtp_server)

            if not imap_config:
                self._log(f"Servidor IMAP no soportado: {smtp_server}")
                return 0

            self._log(f"Conectando a {imap_config['server']}...")

            # Crear conexión IMAP con SSL
            mail = imaplib.IMAP4_SSL(imap_config['server'], imap_config['port'])

            # Autenticar con las mismas credenciales SMTP
            mail.login(smtp_config['username'], smtp_config['password'])
            self._log("Autenticación IMAP exitosa")

            # Seleccionar bandeja de entrada
            mail.select('inbox')
            self._log("Bandeja de entrada seleccionada")

            # Buscar correos del día actual
            today = date.today().strftime("%d-%b-%Y")
            search_criteria_imap = f'(ON "{today}")'

            self._log(f"Buscando correos del {today}...")
            status, messages = mail.search(None, search_criteria_imap)

            if status != 'OK':
                self._log("Error al buscar correos")
                return 0

            message_ids = messages[0].split()
            self._log(f"Encontrados {len(message_ids)} correos del día actual")

            if not message_ids:
                return 0

            # Filtrar por criterio de búsqueda en el asunto
            matching_count = 0
            search_term = search_criteria.lower()

            for msg_id in message_ids:
                try:
                    # Obtener el correo
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parsear el mensaje
                    email_message = email.message_from_bytes(msg_data[0][1])
                    subject = email_message['subject']

                    if subject:
                        # Decodificar el asunto si está codificado
                        decoded_subject = self._decode_subject(subject)

                        # Verificar si el criterio de búsqueda está en el asunto
                        if search_term in decoded_subject.lower():
                            matching_count += 1
                            self._log(f"Match encontrado: {decoded_subject[:50]}...")

                except Exception as e:
                    self._log(f"Error procesando mensaje {msg_id}: {e}")
                    continue

            self._log(f"Total de correos que coinciden con '{search_criteria}': {matching_count}")
            return matching_count

        except imaplib.IMAP4.error as e:
            self._log(f"Error IMAP: {e}")
            return 0
        except Exception as e:
            self._log(f"Error inesperado en búsqueda IMAP: {e}")
            return 0
        finally:
            # Cerrar conexión IMAP
            if mail:
                try:
                    mail.close()
                    mail.logout()
                    self._log("Conexión IMAP cerrada")
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
            self._log(f"Error decodificando asunto: {e}")
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
                self._log("Configuración SMTP cargada para búsqueda IMAP")
                return config
        except Exception as e:
            self._log(f"Error cargando configuración SMTP: {e}")
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

                self._log(f"Caché de correos cargada: {len(self.email_cache)} entradas del día actual")
            except Exception as e:
                self._log(f"Error al cargar caché: {e}")
                self.email_cache = {}
        else:
            self.email_cache = {}

    def _save_cache(self):
        """Guarda la caché de correos en el archivo."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.email_cache, f, indent=4, ensure_ascii=False)
            self._log("Caché de correos guardada")
        except Exception as e:
            self._log(f"Error al guardar caché: {e}")

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
            self._log("Caché de correos limpiada")
        except Exception as e:
            self._log(f"Error al limpiar caché: {e}")

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
            "cache_date": today_str
        }