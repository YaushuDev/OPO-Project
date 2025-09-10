# scheduler_service.py
"""
Servicio modular para programación de tareas automáticas.
Implementa servicios especializados para programación diaria, semanal y mensual
con manejo robusto de hilos independientes y cálculo inteligente de próximas ejecuciones.
"""

import json
import time
import threading
from datetime import datetime, timedelta, date
import os
from pathlib import Path
from abc import ABC, abstractmethod
import calendar


class BaseSchedulerService(ABC):
    """Clase base abstracta para servicios de programación."""

    def __init__(self, config_file, log_callback=None):
        """
        Inicializa el servicio base de programación.

        Args:
            config_file (Path): Ruta al archivo de configuración
            log_callback (callable, optional): Función para registrar logs
        """
        self.config_file = config_file
        self.log_callback = log_callback

        # Control de hilos
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.last_execution_time = None

        # Lock para operaciones thread-safe
        self.operation_lock = threading.Lock()

        # Estado del scheduler
        self.current_config = None
        self.next_execution = None

    def _load_config(self):
        """
        Carga configuración de programación de manera segura.

        Returns:
            dict: Configuración cargada o None si no existe
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                # Validar configuración básica
                if not isinstance(config, dict):
                    return None

                return config
        except Exception as e:
            self._log(f"❌ Error al cargar configuración de programación: {e}")
        return None

    def _start_scheduler_thread(self):
        """Inicia el hilo que ejecuta el programador de manera segura."""
        # Detener hilo existente si está corriendo
        if self.is_running:
            self._stop_scheduler_thread()

        try:
            # Limpiar evento de parada
            self.stop_event.clear()

            # Crear e iniciar nuevo hilo
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                name=f"{self.__class__.__name__}Thread",
                daemon=True
            )

            self.is_running = True
            self.scheduler_thread.start()

            self._log(f"📋 Hilo del programador {self.__class__.__name__} iniciado")

        except Exception as e:
            self.is_running = False
            self._log(f"❌ Error al iniciar hilo del programador: {e}")

    def _stop_scheduler_thread(self):
        """Detiene el hilo del programador de manera segura."""
        if not self.is_running:
            return

        try:
            # Señalar parada
            self.stop_event.set()

            # Esperar a que termine el hilo (con timeout)
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5.0)

                # Si no terminó, informar (aunque no forzamos la terminación)
                if self.scheduler_thread.is_alive():
                    self._log("⚠️ Hilo del programador no terminó gracefully")

            self.is_running = False
            self.scheduler_thread = None

            self._log(f"🛑 Hilo del programador {self.__class__.__name__} detenido")

        except Exception as e:
            self._log(f"❌ Error al detener hilo del programador: {e}")

    @abstractmethod
    def _run_scheduler(self):
        """Función que ejecuta el programador en segundo plano."""
        pass

    @abstractmethod
    def _calculate_next_execution(self, config, current_time):
        """Calcula la próxima ejecución programada."""
        pass

    @abstractmethod
    def _execute_scheduled_task(self):
        """Ejecuta la tarea programada."""
        pass

    def stop(self):
        """Detiene el programador de manera segura."""
        if self.is_running:
            self._log(f"🛑 Deteniendo servicio de programación {self.__class__.__name__}...")
            self._stop_scheduler_thread()

    def restart(self):
        """Reinicia el programador con la configuración actual de manera segura."""
        self._log(f"📋 Reiniciando servicio de programación {self.__class__.__name__}...")

        try:
            # Detener si está corriendo
            if self.is_running:
                self._stop_scheduler_thread()

            # Pequeña pausa para asegurar limpieza
            time.sleep(1)

            # Reconfigurar
            self._setup_scheduler()

        except Exception as e:
            self._log(f"❌ Error al reiniciar programación {self.__class__.__name__}: {e}")

    @abstractmethod
    def _setup_scheduler(self):
        """Configura el programador según los ajustes guardados."""
        pass

    def get_status(self):
        """
        Obtiene el estado actual del programador.

        Returns:
            dict: Estado actual del programador
        """
        try:
            status = {
                "is_running": self.is_running,
                "is_enabled": False,
                "next_execution": None,
                "last_execution": self.last_execution_time,
                "current_config": self.current_config,
                "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False,
                "scheduler_type": self.__class__.__name__
            }

            if self.current_config:
                status["is_enabled"] = self.current_config.get("enabled", False)

            if self.next_execution:
                status["next_execution"] = self.next_execution.isoformat()

            if self.last_execution_time:
                status["last_execution"] = self.last_execution_time.isoformat()

            return status

        except Exception as e:
            self._log(f"❌ Error obteniendo estado: {e}")
            return {"error": str(e)}

    def force_execution(self):
        """
        Fuerza la ejecución inmediata de la tarea programada (para testing).

        Returns:
            bool: True si la ejecución fue exitosa, False en caso contrario
        """
        self._log(f"🚀 Forzando ejecución de {self.__class__.__name__}...")

        try:
            success = self._execute_scheduled_task()
            if success:
                self._log(f"✅ Ejecución forzada de {self.__class__.__name__} completada exitosamente")
            else:
                self._log(f"❌ Ejecución forzada de {self.__class__.__name__} falló")
            return success

        except Exception as e:
            self._log(f"💥 Error en ejecución forzada de {self.__class__.__name__}: {e}")
            return False

    def _log(self, message):
        """Registra mensaje en el log de manera thread-safe."""
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception:
                # Si falla el log, no hacer nada para evitar cascada de errores
                pass


class DailySchedulerService(BaseSchedulerService):
    """Servicio específico para programación de tareas diarias."""

    def __init__(self, config_file, report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación diaria.

        Args:
            config_file (Path): Ruta al archivo de configuración
            report_generator (callable, optional): Función para generar reportes diarios
            log_callback (callable, optional): Función para registrar logs
        """
        super().__init__(config_file, log_callback)
        self.report_generator = report_generator

        # Iniciar servicio
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador diario según los ajustes guardados."""
        try:
            config = self._load_config()
            self.current_config = config

            if not config:
                self._log("Programador de reportes diarios no activado")
                return

            daily_enabled = config.get("enabled", False)

            if not daily_enabled:
                self._log("Programación de reportes diarios desactivada")
                return

            # Iniciar hilo de programación
            self._start_scheduler_thread()
            self._log("✅ Servicio de programación diaria iniciado correctamente")

        except Exception as e:
            self._log(f"❌ Error al configurar programador diario: {e}")

    def _run_scheduler(self):
        """Función optimizada que ejecuta el programador diario en segundo plano."""
        self._log("📋 Bucle del programador diario iniciado")

        # Valores iniciales para evitar ejecución inmediata
        last_execution_date = datetime.now() - timedelta(days=1)
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.stop_event.is_set():
            try:
                # Cargar configuración actual (puede haber cambiado)
                config = self._load_config()
                self.current_config = config

                if not config:
                    # Si está deshabilitado, esperar más tiempo
                    if self.stop_event.wait(60):  # Espera 60 segundos o hasta que se señale parada
                        break
                    continue

                # Verificar si está habilitado
                daily_enabled = config.get("enabled", False)
                if not daily_enabled:
                    if self.stop_event.wait(60):
                        break
                    continue

                now = datetime.now()

                # Comprobar reportes diarios
                self._check_daily_execution(now, config, last_execution_date)

                # Actualizar last_execution_date si se ha ejecutado
                if self.last_execution_time and self.last_execution_time.date() == now.date():
                    last_execution_date = self.last_execution_time

                # Esperar antes de la próxima verificación (30 segundos)
                if self.stop_event.wait(30):
                    break

            except Exception as e:
                consecutive_errors += 1
                self._log(f"💥 Error en el bucle del programador diario: {e}")

                # Pausa más larga en caso de error
                sleep_time = min(300, 60 * consecutive_errors)  # Máximo 5 minutos
                if self.stop_event.wait(sleep_time):
                    break

        self._log("👋 Bucle del programador diario terminado")

    def _check_daily_execution(self, now, config, last_execution_date):
        """
        Comprueba si es momento de ejecutar reportes diarios.

        Args:
            now (datetime): Tiempo actual
            config (dict): Configuración actual
            last_execution_date (datetime): Fecha de última ejecución
        """
        current_time = now.strftime("%H:%M")
        scheduled_time = config.get("time", "08:00")

        # Mapeo de días de la semana (0 = lunes en Python)
        day_mapping = {
            0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
            4: "friday", 5: "saturday", 6: "sunday"
        }

        current_day = day_mapping.get(now.weekday())
        days_config = config.get("days", {})

        # Calcular próxima ejecución para logs
        self._calculate_next_execution(config, now)

        # Verificar si hoy es un día programado y si es la hora configurada
        should_execute = (
                days_config.get(current_day, False) and
                current_time == scheduled_time and
                (not self.last_execution_time or self.last_execution_time.date() != now.date())
        )

        if should_execute:
            self._log(f"⏰ Ejecutando reporte diario programado: {current_day} {scheduled_time}")

            # Ejecutar reporte de manera thread-safe
            success = self._execute_scheduled_task()

            if success:
                self.last_execution_time = now
                self._log("✅ Reporte diario programado ejecutado exitosamente")
            else:
                self._log(f"❌ Error en reporte diario programado")

    def _calculate_next_execution(self, config, current_time):
        """
        Calcula y guarda la próxima ejecución programada diaria.

        Args:
            config (dict): Configuración actual
            current_time (datetime): Tiempo actual
        """
        try:
            days_config = config.get("days", {})
            scheduled_time = config.get("time", "08:00")

            # Encontrar el próximo día programado
            current_weekday = current_time.weekday()

            for i in range(7):  # Buscar en los próximos 7 días
                check_day = (current_weekday + i) % 7
                day_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][check_day]

                if days_config.get(day_name, False):
                    # Calcular fecha y hora
                    days_ahead = i
                    hour, minute = map(int, scheduled_time.split(":"))

                    # Si es hoy pero ya pasó la hora, buscar el siguiente día programado
                    if i == 0:
                        scheduled_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if scheduled_datetime <= current_time:
                            continue  # Ya pasó la hora de hoy, buscar siguiente día
                    else:
                        next_date = current_time.date() + timedelta(days=days_ahead)
                        scheduled_datetime = datetime.combine(next_date,
                                                              datetime.min.time().replace(hour=hour, minute=minute))

                    self.next_execution = scheduled_datetime
                    break
            else:
                self.next_execution = None

        except Exception as e:
            self._log(f"⚠️ Error calculando próxima ejecución diaria: {e}")
            self.next_execution = None

    def _execute_scheduled_task(self):
        """
        Ejecuta el reporte diario programado de manera thread-safe.

        Returns:
            bool: True si la ejecución fue exitosa, False en caso contrario
        """
        with self.operation_lock:
            try:
                if self.report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_execution_time = datetime.now()

                    # Ejecutar generador de reportes diarios
                    result = self.report_generator()

                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes diarios")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte diario programado: {e}")
                return False


class WeeklySchedulerService(BaseSchedulerService):
    """Servicio específico para programación de tareas semanales."""

    def __init__(self, config_file, weekly_report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación semanal.

        Args:
            config_file (Path): Ruta al archivo de configuración
            weekly_report_generator (callable, optional): Función para generar reportes semanales
            log_callback (callable, optional): Función para registrar logs
        """
        super().__init__(config_file, log_callback)
        self.weekly_report_generator = weekly_report_generator

        # Iniciar servicio
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador semanal según los ajustes guardados."""
        try:
            config = self._load_config()
            self.current_config = config

            if not config:
                self._log("Programador de reportes semanales no activado")
                return

            # Verificar configuración específica semanal
            weekly_config = config.get("weekly", {})
            weekly_enabled = weekly_config.get("enabled", False)

            if not weekly_enabled:
                self._log("Programación de reportes semanales desactivada")
                return

            # Iniciar hilo de programación
            self._start_scheduler_thread()
            self._log("✅ Servicio de programación semanal iniciado correctamente")

        except Exception as e:
            self._log(f"❌ Error al configurar programador semanal: {e}")

    def _run_scheduler(self):
        """Función optimizada que ejecuta el programador semanal en segundo plano."""
        self._log("📋 Bucle del programador semanal iniciado")

        # Valores iniciales para evitar ejecución inmediata
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.stop_event.is_set():
            try:
                # Cargar configuración actual (puede haber cambiado)
                config = self._load_config()
                self.current_config = config

                if not config:
                    # Si está deshabilitado, esperar más tiempo
                    if self.stop_event.wait(60):  # Espera 60 segundos o hasta que se señale parada
                        break
                    continue

                # Verificar configuración específica semanal
                weekly_config = config.get("weekly", {})
                weekly_enabled = weekly_config.get("enabled", False)

                if not weekly_enabled:
                    if self.stop_event.wait(60):
                        break
                    continue

                now = datetime.now()

                # Comprobar reportes semanales
                self._check_weekly_execution(now, weekly_config)

                # Esperar antes de la próxima verificación (60 segundos)
                if self.stop_event.wait(60):
                    break

            except Exception as e:
                consecutive_errors += 1
                self._log(f"💥 Error en el bucle del programador semanal: {e}")

                # Pausa más larga en caso de error
                sleep_time = min(300, 60 * consecutive_errors)  # Máximo 5 minutos
                if self.stop_event.wait(sleep_time):
                    break

        self._log("👋 Bucle del programador semanal terminado")

    def _check_weekly_execution(self, now, weekly_config):
        """
        Comprueba si es momento de ejecutar reportes semanales.

        Args:
            now (datetime): Tiempo actual
            weekly_config (dict): Configuración semanal
        """
        current_time = now.strftime("%H:%M")
        scheduled_time = weekly_config.get("time", "16:00")
        scheduled_day = weekly_config.get("day", "friday")

        # Mapeo de días de la semana (0 = lunes en Python)
        day_mapping = {
            0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
            4: "friday", 5: "saturday", 6: "sunday"
        }

        current_day = day_mapping.get(now.weekday())

        # Calcular próxima ejecución semanal para logs
        self._calculate_next_execution(weekly_config, now)

        # Verificar si hoy es el día programado y si es la hora configurada
        # Además, verificar que no se haya ejecutado hoy todavía
        should_execute = (
                current_day == scheduled_day and
                current_time == scheduled_time and
                (not self.last_execution_time or self.last_execution_time.date() != now.date())
        )

        if should_execute:
            self._log(f"⏰ Ejecutando reporte semanal programado: {scheduled_day} {scheduled_time}")

            # Ejecutar reporte semanal de manera thread-safe
            success = self._execute_scheduled_task()

            if success:
                self.last_execution_time = now
                self._log("✅ Reporte semanal programado ejecutado exitosamente")
            else:
                self._log(f"❌ Error en reporte semanal programado")

    def _calculate_next_execution(self, weekly_config, current_time):
        """
        Calcula y guarda la próxima ejecución programada semanal.

        Args:
            weekly_config (dict): Configuración semanal
            current_time (datetime): Tiempo actual
        """
        try:
            if not weekly_config.get("enabled", False):
                self.next_execution = None
                return

            scheduled_day = weekly_config.get("day", "friday")
            scheduled_time = weekly_config.get("time", "16:00")

            # Mapear el día a número de día de la semana (0=lunes, 6=domingo)
            day_mapping = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }

            target_weekday = day_mapping.get(scheduled_day, 4)  # Default a viernes si no es válido
            current_weekday = current_time.weekday()

            # Calcular días hasta el próximo día programado
            days_ahead = (target_weekday - current_weekday) % 7

            # Si es el mismo día pero ya pasó la hora, sumar una semana
            if days_ahead == 0:
                hour, minute = map(int, scheduled_time.split(":"))
                scheduled_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if scheduled_datetime <= current_time:
                    days_ahead = 7  # Esperar a la próxima semana

            # Calcular la fecha y hora exacta
            next_date = current_time.date() + timedelta(days=days_ahead)
            hour, minute = map(int, scheduled_time.split(":"))

            self.next_execution = datetime.combine(
                next_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

        except Exception as e:
            self._log(f"⚠️ Error calculando próxima ejecución semanal: {e}")
            self.next_execution = None

    def _execute_scheduled_task(self):
        """
        Ejecuta el reporte semanal programado de manera thread-safe.

        Returns:
            bool: True si la ejecución fue exitosa, False en caso contrario
        """
        with self.operation_lock:
            try:
                if self.weekly_report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_execution_time = datetime.now()

                    # Ejecutar generador de reportes semanales
                    result = self.weekly_report_generator()

                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes semanales")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte semanal programado: {e}")
                return False


class MonthlySchedulerService(BaseSchedulerService):
    """Servicio específico para programación de tareas mensuales."""

    def __init__(self, config_file, monthly_report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación mensual.

        Args:
            config_file (Path): Ruta al archivo de configuración
            monthly_report_generator (callable, optional): Función para generar reportes mensuales
            log_callback (callable, optional): Función para registrar logs
        """
        super().__init__(config_file, log_callback)
        self.monthly_report_generator = monthly_report_generator

        # Iniciar servicio
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador mensual según los ajustes guardados."""
        try:
            config = self._load_config()
            self.current_config = config

            if not config:
                self._log("Programador de reportes mensuales no activado")
                return

            # Verificar configuración específica mensual
            monthly_config = config.get("monthly", {})
            monthly_enabled = monthly_config.get("enabled", False)

            if not monthly_enabled:
                self._log("Programación de reportes mensuales desactivada")
                return

            # Iniciar hilo de programación
            self._start_scheduler_thread()
            self._log("✅ Servicio de programación mensual iniciado correctamente")

        except Exception as e:
            self._log(f"❌ Error al configurar programador mensual: {e}")

    def _run_scheduler(self):
        """Función optimizada que ejecuta el programador mensual en segundo plano."""
        self._log("📋 Bucle del programador mensual iniciado")

        # Valores iniciales para evitar ejecución inmediata
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.stop_event.is_set():
            try:
                # Cargar configuración actual (puede haber cambiado)
                config = self._load_config()
                self.current_config = config

                if not config:
                    # Si está deshabilitado, esperar más tiempo
                    if self.stop_event.wait(300):  # Espera 5 minutos o hasta que se señale parada
                        break
                    continue

                # Verificar configuración específica mensual
                monthly_config = config.get("monthly", {})
                monthly_enabled = monthly_config.get("enabled", False)

                if not monthly_enabled:
                    if self.stop_event.wait(300):
                        break
                    continue

                now = datetime.now()

                # Comprobar reportes mensuales
                self._check_monthly_execution(now, monthly_config)

                # Para chequeos mensuales, una verificación cada hora es suficiente
                if self.stop_event.wait(3600):  # 1 hora
                    break

            except Exception as e:
                consecutive_errors += 1
                self._log(f"💥 Error en el bucle del programador mensual: {e}")

                # Pausa más larga en caso de error
                sleep_time = min(3600, 300 * consecutive_errors)  # Máximo 1 hora
                if self.stop_event.wait(sleep_time):
                    break

        self._log("👋 Bucle del programador mensual terminado")

    def _check_monthly_execution(self, now, monthly_config):
        """
        Comprueba si es momento de ejecutar reportes mensuales.

        Args:
            now (datetime): Tiempo actual
            monthly_config (dict): Configuración mensual
        """
        current_time = now.strftime("%H:%M")
        scheduled_time = monthly_config.get("time", "09:00")
        scheduled_day = monthly_config.get("day", "1")  # Día del mes (1-31 o "last")

        # Determinar si hoy es el día programado
        is_scheduled_day = False

        if scheduled_day == "last":
            # Último día del mes
            last_day = calendar.monthrange(now.year, now.month)[1]
            is_scheduled_day = now.day == last_day
        else:
            # Día específico del mes
            try:
                day_num = int(scheduled_day)
                # Si el día es mayor que el último día del mes, usar el último día
                last_day = calendar.monthrange(now.year, now.month)[1]
                target_day = min(day_num, last_day)
                is_scheduled_day = now.day == target_day
            except (ValueError, TypeError):
                self._log(f"⚠️ Configuración inválida para día del mes: {scheduled_day}")
                is_scheduled_day = False

        # Calcular próxima ejecución mensual para logs
        self._calculate_next_execution(monthly_config, now)

        # Verificar si hoy es el día programado y si es la hora configurada
        # Además, verificar que no se haya ejecutado hoy todavía
        should_execute = (
                is_scheduled_day and
                current_time == scheduled_time and
                (not self.last_execution_time or self.last_execution_time.date() != now.date())
        )

        if should_execute:
            day_description = "último día" if scheduled_day == "last" else f"día {scheduled_day}"
            self._log(f"⏰ Ejecutando reporte mensual programado: {day_description} {scheduled_time}")

            # Ejecutar reporte mensual de manera thread-safe
            success = self._execute_scheduled_task()

            if success:
                self.last_execution_time = now
                self._log("✅ Reporte mensual programado ejecutado exitosamente")
            else:
                self._log(f"❌ Error en reporte mensual programado")

    def _calculate_next_execution(self, monthly_config, current_time):
        """
        Calcula y guarda la próxima ejecución programada mensual.

        Args:
            monthly_config (dict): Configuración mensual
            current_time (datetime): Tiempo actual
        """
        try:
            if not monthly_config.get("enabled", False):
                self.next_execution = None
                return

            scheduled_day = monthly_config.get("day", "1")
            scheduled_time = monthly_config.get("time", "09:00")
            hour, minute = map(int, scheduled_time.split(":"))

            # Determinar fecha objetivo
            target_date = None
            current_date = current_time.date()

            # Primero comprobar si la ejecución sería hoy
            if scheduled_day == "last":
                # Último día del mes
                last_day = calendar.monthrange(current_date.year, current_date.month)[1]
                if current_date.day == last_day:
                    # Es hoy, comprobar la hora
                    scheduled_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if scheduled_datetime > current_time:
                        target_date = current_date
            else:
                # Día específico
                try:
                    day_num = int(scheduled_day)
                    last_day = calendar.monthrange(current_date.year, current_date.month)[1]
                    # Si el día especificado es mayor que el último día, usar el último día
                    target_day = min(day_num, last_day)

                    if current_date.day == target_day:
                        # Es hoy, comprobar la hora
                        scheduled_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if scheduled_datetime > current_time:
                            target_date = current_date
                except (ValueError, TypeError):
                    self._log(f"⚠️ Configuración inválida para día del mes: {scheduled_day}")

            # Si no es hoy o ya pasó la hora, calcular para el próximo mes
            if target_date is None:
                # Determinar el mes siguiente
                if current_date.month == 12:
                    next_month = 1
                    next_year = current_date.year + 1
                else:
                    next_month = current_date.month + 1
                    next_year = current_date.year

                if scheduled_day == "last":
                    # Último día del próximo mes
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    target_date = date(next_year, next_month, last_day)
                else:
                    # Día específico del próximo mes
                    try:
                        day_num = int(scheduled_day)
                        last_day = calendar.monthrange(next_year, next_month)[1]
                        # Si el día especificado es mayor que el último día, usar el último día
                        target_day = min(day_num, last_day)
                        target_date = date(next_year, next_month, target_day)
                    except (ValueError, TypeError):
                        # Fallback a primer día si hay error
                        target_date = date(next_year, next_month, 1)

            # Combinar fecha y hora
            self.next_execution = datetime.combine(
                target_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

        except Exception as e:
            self._log(f"⚠️ Error calculando próxima ejecución mensual: {e}")
            self.next_execution = None

    def _execute_scheduled_task(self):
        """
        Ejecuta el reporte mensual programado de manera thread-safe.

        Returns:
            bool: True si la ejecución fue exitosa, False en caso contrario
        """
        with self.operation_lock:
            try:
                if self.monthly_report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_execution_time = datetime.now()

                    # Ejecutar generador de reportes mensuales
                    result = self.monthly_report_generator()

                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes mensuales")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte mensual programado: {e}")
                return False