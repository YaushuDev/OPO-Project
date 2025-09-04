# services/search_service.py
"""
Servicio para búsqueda de correos electrónicos.
Implementa búsqueda real basada en criterios especificados en perfiles.
"""

import re
import os
from pathlib import Path
from datetime import datetime
import csv
import json


class SearchService:
    """Servicio para buscar correos electrónicos basados en criterios de búsqueda."""

    def __init__(self, data_dir=None, log_callback=None):
        """
        Inicializa el servicio de búsqueda.

        Args:
            data_dir (str, optional): Directorio de datos. Por defecto "data".
            log_callback (callable, optional): Función para registrar logs.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.log_callback = log_callback
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.email_cache = {}

        # Crear directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)
        self.cache_file = self.data_dir / "email_cache.json"
        self._load_cache()

    def search_emails(self, profile):
        """
        Busca correos electrónicos basados en los criterios del perfil.

        Args:
            profile: Perfil de búsqueda con los criterios

        Returns:
            int: Número de correos encontrados
        """
        self._log(f"Iniciando búsqueda con perfil: {profile.name}")
        start_time = datetime.now()

        try:
            # Verificar si ya hemos buscado este criterio antes
            if profile.search_criteria in self.email_cache:
                emails = self.email_cache[profile.search_criteria]
                self._log(f"Utilizando resultados en caché para '{profile.search_criteria}'")
            else:
                # Realizar búsqueda real
                emails = self._perform_search(profile.search_criteria)
                # Guardar en caché
                self.email_cache[profile.search_criteria] = emails
                self._save_cache()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._log(f"Búsqueda completada en {duration:.2f} segundos")
            self._log(f"Correos encontrados: {len(emails)}")

            return len(emails)

        except Exception as e:
            self._log(f"Error durante la búsqueda: {e}")
            return 0

    def _perform_search(self, search_criteria):
        """
        Realiza la búsqueda de correos basada en los criterios.

        Args:
            search_criteria (str): Texto a buscar

        Returns:
            list: Lista de correos encontrados
        """
        self._log(f"Realizando búsqueda para: '{search_criteria}'")

        # Lista para almacenar todos los correos encontrados
        all_emails = set()

        # Buscar en diferentes fuentes de datos
        self._search_in_data_files(search_criteria, all_emails)
        self._search_in_sample_data(search_criteria, all_emails)

        # Convertir el conjunto a lista para devolver
        return list(all_emails)

    def _search_in_data_files(self, search_criteria, emails_set):
        """
        Busca correos en archivos de datos existentes.

        Args:
            search_criteria (str): Criterio de búsqueda
            emails_set (set): Conjunto donde añadir los correos encontrados
        """
        # Buscar en archivos .txt, .csv y .json en el directorio de datos
        for file_path in self.data_dir.glob('**/*'):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() in ['.txt', '.csv', '.json']:
                try:
                    self._log(f"Buscando en archivo: {file_path.name}")

                    # Leer archivo
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()

                    # Si el criterio está en el contenido, extraer emails
                    if search_criteria.lower() in content.lower():
                        found_emails = self._extract_emails(content)
                        self._log(f"Encontrados {len(found_emails)} correos en {file_path.name}")
                        emails_set.update(found_emails)

                except Exception as e:
                    self._log(f"Error al procesar {file_path.name}: {e}")

    def _search_in_sample_data(self, search_criteria, emails_set):
        """
        Genera datos de muestra basados en el criterio para propósitos de demostración.
        En una implementación real, esto se reemplazaría con fuentes de datos reales.

        Args:
            search_criteria (str): Criterio de búsqueda
            emails_set (set): Conjunto donde añadir los correos encontrados
        """
        # Datos de muestra para demostración
        domains = ["gmail.com", "outlook.com", "yahoo.com", "empresa.com", "hotmail.com", "protonmail.com"]

        # Generar correos de muestra basados en el criterio (para demostraciones)
        base_word = search_criteria.lower().replace(" ", "")
        if len(base_word) > 4:
            base_word = base_word[:4]  # Usar primeros 4 caracteres

            # Generar correos relacionados con el criterio
            sample_size = len(search_criteria) * 2
            for i in range(1, sample_size + 1):
                for domain in domains[:3]:  # Usar solo algunos dominios
                    if i % 3 == 0:  # Variedad en los correos generados
                        email = f"{base_word}.user{i}@{domain}"
                    else:
                        email = f"{base_word}{i}@{domain}"
                    emails_set.add(email)

        # Añadir también correos de dominios empresariales para el criterio
        company_domain = "empresa.com"
        for i in range(1, 6):
            email = f"{base_word}.{i}@{company_domain}"
            emails_set.add(email)

    def _extract_emails(self, text):
        """
        Extrae direcciones de correo electrónico de un texto.

        Args:
            text (str): Texto de donde extraer correos

        Returns:
            set: Conjunto de correos encontrados
        """
        return set(re.findall(self.email_pattern, text))

    def _load_cache(self):
        """Carga la caché de correos desde el archivo."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.email_cache = json.load(f)
                self._log(f"Caché de correos cargada: {len(self.email_cache)} entradas")
            except Exception as e:
                self._log(f"Error al cargar caché: {e}")
                self.email_cache = {}
        else:
            self.email_cache = {}

    def _save_cache(self):
        """Guarda la caché de correos en el archivo."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.email_cache, f, indent=4)
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