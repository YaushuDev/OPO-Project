# gui/models/search_profile.py
"""
Modelo para representar un perfil de búsqueda de correos.
Contiene información sobre múltiples criterios de búsqueda (hasta 3), resultados,
y seguimiento de ejecuciones óptimas con porcentaje de éxito.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


class SearchProfile:
    """Representa un perfil de búsqueda de correos electrónicos con múltiples criterios y seguimiento óptimo."""

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

        # Campos originales
        self.found_emails = 0  # Ahora representa "Cantidad de ejecuciones"
        self.last_search = None

        # Nuevos campos para seguimiento óptimo
        self.optimal_executions = 0  # Cantidad de ejecuciones óptimas
        self.track_optimal = False  # Habilitar/deshabilitar seguimiento óptimo

    def to_dict(self):
        """
        Convierte el perfil a un diccionario para serialización.

        Returns:
            dict: Diccionario con los datos del perfil incluyendo campos nuevos
        """
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "search_criteria": self.search_criteria,
            "found_emails": self.found_emails,
            "last_search": self.last_search.isoformat() if self.last_search else None,
            # Nuevos campos
            "optimal_executions": self.optimal_executions,
            "track_optimal": self.track_optimal
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crea una instancia de perfil a partir de un diccionario.
        Mantiene compatibilidad con formato antiguo (string) y nuevo (lista).
        Incluye compatibilidad hacia atrás para perfiles sin campos nuevos.

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

        # Cargar nuevos campos con compatibilidad hacia atrás
        profile.optimal_executions = data.get("optimal_executions", 0)
        profile.track_optimal = data.get("track_optimal", False)

        return profile

    def update(self, name, search_criteria, optimal_executions=None, track_optimal=None):
        """
        Actualiza los datos del perfil incluyendo campos de seguimiento óptimo.

        Args:
            name (str): Nuevo nombre
            search_criteria (str or list): Nuevo(s) criterio(s) de búsqueda
            optimal_executions (int, optional): Cantidad de ejecuciones óptimas
            track_optimal (bool, optional): Habilitar seguimiento óptimo
        """
        self.name = name

        # Convertir y limpiar criterios
        if isinstance(search_criteria, str):
            self.search_criteria = [search_criteria.strip()] if search_criteria.strip() else []
        elif isinstance(search_criteria, list):
            self.search_criteria = [criteria.strip() for criteria in search_criteria if criteria.strip()][:3]
        else:
            self.search_criteria = []

        # Actualizar campos de seguimiento óptimo si se proporcionan
        if optimal_executions is not None:
            self.optimal_executions = max(0, int(optimal_executions))

        if track_optimal is not None:
            self.track_optimal = track_optimal

    def update_search_results(self, found_emails):
        """
        Actualiza los resultados de búsqueda (cantidad de ejecuciones).

        Args:
            found_emails (int): Número de correos encontrados (cantidad de ejecuciones)
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

    def get_success_percentage(self):
        """
        Calcula el porcentaje de éxito basado en ejecuciones óptimas.

        Returns:
            float: Porcentaje de éxito (0-100+) o None si no está habilitado el seguimiento
        """
        if not self.track_optimal or self.optimal_executions <= 0:
            return None

        return round((self.found_emails / self.optimal_executions) * 100, 1)

    def is_success_optimal(self):
        """
        Verifica si el perfil ha alcanzado el éxito óptimo (≥100%).

        Returns:
            bool: True si el porcentaje de éxito es >= 100%, False si no está habilitado o es menor
        """
        percentage = self.get_success_percentage()
        return percentage is not None and percentage >= 100.0

    def get_optimal_display(self):
        """
        Retorna una representación de las ejecuciones óptimas para mostrar.

        Returns:
            str: Texto formateado para mostrar ejecuciones óptimas
        """
        if not self.track_optimal:
            return "Deshabilitado"

        if self.optimal_executions <= 0:
            return "No configurado"

        return str(self.optimal_executions)

    def get_success_display(self):
        """
        Retorna una representación del porcentaje de éxito para mostrar.

        Returns:
            str: Texto formateado para mostrar porcentaje de éxito
        """
        percentage = self.get_success_percentage()

        if percentage is None:
            return "N/A"

        return f"{percentage}%"