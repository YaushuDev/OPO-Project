# scheduler_service.py
"""
Servicio optimizado para programación de tareas automáticas.
Maneja la ejecución programada con threading mejorado y manejo robusto de errores.
Previene bloqueos y proporciona mejor control de hilos.
"""

import json
import time
import threading
from datetime import datetime, timedelta
import os
from pathlib import Path


class SchedulerService:
    """Servicio optimizado para programación de tareas automáticas con threading mejorado."""

    def __init__(self, report_generator=None, weekly_report_generator=None,
                 monthly_report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación optimizado.

        Args:
            report_generator: Función a llamar para generar reportes diarios
            weekly_report_generator: Función para generar reportes semanales
            monthly_report_generator: Función para generar reportes mensuales
            log_callback: Función para registrar logs
        """
        self.config_file = Path("config") / "scheduler_config.json"
        self.report_generator = report_generator
        self.weekly_report_generator = weekly_report_generator
        self.monthly_report_generator = monthly_report_generator
        self.log_callback = log_callback

        # Control de hilos mejorado
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.last_execution_time = None

        # Lock para operaciones thread-safe
        self.operation_lock = threading.Lock()

        # Estado del scheduler
        self.current_config = None
        self.next_execution = None
        self.last_weekly_execution = None
        self.last_monthly_execution = None
        self.weekly_time = "08:00"
        self.monthly_time = "08:00"

        # Iniciar servicio de manera segura
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador según los ajustes guardados de manera segura."""
        try:
            config = self._load_config()
            self.current_config = config

            if not config or not config.get("enabled", False):
                self._log("Programador de reportes no activado")
                return

            # Iniciar hilo de programación de manera segura
            self._start_scheduler_thread()
            self._log("✅ Servicio de programación iniciado correctamente")

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
        last_check_day = -1
        last_execution_date = datetime.now() - timedelta(days=1)
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.stop_event.is_set():
            try:
                # Cargar configuración actual (puede haber cambiado)
                config = self._load_config()
                self.current_config = config

                if not config or not config.get("enabled", False):
                    # Si está deshabilitado, esperar más tiempo
                    if self.stop_event.wait(60):  # Espera 60 segundos o hasta que se señale parada
                        break
                    continue

                now = datetime.now()
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
                    self._log(f"⏰ Ejecutando reporte programado: {current_day} {scheduled_time}")

                    # Ejecutar reporte de manera thread-safe
                    success = self._execute_scheduled_report()

                    if success:
                        last_execution_date = now
                        consecutive_errors = 0
                        self._log("✅ Reporte programado ejecutado exitosamente")
                    else:
                        consecutive_errors += 1
                        self._log(f"❌ Error en reporte programado (error #{consecutive_errors})")

                        # Si hay muchos errores consecutivos, pausar por más tiempo
                        if consecutive_errors >= max_consecutive_errors:
                            self._log(
                                f"⚠️ Demasiados errores consecutivos ({consecutive_errors}), pausando scheduler por 1 hora")
                            if self.stop_event.wait(3600):  # Pausa de 1 hora
                                break
                            consecutive_errors = 0  # Reset después de la pausa

                # Reportes semanal y mensual automáticos
                if self.weekly_report_generator:
                    if current_day == "saturday" and current_time == self.weekly_time:
                        if not self.last_weekly_execution or self.last_weekly_execution.date() != now.date():
                            self._log("⏰ Ejecutando reporte semanal programado")
                            success = self._execute_custom_report(self.weekly_report_generator)
                            if success:
                                self.last_weekly_execution = now
                                self._log("✅ Reporte semanal ejecutado")
                            else:
                                self._log("❌ Error en reporte semanal programado")

                if self.monthly_report_generator:
                    next_day = now + timedelta(days=1)
                    is_last_day = next_day.month != now.month
                    if is_last_day and current_time == self.monthly_time:
                        if not self.last_monthly_execution or (
                                self.last_monthly_execution.month != now.month or
                                self.last_monthly_execution.year != now.year):
                            self._log("⏰ Ejecutando reporte mensual programado")
                            success = self._execute_custom_report(self.monthly_report_generator)
                            if success:
                                self.last_monthly_execution = now
                                self._log("✅ Reporte mensual ejecutado")
                            else:
                                self._log("❌ Error en reporte mensual programado")

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

        self._log("🏁 Bucle del programador terminado")

    def _calculate_next_execution(self, config, current_time):
        """Calcula y guarda la próxima ejecución programada."""
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
            self._log(f"⚠️ Error calculando próxima ejecución: {e}")
            self.next_execution = None

    def _execute_scheduled_report(self):
        """Ejecuta el reporte programado de manera thread-safe."""
        with self.operation_lock:
            try:
                if self.report_generator:
                    # Actualizar timestamp de última ejecución
                    self.last_execution_time = datetime.now()

                    # Ejecutar generador de reportes
                    result = self.report_generator()

                    return bool(result)
                else:
                    self._log("⚠️ No se encontró función generadora de reportes")
                    return False

            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte programado: {e}")
                return False

    def _execute_custom_report(self, generator):
        """Ejecuta un generador de reportes personalizado de manera segura."""
        with self.operation_lock:
            try:
                if generator:
                    self.last_execution_time = datetime.now()
                    result = generator()
                    return bool(result)
                else:
                    self._log("⚠️ Generador de reportes no disponible")
                    return False
            except Exception as e:
                self._log(f"💥 Error al ejecutar reporte: {e}")
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
                "next_execution": None,
                "last_execution": self.last_execution_time,
                "current_config": self.current_config,
                "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False
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
        """Fuerza la ejecución inmediata de un reporte (para testing)."""
        if not self.report_generator:
            self._log("❌ No hay función generadora configurada")
            return False

        self._log("🚀 Forzando ejecución de reporte...")

        try:
            success = self._execute_scheduled_report()
            if success:
                self._log("✅ Ejecución forzada completada exitosamente")
            else:
                self._log("❌ Ejecución forzada falló")
            return success

        except Exception as e:
            self._log(f"💥 Error en ejecución forzada: {e}")
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