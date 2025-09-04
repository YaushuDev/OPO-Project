# gui/models/search_profile.py
"""
Modelo para representar un perfil de búsqueda de correos.
Contiene información sobre múltiples criterios de búsqueda (hasta 3) y resultados.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


class SearchProfile:
    """Representa un perfil de búsqueda de correos electrónicos con múltiples criterios."""

    def __init__(self, name, search_criteria, profile_id=None):
        """
        Inicializa un perfil de búsqueda.

        Args:
            name (str): Nombre del perfil
            search_criteria (str or list): Criterio(s) de búsqueda. Puede ser string único o lista de hasta 3
            profile_id (str, optional): ID único del perfil. Si no se proporciona, se genera uno.
        """
        self.profile_id = profile_id if profile_id else str(uuid.uuid4())
        self.name = name

        # Convertir criterios a lista si es necesario, manteniendo compatibilidad
        if isinstance(search_criteria, str):
            self.search_criteria = [search_criteria]
        elif isinstance(search_criteria, list):
            # Filtrar criterios vacíos y limitar a máximo 3
            self.search_criteria = [criteria.strip() for criteria in search_criteria if criteria.strip()][:3]
        else:
            self.search_criteria = []

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
            "search_criteria": self.search_criteria,  # Ahora es lista
            "found_emails": self.found_emails,
            "last_search": self.last_search.isoformat() if self.last_search else None
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crea una instancia de perfil a partir de un diccionario.
        Mantiene compatibilidad con formato antiguo (string) y nuevo (lista).

        Args:
            data (dict): Diccionario con los datos del perfil

        Returns:
            SearchProfile: Instancia de perfil
        """
        search_criteria = data.get("search_criteria", [])

        # Compatibilidad hacia atrás: si es string, convertir a lista
        if isinstance(search_criteria, str):
            search_criteria = [search_criteria]
        elif not isinstance(search_criteria, list):
            search_criteria = []

        profile = cls(
            name=data.get("name", ""),
            search_criteria=search_criteria,
            profile_id=data.get("profile_id")
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
            search_criteria (str or list): Nuevo(s) criterio(s) de búsqueda
        """
        self.name = name

        # Convertir y limpiar criterios
        if isinstance(search_criteria, str):
            self.search_criteria = [search_criteria.strip()] if search_criteria.strip() else []
        elif isinstance(search_criteria, list):
            self.search_criteria = [criteria.strip() for criteria in search_criteria if criteria.strip()][:3]
        else:
            self.search_criteria = []

    def update_search_results(self, found_emails):
        """
        Actualiza los resultados de búsqueda.

        Args:
            found_emails (int): Número de correos encontrados
        """
        self.found_emails = found_emails
        self.last_search = datetime.now()

    def get_criteria_display(self):
        """
        Retorna una representación legible de los criterios para mostrar en la interfaz.

        Returns:
            str: Criterios formateados para mostrar
        """
        if not self.search_criteria:
            return "Sin criterios"
        elif len(self.search_criteria) == 1:
            return self.search_criteria[0]
        else:
            return f"{len(self.search_criteria)} criterios: {', '.join(self.search_criteria[:2])}{'...' if len(self.search_criteria) > 2 else ''}"

    def has_valid_criteria(self):
        """
        Verifica si el perfil tiene al menos un criterio válido.

        Returns:
            bool: True si tiene criterios válidos
        """
        return len(self.search_criteria) > 0