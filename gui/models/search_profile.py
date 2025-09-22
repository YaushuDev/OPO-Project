# search_profile.py
"""
Modelo optimizado para representar un perfil de búsqueda de correos.
Contiene información sobre múltiples criterios de búsqueda (hasta 3), resultados,
seguimiento de ejecuciones óptimas con porcentaje de éxito y tipo de bot (Automático/Manual/Offline).
Incluye validaciones mejoradas y métodos de utilidad optimizados.
"""

import json
import uuid
import re
from datetime import datetime


class SearchProfile:
    """Representa un perfil de búsqueda de correos electrónicos con criterios múltiples optimizados."""

    # Constantes de configuración
    MAX_CRITERIA = 3
    MIN_CRITERIA_LENGTH = 2
    MAX_CRITERIA_LENGTH = 100
    BOT_TYPES = ["automatico", "manual", "offline"]
    RESPONSABLE_MAX_LENGTH = 100
    TEXT_FIELD_MAX_LENGTH = 200

    def __init__(self, name, search_criteria, sender_filters=None, responsable=None, profile_id=None,
                 last_update_text=None, delivery_date_text=None):
        """
        Inicializa un perfil de búsqueda con validaciones mejoradas.

        Args:
            name (str): Nombre del perfil
            search_criteria (str or list): Criterio(s) de búsqueda. Puede ser string único o lista de hasta 3
            sender_filters (str or list, optional): Remitentes sugeridos para filtrar resultados
            responsable (str, optional): Responsable asociado al perfil
            profile_id (str, optional): ID único del perfil. Si no se proporciona, se genera uno.
        """
        self.profile_id = profile_id if profile_id else str(uuid.uuid4())
        self.name = self._validate_name(name)

        # Procesar y validar criterios
        self.search_criteria = self._process_criteria(search_criteria)

        # Filtros opcionales por remitente
        self.sender_filters = self._process_sender_filters(sender_filters)

        # Responsable opcional del perfil
        self.responsable = self._process_responsable(responsable)

        # Campos de seguimiento manual adicionales
        self.last_update_text = self._process_optional_text(last_update_text)
        self.delivery_date_text = self._process_optional_text(delivery_date_text)

        # Campos originales
        self.found_emails = 0  # Cantidad de ejecuciones encontradas
        self.last_search = None

        # Campos para seguimiento óptimo
        self.optimal_executions = 0  # Cantidad de ejecuciones óptimas esperadas
        self.track_optimal = False  # Habilitar/deshabilitar seguimiento óptimo

        # Campo para tipo de bot
        self.bot_type = "manual"  # Valor por defecto

        # Campos de metadatos (nuevos)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.search_count = 0  # Número de veces que se ha ejecutado

    def _validate_name(self, name):
        """
        Valida y limpia el nombre del perfil.

        Args:
            name (str): Nombre a validar

        Returns:
            str: Nombre validado

        Raises:
            ValueError: Si el nombre no es válido
        """
        if not isinstance(name, str):
            raise ValueError("El nombre debe ser una cadena de texto")

        cleaned_name = name.strip()

        if not cleaned_name:
            raise ValueError("El nombre del perfil no puede estar vacío")

        if len(cleaned_name) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")

        if len(cleaned_name) > 50:
            raise ValueError("El nombre no puede tener más de 50 caracteres")

        # Eliminar caracteres especiales problemáticos
        cleaned_name = re.sub(r'[<>:"/\\|?*]', '', cleaned_name)

        return cleaned_name

    def _process_criteria(self, search_criteria):
        """
        Procesa y valida los criterios de búsqueda.

        Args:
            search_criteria (str or list): Criterios a procesar

        Returns:
            list: Lista de criterios procesados y validados

        Raises:
            ValueError: Si los criterios no son válidos
        """
        if isinstance(search_criteria, str):
            criteria_list = [search_criteria]
        elif isinstance(search_criteria, list):
            criteria_list = search_criteria
        else:
            raise ValueError("Los criterios deben ser string o lista")

        # Procesar y validar cada criterio
        processed_criteria = []
        seen_criteria = set()

        for criterio in criteria_list:
            if not isinstance(criterio, str):
                continue

            # Limpiar criterio
            cleaned = self._clean_criteria(criterio)

            if self._validate_criteria(cleaned):
                # Evitar duplicados (case-insensitive)
                criterio_lower = cleaned.lower()
                if criterio_lower not in seen_criteria:
                    seen_criteria.add(criterio_lower)
                    processed_criteria.append(cleaned)

                    # Limitar a máximo de criterios
                    if len(processed_criteria) >= self.MAX_CRITERIA:
                        break

        if not processed_criteria:
            raise ValueError("Debe proporcionar al menos un criterio de búsqueda válido")

        return processed_criteria

    def _process_sender_filters(self, sender_filters):
        """Procesa y normaliza los filtros de remitente opcionales."""
        if not sender_filters:
            return []

        if isinstance(sender_filters, str):
            raw_filters = re.split(r'[\n,;]+', sender_filters)
        elif isinstance(sender_filters, (list, tuple, set)):
            raw_filters = sender_filters
        else:
            return []

        processed_filters = []
        seen = set()

        for sender in raw_filters:
            if not isinstance(sender, str):
                continue

            cleaned = ' '.join(sender.split()).strip()
            if not cleaned:
                continue

            sender_key = cleaned.lower()
            if sender_key not in seen:
                seen.add(sender_key)
                processed_filters.append(cleaned)

        return processed_filters

    def _process_responsable(self, responsable):
        """Normaliza el responsable asociado al perfil."""
        if responsable is None:
            return ""

        if not isinstance(responsable, str):
            raise ValueError("El responsable debe ser una cadena de texto")

        cleaned = ' '.join(responsable.split()).strip()

        if len(cleaned) > self.RESPONSABLE_MAX_LENGTH:
            cleaned = cleaned[:self.RESPONSABLE_MAX_LENGTH]

        return cleaned

    def _process_optional_text(self, value):
        """Normaliza campos de texto opcionales."""
        if value is None:
            return ""

        if not isinstance(value, str):
            value = str(value)

        cleaned = value.strip()

        if len(cleaned) > self.TEXT_FIELD_MAX_LENGTH:
            cleaned = cleaned[:self.TEXT_FIELD_MAX_LENGTH]

        return cleaned

    def _clean_criteria(self, criterio):
        """
        Limpia un criterio de búsqueda.

        Args:
            criterio (str): Criterio a limpiar

        Returns:
            str: Criterio limpio
        """
        # Eliminar espacios extras
        cleaned = ' '.join(criterio.split())

        # Eliminar caracteres de control
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32)

        return cleaned.strip()

    def _validate_criteria(self, criterio):
        """
        Valida un criterio individual.

        Args:
            criterio (str): Criterio a validar

        Returns:
            bool: True si el criterio es válido
        """
        if not criterio:
            return False

        if len(criterio) < self.MIN_CRITERIA_LENGTH:
            return False

        if len(criterio) > self.MAX_CRITERIA_LENGTH:
            return False

        # Verificar que no sea solo espacios o caracteres especiales
        if not re.search(r'[a-zA-Z0-9]', criterio):
            return False

        return True

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
            "sender_filters": self.sender_filters,
            "responsable": self.responsable,
            "found_emails": self.found_emails,
            "last_search": self.last_search.isoformat() if self.last_search else None,
            # Campos de seguimiento óptimo
            "optimal_executions": self.optimal_executions,
            "track_optimal": self.track_optimal,
            # Campo de tipo de bot
            "bot_type": self.bot_type,
            # Metadatos
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "search_count": self.search_count,
            "last_update_text": self.last_update_text,
            "delivery_date_text": self.delivery_date_text
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crea una instancia de perfil a partir de un diccionario.
        Mantiene compatibilidad con formato antiguo y maneja errores gracefully.

        Args:
            data (dict): Diccionario con los datos del perfil

        Returns:
            SearchProfile: Instancia de perfil

        Raises:
            ValueError: Si los datos no son válidos para crear un perfil
        """
        try:
            search_criteria = data.get("search_criteria", [])

            # Compatibilidad hacia atrás: si es string, convertir a lista
            if isinstance(search_criteria, str):
                search_criteria = [search_criteria]
            elif not isinstance(search_criteria, list):
                search_criteria = []

            sender_filters = data.get("sender_filters")
            if not sender_filters and data.get("sender_filter"):
                sender_filters = data.get("sender_filter")

            last_update_text = data.get("last_update_text")
            if not last_update_text:
                last_update_text = data.get("ultima_actualizacion")

            delivery_date_text = data.get("delivery_date_text")
            if not delivery_date_text:
                delivery_date_text = data.get("fecha_de_entrega") or data.get("fecha_entrega")

            profile = cls(
                name=data.get("name", "Perfil sin nombre"),
                search_criteria=search_criteria,
                sender_filters=sender_filters,
                responsable=data.get("responsable"),
                profile_id=data.get("profile_id"),
                last_update_text=last_update_text,
                delivery_date_text=delivery_date_text
            )

            profile.found_emails = max(0, int(data.get("found_emails", 0)))

            # Convertir ISO date string a datetime
            if data.get("last_search"):
                try:
                    profile.last_search = datetime.fromisoformat(data["last_search"])
                except (ValueError, TypeError):
                    profile.last_search = None

            # Cargar campos de seguimiento óptimo con validación
            profile.optimal_executions = max(0, int(data.get("optimal_executions", 0)))
            profile.track_optimal = bool(data.get("track_optimal", False))

            # Cargar tipo de bot con validación
            bot_type = data.get("bot_type", "manual")
            if bot_type in cls.BOT_TYPES:
                profile.bot_type = bot_type
            else:
                profile.bot_type = "manual"  # Fallback seguro

            # Cargar metadatos
            if data.get("created_at"):
                try:
                    profile.created_at = datetime.fromisoformat(data["created_at"])
                except (ValueError, TypeError):
                    profile.created_at = datetime.now()

            if data.get("updated_at"):
                try:
                    profile.updated_at = datetime.fromisoformat(data["updated_at"])
                except (ValueError, TypeError):
                    profile.updated_at = datetime.now()

            profile.search_count = max(0, int(data.get("search_count", 0)))

            # Asegurar normalización de campos de texto opcionales
            profile.last_update_text = profile._process_optional_text(
                getattr(profile, "last_update_text", "")
            )
            profile.delivery_date_text = profile._process_optional_text(
                getattr(profile, "delivery_date_text", "")
            )

            return profile

        except Exception as e:
            raise ValueError(f"Error al crear perfil desde datos: {e}")

    def update(self, name, search_criteria, optimal_executions=None, track_optimal=None,
               bot_type=None, sender_filters=None, responsable=None,
               last_update_text=None, delivery_date_text=None):
        """
        Actualiza los datos del perfil con validaciones mejoradas.

        Args:
            name (str): Nuevo nombre
            search_criteria (str or list): Nuevo(s) criterio(s) de búsqueda
            optimal_executions (int, optional): Cantidad de ejecuciones óptimas
            track_optimal (bool, optional): Habilitar seguimiento óptimo
            bot_type (str, optional): Tipo de bot ("automatico", "manual" u "offline")
            sender_filters (str or list, optional): Remitentes filtrados
            responsable (str, optional): Responsable del perfil
            last_update_text (str, optional): Texto manual de última actualización
            delivery_date_text (str, optional): Texto manual de fecha de entrega
        """
        # Actualizar nombre con validación
        self.name = self._validate_name(name)

        # Actualizar criterios con validación
        self.search_criteria = self._process_criteria(search_criteria)

        if sender_filters is not None:
            self.sender_filters = self._process_sender_filters(sender_filters)

        if responsable is not None:
            self.responsable = self._process_responsable(responsable)

        if last_update_text is not None:
            self.last_update_text = self._process_optional_text(last_update_text)

        if delivery_date_text is not None:
            self.delivery_date_text = self._process_optional_text(delivery_date_text)

        # Actualizar campos de seguimiento óptimo si se proporcionan
        if optimal_executions is not None:
            self.optimal_executions = max(0, int(optimal_executions))

        if track_optimal is not None:
            self.track_optimal = bool(track_optimal)

        # Actualizar tipo de bot con validación
        if bot_type is not None and bot_type in self.BOT_TYPES:
            self.bot_type = bot_type

        # Actualizar timestamp
        self.updated_at = datetime.now()

    def get_sender_filters(self):
        """Retorna la lista de filtros de remitente configurados."""
        return self.sender_filters.copy()

    def has_sender_filters(self):
        """Indica si el perfil tiene filtros de remitente configurados."""
        return bool(self.sender_filters)

    def get_sender_display(self):
        """Retorna representación legible de los remitentes filtrados."""
        if not self.sender_filters:
            return "➖ Sin filtro"
        if len(self.sender_filters) == 1:
            return f"✉️ {self.sender_filters[0]}"
        preview = ", ".join(self.sender_filters[:2])
        suffix = "..." if len(self.sender_filters) > 2 else ""
        return f"✉️ {len(self.sender_filters)} remitentes: {preview}{suffix}"

    def has_responsable(self):
        """Indica si el perfil tiene un responsable asignado."""
        return bool(self.responsable)

    def get_responsable_display(self):
        """Retorna una representación legible del responsable."""
        return self.responsable if self.responsable else "➖ Sin responsable"

    def has_last_update_text(self):
        """Indica si el perfil tiene texto de última actualización."""
        return bool(self.last_update_text)

    def get_last_update_display(self):
        """Retorna una representación legible de la última actualización manual."""
        return self.last_update_text if self.last_update_text else "—"

    def has_delivery_date_text(self):
        """Indica si el perfil tiene texto de fecha de entrega."""
        return bool(self.delivery_date_text)

    def get_delivery_date_display(self):
        """Retorna una representación legible de la fecha de entrega manual."""
        return self.delivery_date_text if self.delivery_date_text else "—"

    def update_search_results(self, found_emails):
        """
        Actualiza los resultados de búsqueda.

        Args:
            found_emails (int): Número de correos encontrados
        """
        self.found_emails = max(0, int(found_emails))
        self.last_search = datetime.now()
        self.updated_at = datetime.now()
        self.search_count += 1

    def get_criteria_display(self):
        """
        Retorna una representación legible de los criterios para mostrar en la interfaz.

        Returns:
            str: Criterios formateados para mostrar
        """
        if not self.search_criteria:
            return "❌ Sin criterios"
        elif len(self.search_criteria) == 1:
            return f"🔍 {self.search_criteria[0]}"
        else:
            preview = ", ".join(self.search_criteria[:2])
            suffix = "..." if len(self.search_criteria) > 2 else ""
            return f"🔍 {len(self.search_criteria)} criterios: {preview}{suffix}"

    def get_criteria_summary(self):
        """
        Retorna un resumen detallado de los criterios.

        Returns:
            dict: Resumen de criterios
        """
        return {
            "count": len(self.search_criteria),
            "criteria": self.search_criteria.copy(),
            "total_length": sum(len(c) for c in self.search_criteria),
            "avg_length": sum(len(c) for c in self.search_criteria) / len(
                self.search_criteria) if self.search_criteria else 0
        }

    def has_valid_criteria(self):
        """
        Verifica si el perfil tiene al menos un criterio válido.

        Returns:
            bool: True si tiene criterios válidos
        """
        return len(self.search_criteria) > 0 and all(
            self._validate_criteria(criterio) for criterio in self.search_criteria
        )

    def get_success_percentage(self):
        """
        Calcula el porcentaje de éxito basado en ejecuciones óptimas.

        Returns:
            float: Porcentaje de éxito (0-100+) o None si no está habilitado el seguimiento
        """
        if not self.track_optimal or self.optimal_executions <= 0:
            return None

        percentage = (self.found_emails / self.optimal_executions) * 100
        return round(percentage, 1)

    def is_success_optimal(self):
        """
        Verifica si el perfil ha alcanzado el éxito óptimo (≥100%).

        Returns:
            bool: True si el porcentaje de éxito es >= 100%
        """
        percentage = self.get_success_percentage()
        return percentage is not None and percentage >= 100.0

    def get_success_category(self):
        """
        Obtiene la categoría de éxito del perfil.

        Returns:
            str: Categoría de éxito
        """
        percentage = self.get_success_percentage()

        if percentage is None:
            return "sin_seguimiento"
        elif percentage >= 100:
            return "optimo"
        elif percentage >= 90:
            return "alto"
        elif percentage >= 50:
            return "medio"
        elif percentage >= 30:
            return "bajo"
        else:
            return "muy_bajo"

    def get_optimal_display(self):
        """
        Retorna una representación de las ejecuciones óptimas para mostrar.

        Returns:
            str: Texto formateado para mostrar ejecuciones óptimas
        """
        if not self.track_optimal:
            return "➖ Deshabilitado"

        if self.optimal_executions <= 0:
            return "⚙️ No configurado"

        return f"🎯 {self.optimal_executions}"

    def get_success_display(self):
        """
        Retorna una representación del porcentaje de éxito para mostrar.

        Returns:
            str: Texto formateado para mostrar porcentaje de éxito
        """
        percentage = self.get_success_percentage()

        if percentage is None:
            return "➖ N/A"

        category = self.get_success_category()
        emoji_map = {
            "optimo": "✅",
            "alto": "📊",
            "medio": "📊",
            "bajo": "⚠️",
            "muy_bajo": "❌"
        }

        emoji = emoji_map.get(category, "📊")
        return f"{emoji} {percentage}%"

    def get_bot_type_display(self):
        """
        Retorna una representación del tipo de bot para mostrar.

        Returns:
            str: Tipo de bot formateado para mostrar
        """
        if self.bot_type == "automatico":
            return "🤖 Automático"
        elif self.bot_type == "manual":
            return "👤 Manual"
        elif self.bot_type == "offline":
            return "📴 Offline"
        else:
            return "❓ No definido"

    def is_bot_automatic(self):
        """
        Verifica si el bot es de tipo automático.

        Returns:
            bool: True si es automático
        """
        return self.bot_type == "automatico"

    def is_bot_manual(self):
        """
        Verifica si el bot es de tipo manual.

        Returns:
            bool: True si es manual
        """
        return self.bot_type == "manual"

    def is_bot_offline(self):
        """
        Verifica si el bot es de tipo offline.

        Returns:
            bool: True si es offline
        """
        return self.bot_type == "offline"

    def get_age_days(self):
        """
        Obtiene la edad del perfil en días.

        Returns:
            int: Días desde la creación
        """
        if not self.created_at:
            return 0

        return (datetime.now() - self.created_at).days

    def get_profile_stats(self):
        """
        Obtiene estadísticas completas del perfil.

        Returns:
            dict: Estadísticas del perfil
        """
        return {
            "criteria_count": len(self.search_criteria),
            "total_searches": self.search_count,
            "total_emails_found": self.found_emails,
            "avg_emails_per_search": round(self.found_emails / max(1, self.search_count), 2),
            "success_percentage": self.get_success_percentage(),
            "success_category": self.get_success_category(),
            "bot_type": self.bot_type,
            "age_days": self.get_age_days(),
            "has_optimal_tracking": self.track_optimal,
            "last_search_days_ago": (datetime.now() - self.last_search).days if self.last_search else None,
            "sender_filters": self.sender_filters.copy(),
            "responsable": self.responsable,
            "last_update_text": self.last_update_text,
            "delivery_date_text": self.delivery_date_text
        }

    def __str__(self):
        """Representación string del perfil."""
        responsable_text = f", responsable='{self.responsable}'" if self.responsable else ""
        last_update_text = f", last_update='{self.last_update_text}'" if self.last_update_text else ""
        delivery_text = f", delivery='{self.delivery_date_text}'" if self.delivery_date_text else ""
        return (f"SearchProfile(name='{self.name}', criteria={len(self.search_criteria)}, "
                f"senders={len(self.sender_filters)}, type='{self.bot_type}'"
                f"{responsable_text}{last_update_text}{delivery_text})")

    def __repr__(self):
        """Representación técnica del perfil."""
        responsable_text = f", responsable='{self.responsable}'" if self.responsable else ""
        last_update_text = f", last_update='{self.last_update_text}'" if self.last_update_text else ""
        delivery_text = f", delivery='{self.delivery_date_text}'" if self.delivery_date_text else ""
        return (f"SearchProfile(id='{self.profile_id[:8]}...', name='{self.name}', "
                f"criteria={len(self.search_criteria)}, senders={len(self.sender_filters)}, "
                f"found={self.found_emails}{responsable_text}{last_update_text}{delivery_text})")
