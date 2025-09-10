# scheduler_service.py
"""
Servicio optimizado para programación de tareas automáticas.
Maneja la ejecución programada con threading mejorado y manejo robusto de errores.
Soporta programación de reportes diarios y semanales con control de hilos independiente.
"""

import json
import time
import threading
from datetime import datetime, timedelta
import os
from pathlib import Path


class SchedulerService:
    """Servicio optimizado para programación de tareas automáticas con threading mejorado."""

    def __init__(self, report_generator=None, weekly_report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación optimizado.

        Args:
            report_generator: Función a llamar para generar reportes diarios
            weekly_report_generator: Función a llamar para generar reportes semanales
            log_callback: Función para registrar logs
        """
        self.config_file = Path("config") / "scheduler_config.json"
        self.report_generator = report_generator
        self.weekly_report_generator = weekly_report_generator
        self.log_callback = log_callback

        # Control de hilos mejorado
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.last_execution_time = None
        self.last_weekly_execution_time = None

        # Lock para operaciones thread-safe
        self.operation_lock = threading.Lock()

        # Estado del scheduler
        self.current_config = None
        self.next_execution = None
        self.next_weekly_execution = None

        # Iniciar servicio de manera segura
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador según los ajustes guardados de manera segura."""
        try:
            config = self._load_config()
            self.current_config = config

            if not config:
                self._log("Programador de reportes no activado")
                return

            daily_enabled = config.get("enabled", False)
            weekly_enabled = config.get("weekly", {}).get("enabled", False)

            if not daily_enabled and not weekly_enabled:
                self._log("Ninguna programación de reportes activada")
                return

            # Iniciar hilo de programación de manera segura
            self._start_scheduler_thread()

            if daily_enabled:
                self._log("✅ Servicio de programación diaria iniciado correctamente")

            if weekly_enabled:
                self._log("✅ Servicio de programación semanal iniciado correctamente")

        except Exception as e:
            self._log(f"❌ Error al configurar programador: {e}")

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
                name="SchedulerThread",
                daemon=True
            )

            self.is_running = True
            self.scheduler_thread.start()

            self._log("🔄 Hilo del programador iniciado")

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

                # Si no terminó, forzar (aunque no es recomendable)
                if self.scheduler_thread.is_alive():
                    self._log("⚠️ Hilo del programador no terminó gracefully")

            self.is_running = False
            self.scheduler_thread = None

            self._log("🛑 Hilo del programador detenido")

        except Exception as e:
            self._log(f"❌ Error al detener hilo del programador: {e}")

    def _run_scheduler(self):
        """Función optimizada que ejecuta el programador en segundo plano."""
        self._log("🔄 Bucle del programador iniciado")

        # Valores iniciales para evitar ejecución inmediata
        last_execution_date = datetime.now() - timedelta(days=1)
        last_weekly_execution_date = datetime.now() - timedelta(days=1)
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

                now = datetime.now()

                # Comprobar reportes diarios
                daily_enabled = config.get("enabled", False)
                if daily_enabled:
                    self._check_daily_reports(now, config, last_execution_date)

                # Comprobar reportes semanales
                weekly_config = config.get("weekly", {})
                weekly_enabled = weekly_config.get("enabled", False)
                if weekly_enabled:
                    self._check_weekly_reports(now, weekly_config, last_weekly_execution_date)

                # Esperar antes de la próxima verificación (30 segundos)
                if self.stop_event.wait(30):
                    break

            except Exception as e:
                consecutive_errors += 1
                self._log(f"💥 Error en el bucle del programador: {e}")

                # Pausa más larga en caso de error
                sleep_time = min(300, 60 * consecutive_errors)  # Máximo 5 minutos
                if self.stop_event.wait(sleep_time):
                    break

        self._log("👋 Bucle del programador terminado")

    def _check_daily_reports(self, now, config, last_execution_date):
        """Comprueba si es momento de ejecutar reportes diarios."""
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
                now.date() != last_execution_date.date()
        )

        if should_execute:
            self._log(f"⏰ Ejecutando reporte diario programado: {current_day} {scheduled_time}")

            # Ejecutar reporte de manera thread-safe
            success = self._execute_scheduled_report()

            if success:
                self.last_execution_time = now
                self._log("✅ Reporte diario programado ejecutado exitosamente")
            else:
                self._log(f"❌ Error en reporte diario programado")

    def _check_weekly_reports(self, now, weekly_config, last_weekly_execution_date):
        """Comprueba si es momento de ejecutar reportes semanales."""
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
        self._calculate_next_weekly_execution(weekly_config, now)

        # Verificar si hoy es el día programado y si es la hora configurada
        should_execute = (
                current_day == scheduled_day and
                current_time == scheduled_time and
                now.date() != last_weekly_execution_date.date()
        )

        if should_execute:
            self._log(f"⏰ Ejecutando reporte semanal programado: {scheduled_day} {scheduled_time}")

            # Ejecutar reporte semanal de manera thread-safe
            success = self._execute_scheduled_weekly_report()

            if success:
                self.last_weekly_execution_time = now
                self._log("✅ Reporte semanal programado ejecutado exitosamente")
            else:
                self._log(f"❌ Error en reporte semanal programado")

    def _calculate_next_execution(self, config, current_time):
        """Calcula y guarda la próxima ejecución programada diaria."""
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

    def _calculate_next_weekly_execution(self, weekly_config, current_time):
        """Calcula y guarda la próxima ejecución programada semanal."""
        try:
            if not weekly_config.get("enabled", False):
                self.next_weekly_execution = None
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

            self.next_weekly_execution = datetime.combine(
                next_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

        except Exception as e:
            self._log(f"⚠️ Error calculando próxima ejecución semanal: {e}")
            self.next_weekly_execution = None

    def _execute_scheduled_report(self):
        """Ejecuta el reporte diario programado de manera thread-safe."""
        with self.operation_lock:
            try:
                if self.report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_execution_time = datetime.now()

                    # Ejecutar generador de reportes
                    result = self.report_generator()

                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes diarios")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte diario programado: {e}")
                return False

    def _execute_scheduled_weekly_report(self):
        """Ejecuta el reporte semanal programado de manera thread-safe."""
        with self.operation_lock:
            try:
                if self.weekly_report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_weekly_execution_time = datetime.now()

                    # Ejecutar generador de reportes semanales
                    result = self.weekly_report_generator()

                    return bool(result)
                elif self.report_generator:
                    # Si no hay generador específico para semanales, intentar usar el diario
                    self._log("ℹ️ Usando generador de reportes diarios para reporte semanal")
                    self.last_weekly_execution_time = datetime.now()
                    result = self.report_generator(is_weekly=True)
                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes semanales")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte semanal programado: {e}")
                return False

    def _load_config(self):
        """Carga configuración de programación de manera segura."""
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

    def stop(self):
        """Detiene el programador de manera segura."""
        if self.is_running:
            self._log("🛑 Deteniendo servicio de programación...")
            self._stop_scheduler_thread()

    def restart(self):
        """Reinicia el programador con la configuración actual de manera segura."""
        self._log("🔄 Reiniciando servicio de programación...")

        try:
            # Detener si está corriendo
            if self.is_running:
                self._stop_scheduler_thread()

            # Pequeña pausa para asegurar limpieza
            time.sleep(1)

            # Reconfigurar
            self._setup_scheduler()

        except Exception as e:
            self._log(f"❌ Error al reiniciar programación: {e}")

    def get_status(self):
        """Obtiene el estado actual del programador."""
        try:
            status = {
                "is_running": self.is_running,
                "is_enabled": False,
                "is_weekly_enabled": False,
                "next_execution": None,
                "next_weekly_execution": None,
                "last_execution": self.last_execution_time,
                "last_weekly_execution": self.last_weekly_execution_time,
                "current_config": self.current_config,
                "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False
            }

            if self.current_config:
                status["is_enabled"] = self.current_config.get("enabled", False)
                weekly_config = self.current_config.get("weekly", {})
                status["is_weekly_enabled"] = weekly_config.get("enabled", False)

            if self.next_execution:
                status["next_execution"] = self.next_execution.isoformat()

            if self.next_weekly_execution:
                status["next_weekly_execution"] = self.next_weekly_execution.isoformat()

            if self.last_execution_time:
                status["last_execution"] = self.last_execution_time.isoformat()

            if self.last_weekly_execution_time:
                status["last_weekly_execution"] = self.last_weekly_execution_time.isoformat()

            return status

        except Exception as e:
            self._log(f"❌ Error obteniendo estado: {e}")
            return {"error": str(e)}

    def force_execution(self, weekly=False):
        """
        Fuerza la ejecución inmediata de un reporte (para testing).

        Args:
            weekly (bool): Si es True, ejecuta el reporte semanal en lugar del diario
        """
        if weekly:
            if not self.weekly_report_generator and not self.report_generator:
                self._log("❌ No hay función generadora de reportes semanales configurada")
                return False

            self._log("🚀 Forzando ejecución de reporte semanal...")

            try:
                success = self._execute_scheduled_weekly_report()
                if success:
                    self._log("✅ Ejecución forzada de reporte semanal completada exitosamente")
                else:
                    self._log("❌ Ejecución forzada de reporte semanal falló")
                return success

            except Exception as e:
                self._log(f"💥 Error en ejecución forzada de reporte semanal: {e}")
                return False
        else:
            if not self.report_generator:
                self._log("❌ No hay función generadora de reportes diarios configurada")
                return False

            self._log("🚀 Forzando ejecución de reporte diario...")

            try:
                success = self._execute_scheduled_report()
                if success:
                    self._log("✅ Ejecución forzada de reporte diario completada exitosamente")
                else:
                    self._log("❌ Ejecución forzada de reporte diario falló")
                return success

            except Exception as e:
                self._log(f"💥 Error en ejecución forzada de reporte diario: {e}")
                return False

    def _log(self, message):
        """Registra mensaje en el log de manera thread-safe."""
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception:
                # Si falla el log, no hacer nada para evitar cascada de errores
                pass

    def __del__(self):
        """Destructor para limpiar recursos."""
        try:
            self.stop()
        except Exception:
            pass