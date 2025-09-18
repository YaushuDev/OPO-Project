"""Servicios para programación automática de reportes.

Este módulo implementa un programador unificado capaz de manejar
configuraciones diarias, semanales y mensuales utilizando un único hilo
de fondo. Mejora la lógica previa al consolidar cálculos de próximas
ejecuciones, tolerancias de tiempo flexibles y reinicios controlados
cada vez que la configuración cambia.
"""

from __future__ import annotations

import calendar
import json
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional


class UnifiedSchedulerService:
    """Programa tareas automáticas diarias, semanales y mensuales.

    La clase centraliza toda la lógica de programación en un único hilo
    de fondo. Cada tipo de frecuencia (diaria, semanal y mensual) puede
    tener su propio callback y configuración independiente, pero el
    servicio se encarga de coordinar la ejecución evitando duplicados y
    manejando periodos de tolerancia para no perder ejecuciones si el
    hilo se despierta unos minutos tarde.
    """

    DAY_ORDER = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    FREQUENCIES = ("daily", "weekly", "monthly")

    def __init__(
        self,
        config_file: Path,
        callbacks: Optional[Dict[str, Callable[[], bool]]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Inicializa el servicio unificado de programación."""

        self.config_file = Path(config_file)
        self.callbacks = callbacks or {}
        self.log_callback = log_callback

        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.current_config: Dict[str, Dict] = {}
        self.next_executions: Dict[str, Optional[datetime]] = {
            freq: None for freq in self.FREQUENCIES
        }
        self.last_execution_times: Dict[str, Optional[datetime]] = {
            freq: None for freq in self.FREQUENCIES
        }

        self.is_running = False

        # Asegurar que el directorio exista para evitar errores al leer/escribir
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        self._setup_scheduler()

    # ------------------------------------------------------------------
    # Configuración y carga de datos
    # ------------------------------------------------------------------
    def _setup_scheduler(self) -> None:
        """Carga configuración inicial y arranca el hilo si corresponde."""

        self.current_config = self._load_config()

        if self._any_frequency_enabled(self.current_config):
            self._start_thread()
        else:
            self._log(
                "Programación automática desactivada: no hay frecuencias habilitadas"
            )

    def _load_config(self) -> Dict[str, Dict]:
        """Carga y normaliza la configuración de programación."""

        raw_config = self._read_config_file()
        normalized = self._normalize_config(raw_config)
        return normalized

    def _read_config_file(self) -> Dict:
        """Lee el archivo de configuración si existe."""

        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as exc:  # pragma: no cover - errores raros de lectura
            self._log(f"❌ Error al leer configuración de programación: {exc}")
            return {}

    def _normalize_config(self, raw_config: Optional[Dict]) -> Dict[str, Dict]:
        """Normaliza la configuración para asegurar llaves y valores válidos."""

        default_config = {
            "daily": {
                "enabled": False,
                "days": {day: False for day in self.DAY_ORDER},
                "time": "08:00",
            },
            "weekly": {
                "enabled": False,
                "day": "friday",
                "time": "16:00",
            },
            "monthly": {
                "enabled": False,
                "day": "1",
                "time": "09:00",
            },
        }

        if not raw_config:
            return default_config

        config = default_config.copy()
        config["daily"] = {**default_config["daily"], **self._extract_daily(raw_config)}
        config["weekly"] = {
            **default_config["weekly"],
            **self._extract_weekly(raw_config.get("weekly")),
        }
        config["monthly"] = {
            **default_config["monthly"],
            **self._extract_monthly(raw_config.get("monthly")),
        }
        return config

    def _extract_daily(self, raw_config: Dict) -> Dict:
        """Extrae configuración diaria soportando formatos heredados."""

        daily_config = raw_config.get("daily")
        if isinstance(daily_config, dict):
            source = daily_config
        else:
            # Formato legacy donde las claves estaban en la raíz del JSON
            source = raw_config

        enabled = bool(source.get("enabled", False))
        time_value = self._sanitize_time(source.get("time"), default="08:00")
        days_raw = source.get("days", {})
        days = {day: bool(days_raw.get(day, False)) for day in self.DAY_ORDER}

        return {"enabled": enabled, "time": time_value, "days": days}

    def _extract_weekly(self, weekly_config: Optional[Dict]) -> Dict:
        """Extrae configuración semanal normalizada."""

        if not isinstance(weekly_config, dict):
            weekly_config = {}

        day = weekly_config.get("day", "friday")
        if day not in self.DAY_ORDER:
            day = "friday"

        time_value = self._sanitize_time(weekly_config.get("time"), default="16:00")

        return {
            "enabled": bool(weekly_config.get("enabled", False)),
            "day": day,
            "time": time_value,
        }

    def _extract_monthly(self, monthly_config: Optional[Dict]) -> Dict:
        """Extrae configuración mensual normalizada."""

        if not isinstance(monthly_config, dict):
            monthly_config = {}

        day_value = monthly_config.get("day", "1")
        if isinstance(day_value, int):
            day_value = str(day_value)

        if isinstance(day_value, str):
            day_value = day_value.strip() or "1"
            if day_value != "last":
                try:
                    number = int(day_value)
                    if number < 1:
                        number = 1
                    if number > 31:
                        number = 31
                    day_value = str(number)
                except ValueError:
                    day_value = "1"
        else:
            day_value = "1"

        time_value = self._sanitize_time(monthly_config.get("time"), default="09:00")

        return {
            "enabled": bool(monthly_config.get("enabled", False)),
            "day": day_value,
            "time": time_value,
        }

    def _sanitize_time(self, value: Optional[str], default: str) -> str:
        """Normaliza una cadena de hora en formato HH:MM."""

        if not value or not isinstance(value, str):
            return default

        parts = value.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except (TypeError, ValueError):
            return default

        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        return f"{hour:02d}:{minute:02d}"

    # ------------------------------------------------------------------
    # Gestión del hilo del programador
    # ------------------------------------------------------------------
    def _start_thread(self) -> None:
        """Inicia el hilo del programador unificado."""

        if self.thread and self.thread.is_alive():
            self.stop()

        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self._run_scheduler,
            name="UnifiedSchedulerThread",
            daemon=True,
        )
        self.thread.start()
        self.is_running = True
        self._log("📋 Hilo de programación automática iniciado")

    def stop(self) -> None:
        """Detiene el hilo de programación si está en ejecución."""

        if not self.thread or not self.thread.is_alive():
            self.is_running = False
            return

        self._log("🛑 Deteniendo programación automática...")
        self.stop_event.set()
        self.thread.join(timeout=5)
        self.thread = None
        self.is_running = False
        self._log("🛑 Programación automática detenida")

    def restart(self) -> None:
        """Recarga configuración y reinicia el hilo si es necesario."""

        self._log("♻️ Reiniciando servicio de programación automática...")
        self.stop()
        self.current_config = self._load_config()
        if self._any_frequency_enabled(self.current_config):
            self._start_thread()
        else:
            self._log(
                "Programación automática desactivada tras la actualización de configuración"
            )

    # ------------------------------------------------------------------
    # Lógica principal del scheduler
    # ------------------------------------------------------------------
    def _run_scheduler(self) -> None:
        """Bucle principal que vigila próximas ejecuciones."""

        self._log("▶️ Bucle del programador unificado iniciado")
        consecutive_errors = 0

        while not self.stop_event.is_set():
            wait_seconds = 60  # Valor por defecto si no hay próximas ejecuciones

            try:
                config = self._load_config()
                self.current_config = config

                now = datetime.now()
                due_tasks = self._collect_due_tasks(config, now)

                for frequency in due_tasks:
                    self._execute_task(frequency)

                self.next_executions = self._calculate_next_executions(config, now)
                wait_seconds = self._compute_sleep_interval(now, self.next_executions)
                consecutive_errors = 0

            except Exception as exc:  # pragma: no cover - fallos inesperados
                consecutive_errors += 1
                wait_seconds = min(300, 30 * consecutive_errors)
                self._log(f"💥 Error en el bucle del programador: {exc}")

            if self.stop_event.wait(wait_seconds):
                break

        self._log("⏹️ Bucle del programador unificado finalizado")

    def _collect_due_tasks(self, config: Dict[str, Dict], now: datetime) -> Iterable[str]:
        """Determina qué frecuencias deben ejecutarse en este instante."""

        tolerance = timedelta(minutes=5)
        due_tasks = []

        # Diarios
        daily = config.get("daily", {})
        if daily.get("enabled"):
            day_key = self.DAY_ORDER[now.weekday()]
            if daily.get("days", {}).get(day_key, False):
                scheduled = self._build_datetime_from_time(now.date(), daily.get("time", "08:00"))
                if self._should_run("daily", scheduled, now, tolerance):
                    due_tasks.append("daily")

        # Semanales
        weekly = config.get("weekly", {})
        if weekly.get("enabled"):
            if weekly.get("day") == self.DAY_ORDER[now.weekday()]:
                scheduled = self._build_datetime_from_time(now.date(), weekly.get("time", "16:00"))
                if self._should_run("weekly", scheduled, now, tolerance, period="week"):
                    due_tasks.append("weekly")

        # Mensuales
        monthly = config.get("monthly", {})
        if monthly.get("enabled"):
            target_date = self._resolve_monthly_date(now.date(), monthly.get("day", "1"))
            if target_date == now.date():
                scheduled = self._build_datetime_from_time(target_date, monthly.get("time", "09:00"))
                if self._should_run("monthly", scheduled, now, tolerance, period="month"):
                    due_tasks.append("monthly")

        return due_tasks

    def _should_run(
        self,
        frequency: str,
        scheduled: datetime,
        now: datetime,
        tolerance: timedelta,
        period: str = "day",
    ) -> bool:
        """Determina si se debe ejecutar una frecuencia determinada."""

        if now < scheduled:
            return False

        if now - scheduled > tolerance:
            # Ya pasó demasiado tiempo, esperar a la próxima ventana
            return False

        last_run = self.last_execution_times.get(frequency)
        if not last_run:
            return True

        if period == "day":
            return last_run.date() != now.date()
        if period == "week":
            return last_run.isocalendar()[:2] != now.isocalendar()[:2]
        if period == "month":
            return (last_run.year, last_run.month) != (now.year, now.month)

        return True

    def _calculate_next_executions(
        self, config: Dict[str, Dict], now: datetime
    ) -> Dict[str, Optional[datetime]]:
        """Calcula la siguiente ejecución para cada frecuencia."""

        next_times: Dict[str, Optional[datetime]] = {freq: None for freq in self.FREQUENCIES}

        daily = config.get("daily", {})
        if daily.get("enabled"):
            next_times["daily"] = self._next_daily_execution(daily, now)

        weekly = config.get("weekly", {})
        if weekly.get("enabled"):
            next_times["weekly"] = self._next_weekly_execution(weekly, now)

        monthly = config.get("monthly", {})
        if monthly.get("enabled"):
            next_times["monthly"] = self._next_monthly_execution(monthly, now)

        return next_times

    def _compute_sleep_interval(
        self, now: datetime, next_executions: Dict[str, Optional[datetime]]
    ) -> int:
        """Determina cuántos segundos debe dormir el hilo."""

        upcoming = [dt for dt in next_executions.values() if dt is not None]
        if not upcoming:
            return 60

        seconds_until_next = min((dt - now).total_seconds() for dt in upcoming)
        if seconds_until_next <= 0:
            return 30

        # Limitar a una hora para seguir revisando periódicamente
        return int(max(30, min(seconds_until_next, 3600)))

    # ------------------------------------------------------------------
    # Helpers de cálculo de próximas ejecuciones
    # ------------------------------------------------------------------
    def _build_datetime_from_time(self, target_date: date, time_str: str) -> datetime:
        hour, minute = self._split_time(time_str, default=(0, 0))
        return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))

    def _split_time(self, value: str, default: tuple[int, int]) -> tuple[int, int]:
        try:
            parts = value.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, AttributeError, TypeError):
            return default

        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        return hour, minute

    def _next_daily_execution(self, daily: Dict, now: datetime) -> Optional[datetime]:
        hour, minute = self._split_time(daily.get("time", "08:00"), default=(8, 0))
        days_config = daily.get("days", {})

        for offset in range(0, 7):
            candidate_date = now.date() + timedelta(days=offset)
            day_key = self.DAY_ORDER[(now.weekday() + offset) % 7]
            if not days_config.get(day_key, False):
                continue

            candidate_datetime = datetime.combine(
                candidate_date, datetime.min.time().replace(hour=hour, minute=minute)
            )

            if candidate_datetime <= now:
                continue

            return candidate_datetime

        return None

    def _next_weekly_execution(self, weekly: Dict, now: datetime) -> Optional[datetime]:
        hour, minute = self._split_time(weekly.get("time", "16:00"), default=(16, 0))
        target_day = weekly.get("day", "friday")
        if target_day not in self.DAY_ORDER:
            target_day = "friday"

        current_weekday = now.weekday()
        target_weekday = self.DAY_ORDER.index(target_day)
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            candidate_date = now.date()
        else:
            candidate_date = now.date() + timedelta(days=days_ahead)

        candidate_datetime = datetime.combine(
            candidate_date, datetime.min.time().replace(hour=hour, minute=minute)
        )

        if candidate_datetime <= now:
            candidate_date += timedelta(days=7)
            candidate_datetime = datetime.combine(
                candidate_date, datetime.min.time().replace(hour=hour, minute=minute)
            )

        return candidate_datetime

    def _next_monthly_execution(self, monthly: Dict, now: datetime) -> Optional[datetime]:
        hour, minute = self._split_time(monthly.get("time", "09:00"), default=(9, 0))
        day_value = monthly.get("day", "1")

        candidate_date = self._resolve_monthly_date(now.date(), day_value)
        candidate_datetime = datetime.combine(
            candidate_date, datetime.min.time().replace(hour=hour, minute=minute)
        )

        if candidate_datetime <= now:
            # Calcular para el mes siguiente
            if candidate_date.month == 12:
                next_month = 1
                next_year = candidate_date.year + 1
            else:
                next_month = candidate_date.month + 1
                next_year = candidate_date.year

            next_date = date(next_year, next_month, 1)
            candidate_date = self._resolve_monthly_date(next_date, day_value)
            candidate_datetime = datetime.combine(
                candidate_date, datetime.min.time().replace(hour=hour, minute=minute)
            )

        return candidate_datetime

    def _resolve_monthly_date(self, reference_date: date, day_value: str) -> date:
        """Determina la fecha correcta para un reporte mensual."""

        if day_value == "last":
            last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            return date(reference_date.year, reference_date.month, last_day)

        try:
            day_num = int(day_value)
        except (ValueError, TypeError):
            day_num = 1

        last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
        day_num = max(1, min(last_day, day_num))
        return date(reference_date.year, reference_date.month, day_num)

    # ------------------------------------------------------------------
    # Ejecución de tareas y utilidades públicas
    # ------------------------------------------------------------------
    def _execute_task(self, frequency: str) -> bool:
        """Ejecuta el callback asociado a una frecuencia."""

        callback = self.callbacks.get(frequency)
        if not callback:
            self._log(f"⚠️ No se encontró callback para la frecuencia '{frequency}'")
            return False

        with self.lock:
            self._log(f"⏰ Ejecutando tarea programada: {frequency}")
            try:
                success = bool(callback())
            except Exception as exc:  # pragma: no cover - errores en callback
                self._log(f"💥 Error ejecutando tarea {frequency}: {exc}")
                success = False

            if success:
                self.last_execution_times[frequency] = datetime.now()
                self._log(f"✅ Tarea programada '{frequency}' completada")
            else:
                self._log(f"❌ Tarea programada '{frequency}' finalizó con errores")

            return success

    def force_execution(self, frequency: Optional[str] = None) -> bool:
        """Fuerza la ejecución inmediata de una o varias frecuencias."""

        if frequency:
            return self._execute_task(frequency)

        results = [self._execute_task(freq) for freq in self.FREQUENCIES]
        return any(results)

    def get_status(self) -> Dict[str, Dict]:
        """Retorna información del estado actual del scheduler."""

        status: Dict[str, Dict] = {
            "is_running": self.is_running,
            "thread_alive": bool(self.thread and self.thread.is_alive()),
            "frequencies": {},
        }

        for frequency in self.FREQUENCIES:
            frequency_status = {
                "enabled": self.current_config.get(frequency, {}).get("enabled", False),
                "next_execution": self._format_datetime(self.next_executions.get(frequency)),
                "last_execution": self._format_datetime(
                    self.last_execution_times.get(frequency)
                ),
            }
            status["frequencies"][frequency] = frequency_status

        return status

    def _any_frequency_enabled(self, config: Dict[str, Dict]) -> bool:
        return any(config.get(freq, {}).get("enabled", False) for freq in self.FREQUENCIES)

    def _format_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    def _log(self, message: str) -> None:
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception:
                pass
