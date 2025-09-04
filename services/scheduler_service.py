# services/scheduler_service.py
"""
Servicio para programación de tareas automáticas.
Maneja la ejecución programada de tareas como generación y envío de reportes.
"""

import json
import time
import threading
from datetime import datetime, timedelta
import os
from pathlib import Path


class SchedulerService:
    """Servicio para programación de tareas automáticas."""

    def __init__(self, report_generator=None, log_callback=None):
        """
        Inicializa el servicio de programación.

        Args:
            report_generator: Función a llamar para generar reportes
            log_callback: Función para registrar logs
        """
        self.config_file = Path("config") / "scheduler_config.json"
        self.report_generator = report_generator
        self.log_callback = log_callback
        self.scheduler_thread = None
        self.stop_event = threading.Event()

        # Iniciar servicio
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el programador según los ajustes guardados."""
        config = self._load_config()
        if not config or not config.get("enabled", False):
            self._log("Programador de reportes no activado")
            return

        # Iniciar hilo de programación
        self._start_scheduler_thread()
        self._log("Servicio de programación iniciado")

    def _run_scheduled_report(self):
        """Ejecuta la generación y envío programados del reporte."""
        self._log("Ejecutando reporte programado...")
        try:
            if self.report_generator:
                self.report_generator()
                self._log("✅ Reporte programado generado y enviado correctamente")
            else:
                self._log("⚠️ No se encontró función generadora de reportes")
        except Exception as e:
            self._log(f"❌ Error al generar reporte programado: {e}")

    def _load_config(self):
        """
        Carga configuración de programación.

        Returns:
            dict: Configuración o None si no existe
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    return json.load(file)
        except Exception as e:
            self._log(f"Error al cargar configuración de programación: {e}")
        return None

    def _start_scheduler_thread(self):
        """Inicia el hilo que ejecuta el programador."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self._log("Reiniciando hilo del programador")
            self.stop_event.set()
            self.scheduler_thread.join()
            self.stop_event.clear()

        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        self._log("Hilo del programador iniciado")

    def _run_scheduler(self):
        """Función que ejecuta el programador en segundo plano."""
        self._log("Bucle del programador iniciado")

        # Valores iniciales para evitar ejecución inmediata
        last_check_day = -1
        last_execution_date = datetime.now() - timedelta(days=1)

        while not self.stop_event.is_set():
            try:
                # Cargar configuración actual
                config = self._load_config()
                if not config or not config.get("enabled", False):
                    time.sleep(60)  # Verificar cada minuto
                    continue

                now = datetime.now()
                current_time = now.strftime("%H:%M")
                scheduled_time = config.get("time", "08:00")

                # Mapeo de días de la semana (0 = lunes en Python)
                day_mapping = {
                    0: "monday",
                    1: "tuesday",
                    2: "wednesday",
                    3: "thursday",
                    4: "friday",
                    5: "saturday",
                    6: "sunday"
                }

                current_day = day_mapping.get(now.weekday())
                days_config = config.get("days", {})

                # Verificar si hoy es un día programado y si es la hora configurada
                if (days_config.get(current_day, False) and
                        current_time == scheduled_time and
                        now.date() != last_execution_date.date()):
                    self._run_scheduled_report()
                    last_execution_date = now

                # Evitar verificaciones excesivas
                time.sleep(30)

            except Exception as e:
                self._log(f"Error en el programador: {e}")
                time.sleep(300)  # Esperar 5 minutos en caso de error

    def stop(self):
        """Detiene el programador."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop_event.set()
            self.scheduler_thread.join()
            self._log("Servicio de programación detenido")

    def restart(self):
        """Reinicia el programador con la configuración actual."""
        self._setup_scheduler()

    def _log(self, message):
        """
        Registra mensaje en el log.

        Args:
            message (str): Mensaje a registrar
        """
        if self.log_callback:
            self.log_callback(message)