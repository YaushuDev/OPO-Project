"""Modal unificado para configurar programación automática de reportes."""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class SchedulerModal:
    """Modal que centraliza la configuración diaria, semanal y mensual."""

    DAY_NAMES = {
        "monday": "Lunes",
        "tuesday": "Martes",
        "wednesday": "Miércoles",
        "thursday": "Jueves",
        "friday": "Viernes",
        "saturday": "Sábado",
        "sunday": "Domingo",
    }

    def __init__(self, parent, bottom_panel=None, on_close=None):
        self.parent = parent
        self.bottom_panel = bottom_panel
        self.on_close = on_close

        self.config_file = Path("config") / "scheduler_config.json"
        os.makedirs(self.config_file.parent, exist_ok=True)

        # Variables compartidas
        self.days = {day: tk.BooleanVar(value=False) for day in self.DAY_NAMES}
        self.hour = tk.StringVar(value="08")
        self.minute = tk.StringVar(value="00")
        self.enabled = tk.BooleanVar(value=False)

        self.weekly_enabled = tk.BooleanVar(value=False)
        self.weekly_day = tk.StringVar(value="friday")
        self.weekly_hour = tk.StringVar(value="16")
        self.weekly_minute = tk.StringVar(value="00")

        self.monthly_enabled = tk.BooleanVar(value=False)
        self.monthly_day_type = tk.StringVar(value="specific")
        self.monthly_day = tk.StringVar(value="1")
        self.monthly_hour = tk.StringVar(value="09")
        self.monthly_minute = tk.StringVar(value="00")

        # Widgets que se activan/desactivan según switches
        self.daily_controls = []
        self.weekly_controls = []
        self.monthly_controls = []

        # Configuración inicial desde archivo
        self._load_config()

        # Construcción de UI
        self.modal = tk.Toplevel(parent)
        self.modal.title("Programación de Reportes")
        self.modal.geometry("820x640")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()
        self.modal.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._setup_widgets()
        self._toggle_daily_scheduler()
        self._toggle_weekly_scheduler()
        self._toggle_monthly_scheduler()
        self._update_day_selection()
        self._center_window()

    # ------------------------------------------------------------------
    # Construcción de widgets
    # ------------------------------------------------------------------
    def _setup_widgets(self):
        main_frame = ttk.Frame(self.modal, padding="25 25 25 25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(
            main_frame,
            text="⏰ Programación de Reportes Automáticos",
            font=("Arial", 14, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # ----- Configuración diaria -----
        daily_frame = ttk.LabelFrame(
            main_frame,
            text="Reportes Diarios",
            padding="15 15 15 15",
        )
        daily_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))

        enable_daily = ttk.Checkbutton(
            daily_frame,
            text="Activar envío automático diario",
            variable=self.enabled,
            command=self._toggle_daily_scheduler,
        )
        enable_daily.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        days_frame = ttk.LabelFrame(daily_frame, text="Días de ejecución", padding="10 10 10 10")
        days_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        for index, (day_key, day_name) in enumerate(self.DAY_NAMES.items()):
            day_cb = ttk.Checkbutton(days_frame, text=day_name, variable=self.days[day_key])
            day_cb.grid(row=index // 2, column=index % 2, sticky="w", padx=5, pady=2)
            self.daily_controls.append(day_cb)

        time_frame = ttk.LabelFrame(daily_frame, text="Hora diaria", padding="10 10 10 10")
        time_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        hour_values = [f"{i:02d}" for i in range(24)]
        minute_values = [f"{i:02d}" for i in range(0, 60, 5)]

        hour_combo = ttk.Combobox(
            time_frame,
            textvariable=self.hour,
            values=hour_values,
            width=5,
            state="readonly",
        )
        hour_combo.grid(row=0, column=0, padx=(0, 5))
        minute_combo = ttk.Combobox(
            time_frame,
            textvariable=self.minute,
            values=minute_values,
            width=5,
            state="readonly",
        )
        minute_combo.grid(row=0, column=1, padx=(5, 0))
        self.daily_controls.extend([hour_combo, minute_combo])

        # ----- Configuración semanal -----
        weekly_frame = ttk.LabelFrame(
            main_frame,
            text="Reportes Semanales",
            padding="15 15 15 15",
        )
        weekly_frame.grid(row=1, column=1, sticky="nsew", padx=(12, 0))

        enable_weekly = ttk.Checkbutton(
            weekly_frame,
            text="Activar envío automático semanal",
            variable=self.weekly_enabled,
            command=self._toggle_weekly_scheduler,
        )
        enable_weekly.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        weekly_day_frame = ttk.LabelFrame(
            weekly_frame,
            text="Día de ejecución",
            padding="10 10 10 10",
        )
        weekly_day_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        weekly_day_combo = ttk.Combobox(
            weekly_day_frame,
            state="readonly",
            values=list(self.DAY_NAMES.values()),
            width=20,
        )
        weekly_day_combo.grid(row=0, column=0, sticky="w")
        self.weekly_controls.append(weekly_day_combo)

        # Sincronizar valor mostrado con clave interna
        inverse_day_names = {v: k for k, v in self.DAY_NAMES.items()}
        weekly_day_combo.set(self.DAY_NAMES.get(self.weekly_day.get(), "Viernes"))

        def on_weekly_day_change(event):
            selected = weekly_day_combo.get()
            if selected in inverse_day_names:
                self.weekly_day.set(inverse_day_names[selected])

        weekly_day_combo.bind("<<ComboboxSelected>>", on_weekly_day_change)

        weekly_time_frame = ttk.LabelFrame(
            weekly_frame,
            text="Hora semanal",
            padding="10 10 10 10",
        )
        weekly_time_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        weekly_hour_combo = ttk.Combobox(
            weekly_time_frame,
            textvariable=self.weekly_hour,
            values=hour_values,
            width=5,
            state="readonly",
        )
        weekly_hour_combo.grid(row=0, column=0, padx=(0, 5))
        weekly_minute_combo = ttk.Combobox(
            weekly_time_frame,
            textvariable=self.weekly_minute,
            values=minute_values,
            width=5,
            state="readonly",
        )
        weekly_minute_combo.grid(row=0, column=1, padx=(5, 0))
        self.weekly_controls.extend([weekly_hour_combo, weekly_minute_combo])

        # ----- Configuración mensual -----
        monthly_frame = ttk.LabelFrame(
            main_frame,
            text="Reportes Mensuales",
            padding="15 15 15 15",
        )
        monthly_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(20, 0))

        enable_monthly = ttk.Checkbutton(
            monthly_frame,
            text="Activar envío automático mensual",
            variable=self.monthly_enabled,
            command=self._toggle_monthly_scheduler,
        )
        enable_monthly.grid(row=0, column=0, sticky="w", pady=(0, 10))

        day_type_frame = ttk.Frame(monthly_frame)
        day_type_frame.grid(row=1, column=0, sticky="w", pady=(0, 10))

        specific_radio = ttk.Radiobutton(
            day_type_frame,
            text="Día específico del mes",
            variable=self.monthly_day_type,
            value="specific",
            command=self._update_day_selection,
        )
        specific_radio.grid(row=0, column=0, padx=(0, 15))
        last_day_radio = ttk.Radiobutton(
            day_type_frame,
            text="Último día del mes",
            variable=self.monthly_day_type,
            value="last",
            command=self._update_day_selection,
        )
        last_day_radio.grid(row=0, column=1)
        self.monthly_controls.extend([specific_radio, last_day_radio])

        self.specific_day_frame = ttk.Frame(monthly_frame)
        self.specific_day_frame.grid(row=2, column=0, sticky="w")
        ttk.Label(self.specific_day_frame, text="Día del mes:").grid(row=0, column=0, padx=(0, 10))
        day_values = [str(i) for i in range(1, 32)]
        self.day_combo = ttk.Combobox(
            self.specific_day_frame,
            textvariable=self.monthly_day,
            values=day_values,
            width=5,
            state="readonly",
        )
        self.day_combo.grid(row=0, column=1)
        self.monthly_controls.append(self.day_combo)

        monthly_time_frame = ttk.LabelFrame(
            monthly_frame,
            text="Hora mensual",
            padding="10 10 10 10",
        )
        monthly_time_frame.grid(row=3, column=0, sticky="nsew", pady=(15, 0))

        monthly_hour_combo = ttk.Combobox(
            monthly_time_frame,
            textvariable=self.monthly_hour,
            values=hour_values,
            width=5,
            state="readonly",
        )
        monthly_hour_combo.grid(row=0, column=0, padx=(0, 5))
        monthly_minute_combo = ttk.Combobox(
            monthly_time_frame,
            textvariable=self.monthly_minute,
            values=minute_values,
            width=5,
            state="readonly",
        )
        monthly_minute_combo.grid(row=0, column=1, padx=(5, 0))
        self.monthly_controls.extend([monthly_hour_combo, monthly_minute_combo])

        ttk.Label(
            monthly_frame,
            text="Si se selecciona un día inexistente para un mes determinado, se enviará el último día hábil",
            font=("Arial", 9),
            foreground="gray",
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))

        # Nota general e instrucciones
        note_label = ttk.Label(
            main_frame,
            text=(
                "Los reportes se generarán y enviarán automáticamente según la configuración.\n"
                "El sistema evita duplicados y reinicia los cálculos tras cada actualización."
            ),
            font=("Arial", 9),
            foreground="gray",
            justify="center",
        )
        note_label.grid(row=3, column=0, columnspan=2, pady=(20, 10))

        # Botones inferiores
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        save_btn = ttk.Button(button_frame, text="Guardar", command=self._save_config, width=18)
        save_btn.grid(row=0, column=0, padx=(0, 10), sticky="e")

        close_btn = ttk.Button(button_frame, text="Cerrar", command=self._handle_close, width=18)
        close_btn.grid(row=0, column=1, padx=(10, 0), sticky="w")

    # ------------------------------------------------------------------
    # Manejo de estado y validaciones
    # ------------------------------------------------------------------
    def _toggle_daily_scheduler(self):
        state = "normal" if self.enabled.get() else "disabled"
        for widget in self.daily_controls:
            widget.configure(state=state)

    def _toggle_weekly_scheduler(self):
        state = "normal" if self.weekly_enabled.get() else "disabled"
        for widget in self.weekly_controls:
            widget.configure(state=state)

    def _toggle_monthly_scheduler(self):
        state = "normal" if self.monthly_enabled.get() else "disabled"
        for widget in self.monthly_controls:
            widget.configure(state=state)
        self._update_day_selection()

    def _update_day_selection(self):
        show_specific = self.monthly_day_type.get() == "specific"
        if show_specific:
            self.specific_day_frame.grid()
            state = "readonly" if self.monthly_enabled.get() else "disabled"
            self.day_combo.configure(state=state)
        else:
            self.specific_day_frame.grid_remove()

    def _handle_close(self):
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        self.modal.destroy()

    # ------------------------------------------------------------------
    # Carga y guardado de configuración
    # ------------------------------------------------------------------
    def _load_config(self):
        raw = self._read_config_file()
        config = self._normalize_config(raw)

        daily = config["daily"]
        self.enabled.set(daily.get("enabled", False))
        for day_key, var in self.days.items():
            var.set(daily.get("days", {}).get(day_key, False))
        daily_time = daily.get("time", "08:00").split(":")
        self.hour.set(f"{int(daily_time[0]):02d}")
        self.minute.set(f"{int(daily_time[1]):02d}")

        weekly = config["weekly"]
        self.weekly_enabled.set(weekly.get("enabled", False))
        self.weekly_day.set(weekly.get("day", "friday"))
        weekly_time = weekly.get("time", "16:00").split(":")
        self.weekly_hour.set(f"{int(weekly_time[0]):02d}")
        self.weekly_minute.set(f"{int(weekly_time[1]):02d}")

        monthly = config["monthly"]
        self.monthly_enabled.set(monthly.get("enabled", False))
        day_value = monthly.get("day", "1")
        if day_value == "last":
            self.monthly_day_type.set("last")
        else:
            self.monthly_day_type.set("specific")
            self.monthly_day.set(str(day_value))
        monthly_time = monthly.get("time", "09:00").split(":")
        self.monthly_hour.set(f"{int(monthly_time[0]):02d}")
        self.monthly_minute.set(f"{int(monthly_time[1]):02d}")

        if self.bottom_panel:
            self.bottom_panel.add_log_entry("Configuración de programación cargada")

    def _save_config(self):
        if self.enabled.get() and not any(var.get() for var in self.days.values()):
            messagebox.showerror("Error", "Debe seleccionar al menos un día para los reportes diarios")
            return

        if self.monthly_enabled.get() and self.monthly_day_type.get() == "specific":
            try:
                day_value = int(self.monthly_day.get())
                if day_value < 1 or day_value > 31:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "El día del reporte mensual debe estar entre 1 y 31")
                return

        daily_config = {
            "enabled": self.enabled.get(),
            "days": {day: var.get() for day, var in self.days.items()},
            "time": f"{self.hour.get()}:{self.minute.get()}",
        }

        weekly_config = {
            "enabled": self.weekly_enabled.get(),
            "day": self.weekly_day.get(),
            "time": f"{self.weekly_hour.get()}:{self.weekly_minute.get()}",
        }

        if self.monthly_day_type.get() == "last":
            monthly_day = "last"
        else:
            monthly_day = str(int(self.monthly_day.get()))

        monthly_config = {
            "enabled": self.monthly_enabled.get(),
            "day": monthly_day,
            "time": f"{self.monthly_hour.get()}:{self.monthly_minute.get()}",
        }

        existing = self._normalize_config(self._read_config_file())
        existing["daily"] = daily_config
        existing["weekly"] = weekly_config
        existing["monthly"] = monthly_config
        existing["last_update"] = datetime.now().isoformat()

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(existing, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                logs = []
                logs.append(
                    "✅ Programación diaria "
                    + ("activada" if daily_config["enabled"] else "desactivada")
                )
                logs.append(
                    "✅ Programación semanal "
                    + ("activada" if weekly_config["enabled"] else "desactivada")
                )
                logs.append(
                    "✅ Programación mensual "
                    + ("activada" if monthly_config["enabled"] else "desactivada")
                )
                for log in logs:
                    self.bottom_panel.add_log_entry(log)

            messagebox.showinfo("Éxito", "Configuración de programación guardada correctamente")
        except Exception as exc:
            error_msg = f"Error al guardar configuración: {exc}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    # ------------------------------------------------------------------
    # Helpers de normalización
    # ------------------------------------------------------------------
    def _read_config_file(self) -> Dict:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    def _normalize_config(self, raw: Optional[Dict]) -> Dict[str, Dict]:
        default = {
            "daily": {
                "enabled": False,
                "days": {day: False for day in self.DAY_NAMES},
                "time": "08:00",
            },
            "weekly": {"enabled": False, "day": "friday", "time": "16:00"},
            "monthly": {"enabled": False, "day": "1", "time": "09:00"},
        }

        if not isinstance(raw, dict):
            return default

        # Compatibilidad con formato legacy (claves diarias en raíz)
        daily_source = raw.get("daily") if isinstance(raw.get("daily"), dict) else raw
        daily = {
            "enabled": bool(daily_source.get("enabled", False)),
            "days": self._sanitize_day_map(daily_source.get("days", {})),
            "time": self._sanitize_time_string(daily_source.get("time"), "08:00"),
        }

        weekly_source = raw.get("weekly", {})
        weekly = {
            "enabled": bool(weekly_source.get("enabled", False)),
            "day": weekly_source.get("day", "friday") if weekly_source.get("day") in self.DAY_NAMES else "friday",
            "time": self._sanitize_time_string(weekly_source.get("time"), "16:00"),
        }

        monthly_source = raw.get("monthly", {})
        monthly_day = monthly_source.get("day", "1")
        if monthly_day != "last":
            try:
                monthly_day = str(max(1, min(31, int(monthly_day))))
            except (TypeError, ValueError):
                monthly_day = "1"

        monthly = {
            "enabled": bool(monthly_source.get("enabled", False)),
            "day": monthly_day,
            "time": self._sanitize_time_string(monthly_source.get("time"), "09:00"),
        }

        return {"daily": daily, "weekly": weekly, "monthly": monthly}

    def _sanitize_day_map(self, day_map: Dict) -> Dict[str, bool]:
        sanitized = {}
        for day in self.DAY_NAMES:
            sanitized[day] = bool(day_map.get(day, False)) if isinstance(day_map, dict) else False
        return sanitized

    def _sanitize_time_string(self, value: Optional[str], default: str) -> str:
        if not value or not isinstance(value, str):
            return default
        try:
            hour, minute = value.split(":")
            hour_int = max(0, min(23, int(hour)))
            minute_int = max(0, min(59, int(minute)))
            return f"{hour_int:02d}:{minute_int:02d}"
        except (ValueError, TypeError):
            return default

    def _center_window(self):
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")
