# profile_manager.py
"""
Gestor optimizado para manejar perfiles de búsqueda.
Proporciona funciones CRUD robustas con validaciones mejoradas,
manejo de errores graceful y estadísticas avanzadas.
"""

import json
import os
from pathlib import Path
from gui.models.search_profile import SearchProfile


class ProfileManager:
    """Gestiona operaciones CRUD para perfiles de búsqueda con validaciones mejoradas."""

    def __init__(self, config_dir=None):
        """
        Inicializa el gestor de perfiles.

        Args:
            config_dir (str, optional): Directorio de configuración. Por defecto "config".
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.profiles_file = self.config_dir / "search_profiles.json"
        self.backup_file = self.config_dir / "search_profiles_backup.json"
        self.profiles = []

        # Crear directorio de configuración si no existe
        os.makedirs(self.config_dir, exist_ok=True)

        # Cargar perfiles existentes
        self.load_profiles()

    def load_profiles(self):
        """
        Carga perfiles desde el archivo de configuración con manejo robusto de errores.

        Returns:
            list: Lista de perfiles cargados
        """
        if not self.profiles_file.exists():
            self.profiles = []
            self._log(f"Archivo de perfiles no existe, iniciando con lista vacía")
            return self.profiles

        try:
            with open(self.profiles_file, "r", encoding="utf-8") as file:
                profiles_data = json.load(file)

            if not isinstance(profiles_data, list):
                self._log(f"Archivo de perfiles tiene formato inválido, iniciando con lista vacía")
                self.profiles = []
                return self.profiles

            loaded_profiles = []
            failed_profiles = []

            for i, data in enumerate(profiles_data):
                try:
                    profile = SearchProfile.from_dict(data)

                    # Validación adicional después de la carga
                    if self._validate_loaded_profile(profile):
                        loaded_profiles.append(profile)
                    else:
                        failed_profiles.append(f"Perfil {i + 1}: validación fallida")

                except Exception as e:
                    profile_name = data.get('name', f'perfil #{i + 1}') if isinstance(data,
                                                                                      dict) else f'perfil #{i + 1}'
                    failed_profiles.append(f"{profile_name}: {str(e)}")
                    continue

            self.profiles = loaded_profiles

            # Log de resultados
            self._log(f"Perfiles cargados exitosamente: {len(loaded_profiles)}")

            if failed_profiles:
                self._log(f"Perfiles con errores: {len(failed_profiles)}")
                for error in failed_profiles[:5]:  # Mostrar solo los primeros 5 errores
                    self._log(f"  ⚠️ {error}")
                if len(failed_profiles) > 5:
                    self._log(f"  ... y {len(failed_profiles) - 5} más")

            # Mostrar estadísticas mejoradas
            self._log_profile_statistics()

        except (json.JSONDecodeError, IOError) as e:
            self._log(f"Error crítico al cargar archivo de perfiles: {e}")

            # Intentar cargar backup si existe
            if self._try_load_backup():
                self._log("Backup cargado exitosamente")
            else:
                self.profiles = []
                self._log("Iniciando con lista vacía de perfiles")

        return self.profiles

    def _validate_loaded_profile(self, profile):
        """
        Valida un perfil después de cargarlo.

        Args:
            profile (SearchProfile): Perfil a validar

        Returns:
            bool: True si el perfil es válido
        """
        try:
            # Verificar que tiene criterios válidos
            if not profile.has_valid_criteria():
                return False

            # Verificar que el nombre no esté vacío
            if not profile.name or not profile.name.strip():
                return False

            # Normalizar filtros de remitente si existen
            sender_filters = getattr(profile, "sender_filters", [])
            if sender_filters:
                profile.sender_filters = profile._process_sender_filters(sender_filters)

            # Normalizar responsable si existe
            try:
                profile.responsable = profile._process_responsable(getattr(profile, "responsable", ""))
            except ValueError:
                profile.responsable = ""

            # Verificar que el tipo de bot sea válido
            if profile.bot_type not in SearchProfile.BOT_TYPES:
                profile.bot_type = "manual"  # Corrección automática

            # Verificar rangos numéricos
            if profile.found_emails < 0:
                profile.found_emails = 0

            if profile.optimal_executions < 0:
                profile.optimal_executions = 0

            return True

        except Exception:
            return False

    def _try_load_backup(self):
        """
        Intenta cargar desde el archivo de backup.

        Returns:
            bool: True si se pudo cargar el backup
        """
        if not self.backup_file.exists():
            return False

        try:
            with open(self.backup_file, "r", encoding="utf-8") as file:
                profiles_data = json.load(file)

            loaded_profiles = []
            for data in profiles_data:
                try:
                    profile = SearchProfile.from_dict(data)
                    if self._validate_loaded_profile(profile):
                        loaded_profiles.append(profile)
                except:
                    continue

            if loaded_profiles:
                self.profiles = loaded_profiles
                return True

        except Exception as e:
            self._log(f"Error al cargar backup: {e}")

        return False

    def _log_profile_statistics(self):
        """Log estadísticas detalladas de los perfiles cargados."""
        if not self.profiles:
            return

        stats = self.get_profiles_summary()
        automatic_bots = len([p for p in self.profiles if p.is_bot_automatic()])
        manual_bots = len([p for p in self.profiles if p.is_bot_manual()])
        offline_bots = len([p for p in self.profiles if p.is_bot_offline()])
        sender_filter_profiles = len([p for p in self.profiles if p.has_sender_filters()])
        responsable_profiles = len([p for p in self.profiles if p.has_responsable()])

        # Estadísticas por categoría de éxito
        success_categories = {}
        for profile in self.profiles:
            if profile.track_optimal:
                category = profile.get_success_category()
                success_categories[category] = success_categories.get(category, 0) + 1

        self._log(f"📊 Estadísticas detalladas:")
        self._log(f"  📁 Total: {stats['total_profiles']} perfiles")
        self._log(f"  🎯 Criterios: {stats['total_criteria']} total")
        self._log(
            f"  🤖 Tipos: {automatic_bots} automáticos, {manual_bots} manuales, {offline_bots} offline"
        )
        self._log(f"  ✉️ Filtros de remitente: {sender_filter_profiles} perfiles")
        self._log(f"  👥 Responsables definidos: {responsable_profiles}")
        self._log(f"  📈 Seguimiento: {stats['profiles_with_tracking']} con tracking óptimo")

        if success_categories:
            self._log(f"  🏆 Categorías de éxito: {success_categories}")

    def save_profiles(self):
        """
        Guarda los perfiles con backup automático y validaciones.

        Returns:
            bool: True si se guardaron correctamente
        """
        if not self.profiles:
            # Guardar archivo vacío válido
            try:
                with open(self.profiles_file, "w", encoding="utf-8") as file:
                    json.dump([], file, indent=4, ensure_ascii=False)
                self._log("Archivo de perfiles vacío guardado")
                return True
            except Exception as e:
                self._log(f"Error al guardar archivo vacío: {e}")
                return False

        try:
            # Crear backup antes de guardar
            self._create_backup()

            # Serializar perfiles con validación
            profiles_data = []
            for profile in self.profiles:
                try:
                    if self._validate_loaded_profile(profile):
                        profile_dict = profile.to_dict()
                        profiles_data.append(profile_dict)
                    else:
                        self._log(f"⚠️ Perfil '{profile.name}' no pasó validación al guardar")
                except Exception as e:
                    self._log(f"Error al serializar perfil '{getattr(profile, 'name', 'unknown')}': {e}")
                    continue

            # Guardar archivo
            with open(self.profiles_file, "w", encoding="utf-8") as file:
                json.dump(profiles_data, file, indent=4, ensure_ascii=False)

            self._log(f"✅ Perfiles guardados: {len(profiles_data)}/{len(self.profiles)}")
            return True

        except (IOError, TypeError) as e:
            self._log(f"❌ Error crítico al guardar perfiles: {e}")
            return False

    def _create_backup(self):
        """Crea backup del archivo actual si existe."""
        if self.profiles_file.exists():
            try:
                # Copiar archivo actual como backup
                with open(self.profiles_file, 'r', encoding='utf-8') as src:
                    with open(self.backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except Exception as e:
                self._log(f"⚠️ No se pudo crear backup: {e}")

    def get_all_profiles(self):
        """
        Retorna todos los perfiles válidos.

        Returns:
            list: Lista de todos los perfiles válidos
        """
        return [p for p in self.profiles if self._validate_loaded_profile(p)]

    def get_profile_by_id(self, profile_id):
        """
        Busca un perfil por su ID con validación.

        Args:
            profile_id (str): ID del perfil a buscar

        Returns:
            SearchProfile: Perfil encontrado o None si no existe o no es válido
        """
        if not profile_id:
            return None

        for profile in self.profiles:
            if profile.profile_id == profile_id:
                if self._validate_loaded_profile(profile):
                    return profile
                else:
                    self._log(f"⚠️ Perfil {profile_id} encontrado pero no es válido")
                    return None
        return None

    def add_profile(self, name, search_criteria, sender_filters=None, responsable=None,
                    bot_type=None, track_optimal=None, optimal_executions=None):
        """
        Añade un nuevo perfil con validaciones robustas.

        Args:
            name (str): Nombre del perfil
            search_criteria (str or list): Criterio(s) de búsqueda
            sender_filters (str or list, optional): Remitentes permitidos
            responsable (str, optional): Responsable asignado al perfil
            bot_type (str, optional): Tipo de bot (automatico/manual/offline)
            track_optimal (bool, optional): Habilita seguimiento de ejecuciones óptimas
            optimal_executions (int, optional): Cantidad esperada de ejecuciones óptimas

        Returns:
            SearchProfile: Perfil creado o None si hubo error
        """
        try:
            # Verificar nombre único
            if self._is_name_duplicate(name):
                self._log(f"❌ Ya existe un perfil con el nombre '{name}'")
                return None

            # Crear perfil (las validaciones están en SearchProfile.__init__)
            profile = SearchProfile(
                name,
                search_criteria,
                sender_filters=sender_filters,
                responsable=responsable
            )

            # Configurar tipo de bot si se proporciona
            if bot_type in SearchProfile.BOT_TYPES:
                profile.bot_type = bot_type

            # Configurar seguimiento óptimo
            if track_optimal is not None:
                profile.track_optimal = bool(track_optimal)

            if optimal_executions is not None:
                profile.optimal_executions = max(0, int(optimal_executions))

            # Validación adicional
            if not self._validate_loaded_profile(profile):
                self._log(f"❌ El perfil '{name}' no pasó las validaciones")
                return None

            # Añadir a la lista
            self.profiles.append(profile)

            # Guardar
            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                sender_info = ""
                if profile.has_sender_filters():
                    sender_info = f", {len(profile.sender_filters)} remitente(s) filtrado(s)"
                responsable_info = f", responsable: {profile.responsable}" if profile.has_responsable() else ""
                self._log(
                    f"✅ Perfil creado: '{name}' con {criterios_count} criterio(s)"
                    f"{sender_info}{responsable_info}"
                )
                return profile
            else:
                # Si falla al guardar, remover de la lista
                self.profiles.remove(profile)
                self._log(f"❌ Error al guardar perfil '{name}'")
                return None

        except Exception as e:
            self._log(f"❌ Error al crear perfil '{name}': {e}")
            return None

    def _is_name_duplicate(self, name, exclude_id=None):
        """
        Verifica si ya existe un perfil con el mismo nombre.

        Args:
            name (str): Nombre a verificar
            exclude_id (str, optional): ID de perfil a excluir de la verificación

        Returns:
            bool: True si el nombre ya existe
        """
        name_lower = name.lower().strip()
        for profile in self.profiles:
            if (profile.profile_id != exclude_id and
                    profile.name.lower().strip() == name_lower):
                return True
        return False

    def update_profile(self, profile_id, name, search_criteria, sender_filters=None,
                       responsable=None, optimal_executions=None, track_optimal=None,
                       bot_type=None):
        """
        Actualiza un perfil existente con validaciones.

        Args:
            profile_id (str): ID del perfil a actualizar
            name (str): Nuevo nombre
            search_criteria (str or list): Nuevo(s) criterio(s) de búsqueda
            sender_filters (str or list, optional): Nuevos filtros de remitente
            responsable (str, optional): Responsable asignado al perfil
            optimal_executions (int, optional): Ejecuciones óptimas esperadas
            track_optimal (bool, optional): Habilita seguimiento de óptimos
            bot_type (str, optional): Tipo de bot

        Returns:
            SearchProfile: Perfil actualizado o None si no existe o hay error
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            self._log(f"❌ Perfil con ID {profile_id} no encontrado")
            return None

        try:
            # Verificar nombre único (excluyendo el perfil actual)
            if self._is_name_duplicate(name, profile_id):
                self._log(f"❌ Ya existe otro perfil con el nombre '{name}'")
                return None

            # Guardar valores originales por si hay error
            original_name = profile.name
            original_criteria = profile.search_criteria.copy()
            original_sender_filters = profile.sender_filters.copy()
            original_optimal = profile.optimal_executions
            original_track = profile.track_optimal
            original_bot_type = profile.bot_type
            original_responsable = profile.responsable

            # Actualizar perfil (las validaciones están en SearchProfile.update)
            profile.update(
                name,
                search_criteria,
                optimal_executions,
                track_optimal,
                bot_type,
                sender_filters,
                responsable=responsable
            )

            # Validación adicional
            if not self._validate_loaded_profile(profile):
                # Restaurar valores originales
                profile.name = original_name
                profile.search_criteria = original_criteria
                profile.sender_filters = original_sender_filters
                profile.optimal_executions = original_optimal
                profile.track_optimal = original_track
                profile.bot_type = original_bot_type
                profile.responsable = original_responsable
                self._log(f"❌ El perfil actualizado '{name}' no pasó las validaciones")
                return None

            # Guardar
            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                sender_info = ""
                if profile.has_sender_filters():
                    sender_info = f", {len(profile.sender_filters)} remitente(s) filtrado(s)"
                responsable_info = f", responsable: {profile.responsable}" if profile.has_responsable() else ""
                self._log(
                    f"✅ Perfil actualizado: '{name}' con {criterios_count} criterio(s)"
                    f"{sender_info}{responsable_info}"
                )
                return profile
            else:
                # Restaurar valores originales si falla al guardar
                profile.name = original_name
                profile.search_criteria = original_criteria
                profile.sender_filters = original_sender_filters
                profile.optimal_executions = original_optimal
                profile.track_optimal = original_track
                profile.bot_type = original_bot_type
                profile.responsable = original_responsable
                self._log(f"❌ Error al guardar cambios del perfil '{name}'")
                return None

        except Exception as e:
            self._log(f"❌ Error al actualizar perfil '{name}': {e}")
            return None

    def delete_profile(self, profile_id):
        """
        Elimina un perfil con confirmación y backup.

        Args:
            profile_id (str): ID del perfil a eliminar

        Returns:
            bool: True si se eliminó correctamente
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            self._log(f"❌ Perfil con ID {profile_id} no encontrado para eliminar")
            return False

        try:
            profile_name = profile.name
            bot_type = profile.bot_type
            criterios_count = len(profile.search_criteria)

            # Crear backup antes de eliminar
            self._create_backup()

            # Remover de la lista
            self.profiles.remove(profile)

            # Guardar
            if self.save_profiles():
                self._log(f"✅ Perfil eliminado: '{profile_name}' [{bot_type}] ({criterios_count} criterios)")
                return True
            else:
                # Si falla al guardar, restaurar el perfil
                self.profiles.append(profile)
                self._log(f"❌ Error al guardar tras eliminar perfil '{profile_name}'")
                return False

        except Exception as e:
            self._log(f"❌ Error al eliminar perfil: {e}")
            return False

    def update_search_results(self, profile_id, found_emails):
        """
        Actualiza los resultados de búsqueda para un perfil.

        Args:
            profile_id (str): ID del perfil
            found_emails (int): Número total de correos encontrados

        Returns:
            SearchProfile: Perfil actualizado o None si no existe
        """
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            self._log(f"❌ Perfil con ID {profile_id} no encontrado para actualizar resultados")
            return None

        try:
            profile.update_search_results(found_emails)

            if self.save_profiles():
                criterios_count = len(profile.search_criteria)
                bot_type = "Automático" if profile.is_bot_automatic() else "Manual"

                message = f"📊 Resultados actualizados: '{profile.name}' [{bot_type}] - " \
                          f"{found_emails} ejecuciones ({criterios_count} criterios)"

                # Agregar información de éxito si está habilitado el seguimiento
                if profile.track_optimal:
                    success_percentage = profile.get_success_percentage()
                    if success_percentage is not None:
                        success_category = profile.get_success_category()
                        emoji_map = {
                            "optimo": "✅",
                            "alto": "📊",
                            "medio": "📊",
                            "bajo": "⚠️",
                            "muy_bajo": "❌"
                        }
                        emoji = emoji_map.get(success_category, "📊")
                        message += f" | Éxito: {emoji} {success_percentage}%"

                self._log(message)
                return profile
            else:
                self._log(f"❌ Error al guardar resultados de búsqueda para '{profile.name}'")
                return None

        except Exception as e:
            self._log(f"❌ Error al actualizar resultados para perfil {profile_id}: {e}")
            return None

    def get_profiles_summary(self):
        """
        Retorna estadísticas avanzadas de los perfiles.

        Returns:
            dict: Estadísticas completas de los perfiles
        """
        valid_profiles = self.get_all_profiles()

        if not valid_profiles:
            return {
                "total_profiles": 0,
                "active_profiles": 0,
                "total_criteria": 0,
                "total_emails_found": 0,
                "avg_criteria_per_profile": 0,
                "avg_emails_per_active_profile": 0,
                "profiles_with_tracking": 0,
                "optimal_profiles": 0,
                "avg_success_percentage": 0,
                "success_rate": 0,
                "automatic_bots": 0,
                "manual_bots": 0,
                "offline_bots": 0,
                "profiles_with_sender_filter": 0,
                "profiles_with_responsable": 0,
                "success_categories": {}
            }

        # Estadísticas básicas
        active_profiles = [p for p in valid_profiles if p.last_search is not None]
        total_criteria = sum(len(p.search_criteria) for p in valid_profiles)
        total_emails = sum(p.found_emails for p in valid_profiles)

        # Estadísticas de seguimiento óptimo
        profiles_with_tracking = [p for p in valid_profiles if p.track_optimal]
        optimal_profiles = [p for p in profiles_with_tracking if p.is_success_optimal()]

        # Calcular promedio de éxito
        success_percentages = []
        for profile in profiles_with_tracking:
            percentage = profile.get_success_percentage()
            if percentage is not None:
                success_percentages.append(percentage)

        avg_success = round(sum(success_percentages) / len(success_percentages), 1) if success_percentages else 0

        # Estadísticas de tipos de bot
        automatic_bots = len([p for p in valid_profiles if p.is_bot_automatic()])
        manual_bots = len([p for p in valid_profiles if p.is_bot_manual()])
        offline_bots = len([p for p in valid_profiles if p.is_bot_offline()])
        profiles_with_sender_filter = len([p for p in valid_profiles if p.has_sender_filters()])
        profiles_with_responsable = len([p for p in valid_profiles if p.has_responsable()])

        # Categorías de éxito
        success_categories = {}
        for profile in profiles_with_tracking:
            category = profile.get_success_category()
            success_categories[category] = success_categories.get(category, 0) + 1

        return {
            "total_profiles": len(valid_profiles),
            "active_profiles": len(active_profiles),
            "total_criteria": total_criteria,
            "total_emails_found": total_emails,
            "avg_criteria_per_profile": round(total_criteria / len(valid_profiles), 1),
            "avg_emails_per_active_profile": round(total_emails / len(active_profiles), 1) if active_profiles else 0,
            "profiles_with_tracking": len(profiles_with_tracking),
            "optimal_profiles": len(optimal_profiles),
            "avg_success_percentage": avg_success,
            "success_rate": round((len(optimal_profiles) / len(profiles_with_tracking)) * 100,
                                  1) if profiles_with_tracking else 0,
            "automatic_bots": automatic_bots,
            "manual_bots": manual_bots,
            "offline_bots": offline_bots,
            "profiles_with_sender_filter": profiles_with_sender_filter,
            "profiles_with_responsable": profiles_with_responsable,
            "success_categories": success_categories
        }

    def cleanup_invalid_profiles(self):
        """
        Limpia perfiles inválidos de la lista.

        Returns:
            int: Número de perfiles eliminados
        """
        initial_count = len(self.profiles)
        self.profiles = [p for p in self.profiles if self._validate_loaded_profile(p)]
        removed_count = initial_count - len(self.profiles)

        if removed_count > 0:
            self._log(f"🧹 Limpieza completada: {removed_count} perfiles inválidos eliminados")
            self.save_profiles()

        return removed_count

    def _log(self, message):
        """
        Log interno para debugging (puede ser extendido).

        Args:
            message (str): Mensaje a loggear
        """
        # Por ahora solo print, pero puede conectarse a sistema de logging
        print(f"[ProfileManager] {message}")
