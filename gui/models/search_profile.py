# gui/models/search_profile.py
"""
Modelo para representar un perfil de búsqueda de correos.
Contiene información sobre criterios de búsqueda y resultados.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


class SearchProfile:
    """Representa un perfil de búsqueda de correos electrónicos."""

    def __init__(self, name, search_criteria, profile_id=None):
        """
        Inicializa un perfil de búsqueda.

        Args:
            name (str): Nombre del perfil
            search_criteria (str): Criterio de búsqueda (título o texto similar)
            profile_id (str, optional): ID único del perfil. Si no se proporciona, se genera uno.
        """
        self.profile_id = profile_id if profile_id else str(uuid.uuid4())
        self.name = name
        self.search_criteria = search_criteria
        self.found_emails = 0
        self.last_search = None

    def to_dict(self):
        """
        Convierte el perfil a un diccionario para serialización.

        Returns:
            dict: Diccionario con los datos del perfil
        """
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "search_criteria": self.search_criteria,
            "found_emails": self.found_emails,
            "last_search": self.last_search.isoformat() if self.last_search else None
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crea una instancia de perfil a partir de un diccionario.

        Args:
            data (dict): Diccionario con los datos del perfil

        Returns:
            SearchProfile: Instancia de perfil
        """
        profile = cls(
            name=data["name"],
            search_criteria=data["search_criteria"],
            profile_id=data["profile_id"]
        )
        profile.found_emails = data.get("found_emails", 0)

        # Convertir ISO date string a datetime
        if data.get("last_search"):
            try:
                profile.last_search = datetime.fromisoformat(data["last_search"])
            except (ValueError, TypeError):
                profile.last_search = None

        return profile

    def update(self, name, search_criteria):
        """
        Actualiza los datos del perfil.

        Args:
            name (str): Nuevo nombre
            search_criteria (str): Nuevo criterio de búsqueda
        """
        self.name = name
        self.search_criteria = search_criteria

    def update_search_results(self, found_emails):
        """
        Actualiza los resultados de búsqueda.

        Args:
            found_emails (int): Número de correos encontrados
        """
        self.found_emails = found_emails
        self.last_search = datetime.now()