# weekly_scheduler_modal.py
"""
Modal especializado para configurar programación de envío automático de reportes semanales.
Permite configurar día de la semana y hora para el envío de reportes semanales consolidados
con análisis comparativo y métricas acumuladas de la semana.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from datetime import datetime


class WeeklySchedulerModal:
    """Modal para configuración específica de reportes semanales programados."""

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de programación semanal.

        Args:
            parent: Widget padre
            bottom_panel: Referencia al panel para registrar logs
        """
        self.parent = parent
        self.bottom_panel = bottom_panel
        self.config_file = Path("config") / "scheduler_config.json"

        # Crear directorio de configuración
        os.makedirs(Path("config"), exist_ok=True)

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Programación de Reportes Semanales")
        self.modal.geometry("500x570")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variable para habilitar/deshabilitar programación semanal
        self.weekly_enabled = tk.BooleanVar(value=False)

        # Variable para día de la semana del reporte semanal
        self.weekly_day = tk.StringVar(value="friday")

        # Variables para hora del reporte semanal
        self.weekly_hour = tk.StringVar(value="16")
        self.weekly_minute = tk.StringVar(value="00")

        # Mapeo de días con nombres en español
        self.day_names = {
            "monday": "Lunes",
            "tuesday": "Martes",
            "wednesday": "Miércoles",
            "thursday": "Jueves",
            "friday": "Viernes",
            "saturday": "Sábado",
            "sunday": "Domingo"
        }

        # Mapeo inverso para convertir nombres legibles a claves
        self.day_keys = {v: k for k, v in self.day_names.items()}

        # Centrar ventana
        self._center_window()

        # Cargar configuración existente
        self._load_config()

        # Configurar widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la interfaz del modal."""
        # Frame principal
        main_frame = ttk.Frame(self.modal, padding="25 25 25 25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="📊 Programación de Reportes Semanales",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Switch para activar/desactivar programación semanal
        weekly_enable_switch = ttk.Checkbutton(
            main_frame,
            text="Activar envío automático de reportes semanales",
            variable=self.weekly_enabled,
            command=self._toggle_weekly_scheduler
        )
        weekly_enable_switch.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Frame para día de la semana del reporte semanal
        weekly_day_frame = ttk.LabelFrame(
            main_frame,
            text="Día de envío semanal",
            padding="15 15 15 15"
        )
        weekly_day_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        ttk.Label(
            weekly_day_frame,
            text="Seleccione el día de la semana para enviar el reporte consolidado:",
            font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 10))

        # Combobox para seleccionar el día de la semana
        day_selector_frame = ttk.Frame(weekly_day_frame)
        day_selector_frame.pack(fill=tk.X)

        ttk.Label(
            day_selector_frame,
            text="Día:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        weekly_day_combo = ttk.Combobox(
            day_selector_frame,
            values=list(self.day_names.values()),
            state="readonly",
            width=20
        )
        weekly_day_combo.pack(side=tk.LEFT)

        # Establecer valor inicial visible
        for day_name, day_key in self.day_keys.items():
            if day_key == self.weekly_day.get():
                weekly_day_combo.set(day_name)
                break

        # Escuchar cambios en el combobox para actualizar la variable
        def on_weekly_day_change(event):
            selected_day_name = weekly_day_combo.get()
            if selected_day_name in self.day_keys:
                self.weekly_day.set(self.day_keys[selected_day_name])

        weekly_day_combo.bind("<<ComboboxSelected>>", on_weekly_day_change)

        # Frame para hora de envío semanal
        weekly_time_frame = ttk.LabelFrame(
            main_frame,
            text="Hora de envío semanal",
            padding="15 15 15 15"
        )
        weekly_time_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        ttk.Label(
            weekly_time_frame,
            text="Seleccione la hora para enviar el reporte semanal:",
            font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 10))

        # Selector de hora para reportes semanales
        time_selector_frame = ttk.Frame(weekly_time_frame)
        time_selector_frame.pack(fill=tk.X)

        ttk.Label(
            time_selector_frame,
            text="Hora:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        hour_values = [f"{i:02d}" for i in range(24)]
        weekly_hour_combo = ttk.Combobox(
            time_selector_frame,
            textvariable=self.weekly_hour,
            values=hour_values,
            width=5,
            state="readonly"
        )
        weekly_hour_combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(time_selector_frame, text=":").pack(side=tk.LEFT)

        minute_values = [f"{i:02d}" for i in range(0, 60, 5)]
        weekly_minute_combo = ttk.Combobox(
            time_selector_frame,
            textvariable=self.weekly_minute,
            values=minute_values,
            width=5,
            state="readonly"
        )
        weekly_minute_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Explicación del reporte semanal
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        info_label = ttk.Label(
            info_frame,
            text="Los reportes semanales contienen datos acumulados y análisis comparativo\n"
                 "de todos los reportes diarios de la semana, con métricas consolidadas\n"
                 "y cálculo correcto de porcentajes de éxito semanal.",
            font=("Arial", 9),
            foreground="gray",
            justify="center"
        )
        info_label.pack(fill=tk.X)

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
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

        # Aplicar estado inicial
        self._toggle_weekly_scheduler()

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_weekly_scheduler(self):
        """Habilita/deshabilita los controles de programación semanal según el estado del switch."""
        state = "normal" if self.weekly_enabled.get() else "disabled"

        # Aplicar estado a todos los widgets de programación semanal
        for child in self.modal.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame):
                        for ggchild in grandchild.winfo_children():
                            if isinstance(ggchild, (ttk.Checkbutton, ttk.Combobox, ttk.Frame)):
                                if isinstance(ggchild, ttk.Frame):
                                    for gggchild in ggchild.winfo_children():
                                        if isinstance(gggchild, (ttk.Checkbutton, ttk.Combobox)):
                                            gggchild.configure(state=state)
                                else:
                                    ggchild.configure(state=state)

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                    # Cargar configuración de reportes semanales
                    weekly_config = config.get("weekly", {})
                    self.weekly_enabled.set(weekly_config.get("enabled", False))
                    self.weekly_day.set(weekly_config.get("day", "friday"))

                    # Cargar hora semanal
                    weekly_time_config = weekly_config.get("time", "16:00").split(":")
                    self.weekly_hour.set(weekly_time_config[0])
                    self.weekly_minute.set(weekly_time_config[1])

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de programación semanal cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de programación semanal: {e}")

    def _save_config(self):
        """Guarda la configuración de programación semanal."""
        # Validación específica para programación semanal
        if not self.weekly_day.get():
            messagebox.showerror("Error", "Debe seleccionar un día de la semana")
            return

        # Configuración de reportes semanales
        weekly_time_config = f"{self.weekly_hour.get()}:{self.weekly_minute.get()}"
        weekly_config = {
            "enabled": self.weekly_enabled.get(),
            "day": self.weekly_day.get(),
            "time": weekly_time_config
        }

        # Cargar configuración existente para no perder otros valores
        try:
            existing_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    existing_config = json.load(file)
        except Exception:
            existing_config = {}

        # Actualizar solo la parte de configuración semanal
        config = existing_config
        config["weekly"] = weekly_config
        config["last_update"] = datetime.now().isoformat()

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                if self.weekly_enabled.get():
                    day_name = self.day_names.get(self.weekly_day.get(), self.weekly_day.get())
                    self.bottom_panel.add_log_entry(
                        f"✅ Programación de reportes semanales activada ({day_name}, {weekly_time_config})"
                    )
                else:
                    self.bottom_panel.add_log_entry("✅ Programación de reportes semanales desactivada")

            messagebox.showinfo("Éxito", "Configuración de programación semanal guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar configuración: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    def get_config(self):
        """
        Retorna la configuración actual de programación semanal.

        Returns:
            dict: Configuración de programación semanal
        """
        return {
            "enabled": self.weekly_enabled.get(),
            "day": self.weekly_day.get(),
            "time": f"{self.weekly_hour.get()}:{self.weekly_minute.get()}"
        }