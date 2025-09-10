# gui/components/scheduler_modal.py
"""
Modal para configurar programación de envío automático de reportes.
Implementa un diseño horizontal optimizado con dos columnas principales:
configuración diaria a la izquierda y semanal a la derecha.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from datetime import datetime


class SchedulerModal:
    """Modal optimizado con diseño horizontal para configuración de reportes diarios y semanales."""

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de programación con diseño horizontal.

        Args:
            parent: Widget padre
            bottom_panel: Referencia al panel para registrar logs
        """
        self.parent = parent
        self.bottom_panel = bottom_panel
        self.config_file = Path("config") / "scheduler_config.json"

        # Crear directorio de configuración
        os.makedirs(Path("config"), exist_ok=True)

        # Crear ventana modal optimizada para layout horizontal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Programación de Reportes")
        self.modal.geometry("800x600")  # Más ancho y menos alto para layout horizontal
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variables para días de la semana (reportes diarios)
        self.days = {
            "monday": tk.BooleanVar(value=False),
            "tuesday": tk.BooleanVar(value=False),
            "wednesday": tk.BooleanVar(value=False),
            "thursday": tk.BooleanVar(value=False),
            "friday": tk.BooleanVar(value=False),
            "saturday": tk.BooleanVar(value=False),
            "sunday": tk.BooleanVar(value=False)
        }

        # Variables para hora (reportes diarios)
        self.hour = tk.StringVar(value="08")
        self.minute = tk.StringVar(value="00")

        # Variable para habilitar/deshabilitar programación diaria
        self.enabled = tk.BooleanVar(value=False)

        # Variable para habilitar/deshabilitar programación semanal
        self.weekly_enabled = tk.BooleanVar(value=False)

        # Variable para día de la semana del reporte semanal
        self.weekly_day = tk.StringVar(value="friday")

        # Variables para hora del reporte semanal
        self.weekly_hour = tk.StringVar(value="16")
        self.weekly_minute = tk.StringVar(value="00")

        # Centrar ventana
        self._center_window()

        # Cargar configuración existente
        self._load_config()

        # Configurar widgets con layout horizontal
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la interfaz del modal con layout horizontal."""
        # Frame principal
        main_frame = ttk.Frame(self.modal, padding="25 25 25 25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid principal con dos columnas de igual ancho
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Título general (ocupa ambas columnas)
        title_label = ttk.Label(
            main_frame,
            text="⏰ Programación de Reportes",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # ==== SECCIÓN DE REPORTES DIARIOS (COLUMNA IZQUIERDA) ====
        daily_frame = ttk.LabelFrame(
            main_frame,
            text="Configuración de Reportes Diarios",
            padding="15 15 15 15"
        )
        daily_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Switch para activar/desactivar programación diaria
        enable_switch = ttk.Checkbutton(
            daily_frame,
            text="Activar envío automático de reportes diarios",
            variable=self.enabled,
            command=self._toggle_daily_scheduler
        )
        enable_switch.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Frame para días de la semana (optimizado para layout vertical)
        days_frame = ttk.LabelFrame(
            daily_frame,
            text="Días de envío",
            padding="10 10 10 10"
        )
        days_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 15))

        # Mapeo de días con nombres en español
        day_names = {
            "monday": "Lunes",
            "tuesday": "Martes",
            "wednesday": "Miércoles",
            "thursday": "Jueves",
            "friday": "Viernes",
            "saturday": "Sábado",
            "sunday": "Domingo"
        }

        # Crear los checkboxes de días en una columna
        for i, (day_key, day_name) in enumerate(day_names.items()):
            day_check = ttk.Checkbutton(
                days_frame,
                text=day_name,
                variable=self.days[day_key]
            )
            day_check.grid(row=i, column=0, sticky="w", padx=10, pady=2)

        # Frame para hora de envío diario
        daily_time_frame = ttk.LabelFrame(
            daily_frame,
            text="Hora de envío",
            padding="10 10 10 10"
        )
        daily_time_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        # Selector de hora para reportes diarios
        hour_values = [f"{i:02d}" for i in range(24)]
        hour_combo = ttk.Combobox(
            daily_time_frame,
            textvariable=self.hour,
            values=hour_values,
            width=5,
            state="readonly"
        )
        hour_combo.grid(row=0, column=0, sticky="e", padx=(0, 5))

        ttk.Label(daily_time_frame, text=":").grid(row=0, column=1)

        minute_values = [f"{i:02d}" for i in range(0, 60, 5)]
        minute_combo = ttk.Combobox(
            daily_time_frame,
            textvariable=self.minute,
            values=minute_values,
            width=5,
            state="readonly"
        )
        minute_combo.grid(row=0, column=2, sticky="w", padx=(5, 0))

        # ==== SECCIÓN DE REPORTES SEMANALES (COLUMNA DERECHA) ====
        weekly_frame = ttk.LabelFrame(
            main_frame,
            text="Configuración de Reportes Semanales",
            padding="15 15 15 15"
        )
        weekly_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        # Switch para activar/desactivar programación semanal
        weekly_enable_switch = ttk.Checkbutton(
            weekly_frame,
            text="Activar envío automático de reportes semanales",
            variable=self.weekly_enabled,
            command=self._toggle_weekly_scheduler
        )
        weekly_enable_switch.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Frame para día de la semana del reporte semanal
        weekly_day_frame = ttk.LabelFrame(
            weekly_frame,
            text="Día de envío semanal",
            padding="10 10 10 10"
        )
        weekly_day_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 15))

        # Combobox para seleccionar el día de la semana
        weekly_day_combo = ttk.Combobox(
            weekly_day_frame,
            textvariable=self.weekly_day,
            values=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            state="readonly",
            width=15
        )
        weekly_day_combo.grid(row=0, column=0, pady=5)

        # Establecer textos legibles para el combobox
        weekly_day_combo.configure(values=list(day_names.values()))

        # Mapeo inverso para convertir nombres legibles a claves
        self.day_keys = {v: k for k, v in day_names.items()}

        # Escuchar cambios en el combobox para actualizar la variable
        def on_weekly_day_change(event):
            selected_day_name = weekly_day_combo.get()
            if selected_day_name in self.day_keys:
                self.weekly_day.set(self.day_keys[selected_day_name])

        weekly_day_combo.bind("<<ComboboxSelected>>", on_weekly_day_change)

        # Establecer valor inicial visible
        for day_name, day_key in self.day_keys.items():
            if day_key == self.weekly_day.get():
                weekly_day_combo.set(day_name)
                break

        # Frame para hora de envío semanal
        weekly_time_frame = ttk.LabelFrame(
            weekly_frame,
            text="Hora de envío semanal",
            padding="10 10 10 10"
        )
        weekly_time_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        # Selector de hora para reportes semanales
        weekly_hour_combo = ttk.Combobox(
            weekly_time_frame,
            textvariable=self.weekly_hour,
            values=hour_values,
            width=5,
            state="readonly"
        )
        weekly_hour_combo.grid(row=0, column=0, sticky="e", padx=(0, 5))

        ttk.Label(weekly_time_frame, text=":").grid(row=0, column=1)

        weekly_minute_combo = ttk.Combobox(
            weekly_time_frame,
            textvariable=self.weekly_minute,
            values=minute_values,
            width=5,
            state="readonly"
        )
        weekly_minute_combo.grid(row=0, column=2, sticky="w", padx=(5, 0))

        # Explicación del reporte semanal
        weekly_note = ttk.Label(
            weekly_frame,
            text="El reporte semanal contiene datos acumulados de todos\nlos reportes diarios de la semana.",
            font=("Arial", 9),
            foreground="gray",
            justify="center"
        )
        weekly_note.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Nota explicativa general (abajo de todo, ocupa ambas columnas)
        note_label = ttk.Label(
            main_frame,
            text="Los reportes se generarán y enviarán automáticamente en los días y horas seleccionados.\nSe implementará prevención de duplicados para evitar envíos múltiples.",
            font=("Arial", 9),
            foreground="gray",
            justify="center"
        )
        note_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 20))

        # Botones (al fondo, centrados)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        save_btn = ttk.Button(
            button_frame,
            text="Guardar",
            command=self._save_config,
            width=15
        )
        save_btn.grid(row=0, column=0, padx=(0, 5), sticky="e")

        close_btn = ttk.Button(
            button_frame,
            text="Cerrar",
            command=self.modal.destroy,
            width=15
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="w")

        # Configurar estado inicial
        self._toggle_daily_scheduler()
        self._toggle_weekly_scheduler()

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_daily_scheduler(self):
        """Habilita/deshabilita los controles de programación diaria según el estado del switch."""
        state = "normal" if self.enabled.get() else "disabled"

        # Aplicar estado a todos los widgets de días diarios
        for child in self.modal.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame) and "Reportes Diarios" in grandchild["text"]:
                        for ggchild in grandchild.winfo_children():
                            if isinstance(ggchild, ttk.LabelFrame):
                                for gggchild in ggchild.winfo_children():
                                    if isinstance(gggchild, ttk.Checkbutton) or isinstance(gggchild, ttk.Combobox):
                                        gggchild.configure(state=state)

    def _toggle_weekly_scheduler(self):
        """Habilita/deshabilita los controles de programación semanal según el estado del switch."""
        state = "normal" if self.weekly_enabled.get() else "disabled"

        # Aplicar estado a todos los widgets de programación semanal
        for child in self.modal.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame) and "Reportes Semanales" in grandchild["text"]:
                        for ggchild in grandchild.winfo_children():
                            if isinstance(ggchild, (ttk.LabelFrame, ttk.Frame)):
                                for gggchild in ggchild.winfo_children():
                                    if isinstance(gggchild, (ttk.Checkbutton, ttk.Combobox)):
                                        gggchild.configure(state=state)

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                    # Cargar estado de reportes diarios
                    self.enabled.set(config.get("enabled", False))

                    # Cargar días
                    days_config = config.get("days", {})
                    for day in self.days:
                        self.days[day].set(days_config.get(day, False))

                    # Cargar hora
                    time_config = config.get("time", "08:00").split(":")
                    self.hour.set(time_config[0])
                    self.minute.set(time_config[1])

                    # Cargar configuración de reportes semanales
                    weekly_config = config.get("weekly", {})
                    self.weekly_enabled.set(weekly_config.get("enabled", False))
                    self.weekly_day.set(weekly_config.get("day", "friday"))

                    # Cargar hora semanal
                    weekly_time_config = weekly_config.get("time", "16:00").split(":")
                    self.weekly_hour.set(weekly_time_config[0])
                    self.weekly_minute.set(weekly_time_config[1])

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de programación cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de programación: {e}")

    def _save_config(self):
        """Guarda la configuración de programación."""
        # Validar configuración diaria
        if self.enabled.get():
            any_day_selected = any(self.days[day].get() for day in self.days)
            if not any_day_selected:
                messagebox.showerror("Error", "Debe seleccionar al menos un día de la semana para los reportes diarios")
                return

        # Crear configuración
        days_config = {day: self.days[day].get() for day in self.days}
        time_config = f"{self.hour.get()}:{self.minute.get()}"

        # Configuración de reportes semanales
        weekly_time_config = f"{self.weekly_hour.get()}:{self.weekly_minute.get()}"
        weekly_config = {
            "enabled": self.weekly_enabled.get(),
            "day": self.weekly_day.get(),
            "time": weekly_time_config
        }

        config = {
            "enabled": self.enabled.get(),
            "days": days_config,
            "time": time_config,
            "weekly": weekly_config,
            "last_update": datetime.now().isoformat()
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                log_message = []

                if self.enabled.get():
                    log_message.append("✅ Programación de reportes diarios activada")
                else:
                    log_message.append("✅ Programación de reportes diarios desactivada")

                if self.weekly_enabled.get():
                    log_message.append("✅ Programación de reportes semanales activada")
                else:
                    log_message.append("✅ Programación de reportes semanales desactivada")

                self.bottom_panel.add_log_entry(" y ".join(log_message))

            messagebox.showinfo("Éxito", "Configuración de programación guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar configuración: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)