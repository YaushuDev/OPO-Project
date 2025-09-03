# gui/models/profile_manager.py
"""
Gestor para manejar perfiles de búsqueda.
Proporciona funciones para cargar, guardar, añadir, actualizar y eliminar perfiles.
"""

import json
import os
from pathlib import Path
from gui.models.search_profile import SearchProfile


class ProfileManager:
    """Gestiona operaciones CRUD para perfiles de búsqueda."""

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

        Returns:
            list: Lista de perfiles cargados
        """
        if not self.profiles_file.exists():
            self.profiles = []
            return self.profiles

        try:
            with open(self.profiles_file, "r", encoding="utf-8") as file:
                profiles_data = json.load(file)
                self.profiles = [SearchProfile.from_dict(data) for data in profiles_data]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar perfiles: {e}")
            self.profiles = []

        return self.profiles

    def save_profiles(self):
        """
        Guarda los perfiles en el archivo de configuración.

        Returns:
            bool: True si se guardaron correctamente, False en caso contrario
        """
        try:
            profiles_data = [profile.to_dict() for profile in self.profiles]
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
        Añade un nuevo perfil.

        Args:
            name (str): Nombre del perfil
            search_criteria (str): Criterio de búsqueda

        Returns:
            SearchProfile: Perfil creado
        """
        profile = SearchProfile(name, search_criteria)
        self.profiles.append(profile)
        self.save_profiles()
        return profile

    def update_profile(self, profile_id, name, search_criteria):
        """
        Actualiza un perfil existente.

        Args:
            profile_id (str): ID del perfil a actualizar
            name (str): Nuevo nombre
            search_criteria (str): Nuevo criterio de búsqueda

        Returns:
            SearchProfile: Perfil actualizado o None si no existe
        """
        profile = self.get_profile_by_id(profile_id)
        if profile:
            profile.update(name, search_criteria)
            self.save_profiles()
        return profile

    def delete_profile(self, profile_id):
        """
        Elimina un perfil.

        Args:
            profile_id (str): ID del perfil a eliminar

        Returns:
            bool: True si se eliminó correctamente, False si no existe
        """
        profile = self.get_profile_by_id(profile_id)
        if profile:
            self.profiles.remove(profile)
            self.save_profiles()
            return True
        return False

    def update_search_results(self, profile_id, found_emails):
        """
        Actualiza los resultados de búsqueda para un perfil.

        Args:
            profile_id (str): ID del perfil
            found_emails (int): Número de correos encontrados

        Returns:
            SearchProfile: Perfil actualizado o None si no existe
        """
        profile = self.get_profile_by_id(profile_id)
        if profile:
            profile.update_search_results(found_emails)
            self.save_profiles()
        return profile