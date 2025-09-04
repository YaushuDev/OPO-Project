# gui/components/scheduler_modal.py
"""
Modal para configurar programación de envío automático de reportes.
Permite seleccionar días de la semana y hora para envío automático.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from datetime import datetime


class SchedulerModal:
    """Modal para configurar programación de reportes."""

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de programación.

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
        self.modal.title("Programación de Reportes")
        self.modal.geometry("500x600")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variables para días de la semana
        self.days = {
            "monday": tk.BooleanVar(value=False),
            "tuesday": tk.BooleanVar(value=False),
            "wednesday": tk.BooleanVar(value=False),
            "thursday": tk.BooleanVar(value=False),
            "friday": tk.BooleanVar(value=False),
            "saturday": tk.BooleanVar(value=False),
            "sunday": tk.BooleanVar(value=False)
        }

        # Variables para hora
        self.hour = tk.StringVar(value="08")
        self.minute = tk.StringVar(value="00")

        # Variable para habilitar/deshabilitar programación
        self.enabled = tk.BooleanVar(value=False)

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
            text="⏰ Programación de Reportes",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Switch para activar/desactivar programación
        enable_frame = ttk.Frame(main_frame)
        enable_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        enable_switch = ttk.Checkbutton(
            enable_frame,
            text="Activar envío automático de reportes",
            variable=self.enabled,
            command=self._toggle_scheduler
        )
        enable_switch.pack(side=tk.LEFT)

        # Frame para días de la semana
        days_frame = ttk.LabelFrame(
            main_frame,
            text="Días de envío",
            padding="15 15 15 15"
        )
        days_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Checkboxes para días
        day_names = {
            "monday": "Lunes",
            "tuesday": "Martes",
            "wednesday": "Miércoles",
            "thursday": "Jueves",
            "friday": "Viernes",
            "saturday": "Sábado",
            "sunday": "Domingo"
        }

        # Crear 2 columnas de días
        for i, (day_key, day_name) in enumerate(day_names.items()):
            col = i % 2
            row = i // 2

            day_check = ttk.Checkbutton(
                days_frame,
                text=day_name,
                variable=self.days[day_key]
            )
            day_check.grid(row=row, column=col, sticky="w", padx=10, pady=5)

        # Configurar columnas de días
        days_frame.columnconfigure(0, weight=1)
        days_frame.columnconfigure(1, weight=1)

        # Frame para hora de envío
        time_frame = ttk.LabelFrame(
            main_frame,
            text="Hora de envío",
            padding="15 15 15 15"
        )
        time_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Selector de hora
        time_frame.columnconfigure(0, weight=1)
        time_frame.columnconfigure(1, weight=1)

        hour_values = [f"{i:02d}" for i in range(24)]
        hour_combo = ttk.Combobox(
            time_frame,
            textvariable=self.hour,
            values=hour_values,
            width=5,
            state="readonly"
        )
        hour_combo.grid(row=0, column=0, sticky="e", padx=(0, 5))

        ttk.Label(time_frame, text=":").grid(row=0, column=1, sticky="nsew")

        minute_values = [f"{i:02d}" for i in range(0, 60, 5)]
        minute_combo = ttk.Combobox(
            time_frame,
            textvariable=self.minute,
            values=minute_values,
            width=5,
            state="readonly"
        )
        minute_combo.grid(row=0, column=2, sticky="w", padx=(5, 0))

        # Nota explicativa
        note_label = ttk.Label(
            main_frame,
            text="Los reportes se generarán y enviarán automáticamente\nen los días y hora seleccionados.",
            font=("Arial", 9),
            foreground="gray",
            justify="center"
        )
        note_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        save_btn = ttk.Button(
            button_frame,
            text="Guardar",
            command=self._save_config
        )
        save_btn.grid(row=0, column=0, padx=(0, 5), sticky="e")

        close_btn = ttk.Button(
            button_frame,
            text="Cerrar",
            command=self.modal.destroy
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="w")

        # Configurar estado inicial
        self._toggle_scheduler()

        # Configurar columnas expandibles
        main_frame.columnconfigure(0, weight=1)

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_scheduler(self):
        """Habilita/deshabilita los controles según el estado del switch."""
        state = "normal" if self.enabled.get() else "disabled"

        # Aplicar estado a todos los widgets de días
        for widget in self.modal.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Checkbutton) or isinstance(grandchild, ttk.Combobox):
                                grandchild.configure(state=state)

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                    # Cargar estado
                    self.enabled.set(config.get("enabled", False))

                    # Cargar días
                    days_config = config.get("days", {})
                    for day in self.days:
                        self.days[day].set(days_config.get(day, False))

                    # Cargar hora
                    time_config = config.get("time", "08:00").split(":")
                    self.hour.set(time_config[0])
                    self.minute.set(time_config[1])

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de programación cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de programación: {e}")

    def _save_config(self):
        """Guarda la configuración de programación."""
        # Si está habilitado, verificar que haya al menos un día seleccionado
        if self.enabled.get():
            any_day_selected = any(self.days[day].get() for day in self.days)
            if not any_day_selected:
                messagebox.showerror("Error", "Debe seleccionar al menos un día de la semana")
                return

        # Crear configuración
        days_config = {day: self.days[day].get() for day in self.days}
        time_config = f"{self.hour.get()}:{self.minute.get()}"

        config = {
            "enabled": self.enabled.get(),
            "days": days_config,
            "time": time_config,
            "last_update": datetime.now().isoformat()
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                if self.enabled.get():
                    self.bottom_panel.add_log_entry("✅ Programación de reportes activada y guardada")
                else:
                    self.bottom_panel.add_log_entry("✅ Programación de reportes desactivada")

            messagebox.showinfo("Éxito", "Configuración de programación guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar configuración: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)