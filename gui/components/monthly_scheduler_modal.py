# monthly_scheduler_modal.py
"""
Modal especializado para configurar programación de envío automático de reportes mensuales.
Permite configurar día del mes y hora para el envío de reportes mensuales consolidados
con análisis comparativo y métricas acumuladas del mes completo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from datetime import datetime
import calendar


class MonthlySchedulerModal:
    """Modal para configuración específica de reportes mensuales programados."""

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de programación mensual.

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
        self.modal.title("Programación de Reportes Mensuales")
        self.modal.geometry("500x590")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variable para habilitar/deshabilitar programación mensual
        self.monthly_enabled = tk.BooleanVar(value=False)

        # Variable para día del mes del reporte mensual
        self.monthly_day_type = tk.StringVar(value="specific")  # "specific" o "last"
        self.monthly_day = tk.StringVar(value="1")

        # Variables para hora del reporte mensual
        self.monthly_hour = tk.StringVar(value="09")
        self.monthly_minute = tk.StringVar(value="00")

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
            text="📅 Programación de Reportes Mensuales",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Switch para activar/desactivar programación mensual
        monthly_enable_switch = ttk.Checkbutton(
            main_frame,
            text="Activar envío automático de reportes mensuales",
            variable=self.monthly_enabled,
            command=self._toggle_monthly_scheduler
        )
        monthly_enable_switch.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Frame para configuración del día del mes
        monthly_day_frame = ttk.LabelFrame(
            main_frame,
            text="Día de envío mensual",
            padding="15 15 15 15"
        )
        monthly_day_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        ttk.Label(
            monthly_day_frame,
            text="Seleccione cuándo enviar el reporte mensual:",
            font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 15))

        # Radio buttons para tipo de día
        day_type_frame = ttk.Frame(monthly_day_frame)
        day_type_frame.pack(fill=tk.X, pady=(0, 10))

        specific_day_radio = ttk.Radiobutton(
            day_type_frame,
            text="Día específico del mes",
            variable=self.monthly_day_type,
            value="specific",
            command=self._update_day_selection
        )
        specific_day_radio.grid(row=0, column=0, sticky="w", padx=(0, 15))

        last_day_radio = ttk.Radiobutton(
            day_type_frame,
            text="Último día del mes",
            variable=self.monthly_day_type,
            value="last",
            command=self._update_day_selection
        )
        last_day_radio.grid(row=0, column=1, sticky="w")

        # Frame para selector de día específico
        self.specific_day_frame = ttk.Frame(monthly_day_frame)
        self.specific_day_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(
            self.specific_day_frame,
            text="Día del mes:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Crear combobox con días del mes (1-31)
        day_values = [str(i) for i in range(1, 32)]
        self.day_combo = ttk.Combobox(
            self.specific_day_frame,
            textvariable=self.monthly_day,
            values=day_values,
            width=5,
            state="readonly"
        )
        self.day_combo.pack(side=tk.LEFT)

        # Nota sobre días inválidos
        ttk.Label(
            monthly_day_frame,
            text="Nota: Si selecciona un día que no existe en algún mes (ej: 31 de febrero),\n"
                 "el sistema automáticamente utilizará el último día de ese mes.",
            font=("Arial", 9),
            foreground="gray",
            justify="center"
        ).pack(fill=tk.X, pady=(15, 0))

        # Frame para hora de envío mensual
        monthly_time_frame = ttk.LabelFrame(
            main_frame,
            text="Hora de envío mensual",
            padding="15 15 15 15"
        )
        monthly_time_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        ttk.Label(
            monthly_time_frame,
            text="Seleccione la hora para enviar el reporte mensual:",
            font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 10))

        # Selector de hora para reportes mensuales
        time_selector_frame = ttk.Frame(monthly_time_frame)
        time_selector_frame.pack(fill=tk.X)

        ttk.Label(
            time_selector_frame,
            text="Hora:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        hour_values = [f"{i:02d}" for i in range(24)]
        monthly_hour_combo = ttk.Combobox(
            time_selector_frame,
            textvariable=self.monthly_hour,
            values=hour_values,
            width=5,
            state="readonly"
        )
        monthly_hour_combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(time_selector_frame, text=":").pack(side=tk.LEFT)

        minute_values = [f"{i:02d}" for i in range(0, 60, 5)]
        monthly_minute_combo = ttk.Combobox(
            time_selector_frame,
            textvariable=self.monthly_minute,
            values=minute_values,
            width=5,
            state="readonly"
        )
        monthly_minute_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Explicación del reporte mensual
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        info_label = ttk.Label(
            info_frame,
            text="Los reportes mensuales contienen un análisis completo del rendimiento\n"
                 "durante el mes, con métricas acumuladas, tendencias mensuales\n"
                 "y comparativas de éxito para cada perfil de búsqueda.",
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
        self._toggle_monthly_scheduler()
        self._update_day_selection()

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_monthly_scheduler(self):
        """Habilita/deshabilita los controles de programación mensual según el estado del switch."""
        state = "normal" if self.monthly_enabled.get() else "disabled"

        # Aplicar estado a todos los widgets de programación mensual
        for child in self.modal.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame):
                        for ggchild in grandchild.winfo_children():
                            if isinstance(ggchild, (ttk.Checkbutton, ttk.Combobox, ttk.Frame, ttk.Radiobutton)):
                                if isinstance(ggchild, ttk.Frame):
                                    for gggchild in ggchild.winfo_children():
                                        if isinstance(gggchild, (ttk.Checkbutton, ttk.Combobox, ttk.Radiobutton)):
                                            gggchild.configure(state=state)
                                else:
                                    ggchild.configure(state=state)

    def _update_day_selection(self):
        """Actualiza la interfaz según el tipo de día seleccionado."""
        if self.monthly_day_type.get() == "specific":
            self.specific_day_frame.pack(fill=tk.X, pady=(5, 0))
            self.day_combo.configure(state="readonly" if self.monthly_enabled.get() else "disabled")
        else:
            self.specific_day_frame.pack_forget()

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                    # Cargar configuración de reportes mensuales
                    monthly_config = config.get("monthly", {})
                    self.monthly_enabled.set(monthly_config.get("enabled", False))

                    # Determinar tipo de día y día específico
                    monthly_day = monthly_config.get("day", "1")
                    if monthly_day == "last":
                        self.monthly_day_type.set("last")
                    else:
                        self.monthly_day_type.set("specific")
                        self.monthly_day.set(str(monthly_day))

                    # Cargar hora mensual
                    monthly_time_config = monthly_config.get("time", "09:00").split(":")
                    self.monthly_hour.set(monthly_time_config[0])
                    self.monthly_minute.set(monthly_time_config[1])

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de programación mensual cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de programación mensual: {e}")

    def _save_config(self):
        """Guarda la configuración de programación mensual."""
        # Configuración de reportes mensuales
        monthly_time_config = f"{self.monthly_hour.get()}:{self.monthly_minute.get()}"

        # Determinar el valor del día según el tipo seleccionado
        if self.monthly_day_type.get() == "last":
            day_value = "last"
        else:
            # Validar que el día sea un número entre 1 y 31
            try:
                day_num = int(self.monthly_day.get())
                if 1 <= day_num <= 31:
                    day_value = str(day_num)
                else:
                    messagebox.showerror("Error", "El día del mes debe estar entre 1 y 31")
                    return
            except ValueError:
                messagebox.showerror("Error", "El día del mes debe ser un número válido")
                return

        monthly_config = {
            "enabled": self.monthly_enabled.get(),
            "day": day_value,
            "time": monthly_time_config
        }

        # Cargar configuración existente para no perder otros valores
        try:
            existing_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    existing_config = json.load(file)
        except Exception:
            existing_config = {}

        # Actualizar solo la parte de configuración mensual
        config = existing_config
        config["monthly"] = monthly_config
        config["last_update"] = datetime.now().isoformat()

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                if self.monthly_enabled.get():
                    day_display = "último día del mes" if day_value == "last" else f"día {day_value}"
                    self.bottom_panel.add_log_entry(
                        f"✅ Programación de reportes mensuales activada ({day_display}, {monthly_time_config})"
                    )
                else:
                    self.bottom_panel.add_log_entry("✅ Programación de reportes mensuales desactivada")

            messagebox.showinfo("Éxito", "Configuración de programación mensual guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar configuración: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    def get_config(self):
        """
        Retorna la configuración actual de programación mensual.

        Returns:
            dict: Configuración de programación mensual
        """
        # Determinar el valor del día según el tipo seleccionado
        if self.monthly_day_type.get() == "last":
            day_value = "last"
        else:
            day_value = self.monthly_day.get()

        return {
            "enabled": self.monthly_enabled.get(),
            "day": day_value,
            "time": f"{self.monthly_hour.get()}:{self.monthly_minute.get()}"
        }