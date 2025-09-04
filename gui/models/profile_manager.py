# gui/models/profile_manager.py
"""
Gestor para manejar perfiles de búsqueda.
Proporciona funciones para cargar, guardar, añadir, actualizar y eliminar perfiles
con soporte para múltiples criterios de búsqueda y seguimiento de ejecuciones óptimas.
"""

import json
import os
from pathlib import Path
from gui.models.search_profile import SearchProfile


class ProfileManager:
    """Gestiona operaciones CRUD para perfiles de búsqueda con múltiples criterios y seguimiento óptimo."""

    def __init__(self, config_dir=None):
        """
        Inicializa el gestor de perfiles.

        Args:
            config_dir (str, optional): Directorio de configuración. Por defecto "config".
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.profiles_file = self.config_dir / "search_profiles.json"
        self.profiles = []

        # Crear directorio de configuración si no existe
        os.makedirs(self.config_dir, exist_ok=True)

        # Cargar perfiles existentes
        self.load_profiles()

    def load_profiles(self):
        """
        Carga perfiles desde el archivo de configuración.
        Mantiene compatibilidad con formato antiguo (string) y nuevo (lista).
        Incluye compatibilidad hacia atrás para perfiles sin seguimiento óptimo.

        Returns:
            list: Lista de perfiles cargados
        """
        if not self.profiles_file.exists():
            self.profiles = []
            return self.profiles

        try:
            with open(self.profiles_file, "r", encoding="utf-8") as file:
                profiles_data = json.load(file)
                self.profiles = []

                for data in profiles_data:
                    try:
                        profile = SearchProfile.from_dict(data)
                        self.profiles.append(profile)
                    except Exception as e:
                        print(f"Error al cargar perfil {data.get('name', 'desconocido')}: {e}")
                        continue

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar archivo de perfiles: {e}")
            self.profiles = []

        print(f"Perfiles cargados: {len(self.profiles)}")
        # Mostrar estadísticas de seguimiento óptimo
        tracking_profiles = [p for p in self.profiles if p.track_optimal]
        if tracking_profiles:
            print(f"Perfiles con seguimiento óptimo: {len(tracking_profiles)}")

        return self.profiles

    def save_profiles(self):
        """
        Guarda los perfiles en el archivo de configuración incluyendo campos de seguimiento óptimo.

        Returns:
            bool: True si se guardaron correctamente, False en caso contrario
        """
        try:
            profiles_data = []
            for profile in self.profiles:
                try:
                    profile_dict = profile.to_dict()
                    profiles_data.append(profile_dict)
                except Exception as e:
                    print(f"Error al serializar perfil {profile.name}: {e}")
                    continue

            with open(self.profiles_file, "w", encoding="utf-8") as file:
                json.dump(profiles_data, file, indent=4, ensure_ascii=False)
            return True
        except (IOError, TypeError) as e:
            print(f"Error al guardar perfiles: {e}")
            return False

    def get_all_profiles(self):
        """
        Retorna todos los perfiles.

        Returns:
            list: Lista de todos los perfiles
        """
        return self.profiles

    def get_profile_by_id(self, profile_id):
        """
        Busca un perfil por su ID.

        Args:
            profile_id (str): ID del perfil a buscar

        Returns:
            SearchProfile: Perfil encontrado o None si no existe
        """
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def add_profile(self, name, search_criteria):
        """
        Añade un nuevo perfil con múltiples criterios de búsqueda.
        Los campos de seguimiento óptimo se configuran después de la creación.

        Args:
            name (str): Nombre del perfil
            search_criteria (str or list): Criterio(s) de búsqueda.
                                         Puede ser string único o lista de hasta 3 criterios.

        Returns:
            SearchProfile: Perfil creado
        """
        try:
            profile = SearchProfile(name, search_criteria)

            # Validar que el perfil tenga criterios válidos
            if not profile.has_valid_criteria():
                raise ValueError("El perfil debe tener al menos un criterio válido")

            self.profiles.append(profile)

            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                print(f"Perfil creado: '{name}' con {criterios_count} criterio(s)")
                return profile
            else:
                # Si falla al guardar, remover el perfil de la lista
                self.profiles.remove(profile)
                raise Exception("Error al guardar el perfil en archivo")

        except Exception as e:
            print(f"Error al crear perfil '{name}': {e}")
            return None

    def update_profile(self, profile_id, name, search_criteria):
        """
        Actualiza un perfil existente con nuevos criterios.
        Nota: Los campos de seguimiento óptimo deben actualizarse por separado.

        Args:
            profile_id (str): ID del perfil a actualizar
            name (str): Nuevo nombre
            search_criteria (str or list): Nuevo(s) criterio(s) de búsqueda

        Returns:
            SearchProfile: Perfil actualizado o None si no existe o hay error
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            print(f"Perfil con ID {profile_id} no encontrado")
            return None

        try:
            # Guardar valores originales por si hay error
            original_name = profile.name
            original_criteria = profile.search_criteria.copy()

            # Actualizar solo los criterios básicos (no los campos de seguimiento óptimo)
            profile.update(name, search_criteria)

            # Validar que tenga criterios válidos
            if not profile.has_valid_criteria():
                # Restaurar valores originales
                profile.name = original_name
                profile.search_criteria = original_criteria
                raise ValueError("El perfil debe tener al menos un criterio válido")

            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                print(f"Perfil actualizado: '{name}' con {criterios_count} criterio(s)")
                return profile
            else:
                # Restaurar valores originales si falla al guardar
                profile.name = original_name
                profile.search_criteria = original_criteria
                raise Exception("Error al guardar cambios en archivo")

        except Exception as e:
            print(f"Error al actualizar perfil '{name}': {e}")
            return None

    def delete_profile(self, profile_id):
        """
        Elimina un perfil.

        Args:
            profile_id (str): ID del perfil a eliminar

        Returns:
            bool: True si se eliminó correctamente, False si no existe o hay error
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            print(f"Perfil con ID {profile_id} no encontrado para eliminar")
            return False

        try:
            profile_name = profile.name
            optimal_text = " (con seguimiento óptimo)" if profile.track_optimal else ""
            self.profiles.remove(profile)

            if self.save_profiles():
                print(f"Perfil eliminado: '{profile_name}'{optimal_text}")
                return True
            else:
                # Si falla al guardar, restaurar el perfil
                self.profiles.append(profile)
                raise Exception("Error al guardar cambios tras eliminación")

        except Exception as e:
            print(f"Error al eliminar perfil: {e}")
            return False

    def update_search_results(self, profile_id, found_emails):
        """
        Actualiza los resultados de búsqueda para un perfil.
        Ahora maneja la suma de múltiples criterios y calcula automáticamente porcentajes de éxito.

        Args:
            profile_id (str): ID del perfil
            found_emails (int): Número total de correos encontrados (suma de todos los criterios)

        Returns:
            SearchProfile: Perfil actualizado o None si no existe
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            print(f"Perfil con ID {profile_id} no encontrado para actualizar resultados")
            return None

        try:
            profile.update_search_results(found_emails)

            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                message = f"Resultados actualizados para '{profile.name}': {found_emails} ejecuciones " \
                          f"(búsqueda en {criterios_count} criterio(s))"

                # Agregar información de éxito si está habilitado el seguimiento
                if profile.track_optimal:
                    success_percentage = profile.get_success_percentage()
                    if success_percentage is not None:
                        message += f" - Éxito: {success_percentage}%"
                        if profile.is_success_optimal():
                            message += " ✅"

                print(message)
                return profile
            else:
                raise Exception("Error al guardar resultados de búsqueda")

        except Exception as e:
            print(f"Error al actualizar resultados para perfil {profile_id}: {e}")
            return None

    def get_profiles_summary(self):
        """
        Retorna un resumen estadístico de los perfiles incluyendo métricas de seguimiento óptimo.

        Returns:
            dict: Estadísticas ampliadas de los perfiles
        """
        if not self.profiles:
            return {
                "total_profiles": 0,
                "active_profiles": 0,
                "total_criteria": 0,
                "total_emails_found": 0,
                "profiles_with_tracking": 0,
                "optimal_profiles": 0,
                "avg_success_percentage": 0
            }

        active_profiles = [p for p in self.profiles if p.last_search is not None]
        total_criteria = sum(len(p.search_criteria) for p in self.profiles)
        total_emails = sum(p.found_emails for p in self.profiles)

        # Estadísticas de seguimiento óptimo
        profiles_with_tracking = [p for p in self.profiles if p.track_optimal]
        optimal_profiles = [p for p in profiles_with_tracking if p.is_success_optimal()]

        # Calcular promedio de éxito
        success_percentages = []
        for profile in profiles_with_tracking:
            percentage = profile.get_success_percentage()
            if percentage is not None:
                success_percentages.append(percentage)

        avg_success = round(sum(success_percentages) / len(success_percentages), 1) if success_percentages else 0

        return {
            "total_profiles": len(self.profiles),
            "active_profiles": len(active_profiles),
            "total_criteria": total_criteria,
            "total_emails_found": total_emails,
            "avg_criteria_per_profile": round(total_criteria / len(self.profiles), 1),
            "avg_emails_per_active_profile": round(total_emails / len(active_profiles), 1) if active_profiles else 0,
            # Nuevas métricas
            "profiles_with_tracking": len(profiles_with_tracking),
            "optimal_profiles": len(optimal_profiles),
            "avg_success_percentage": avg_success,
            "success_rate": round((len(optimal_profiles) / len(profiles_with_tracking)) * 100,
                                  1) if profiles_with_tracking else 0
        }