# bottom_left_panel.py
"""
Componente del panel inferior izquierdo del bot.
Maneja configuraciones básicas y logs simples.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class BottomLeftPanel:
    """Maneja el contenido y funcionalidad del panel de configuración."""

    def __init__(self, parent_frame):
        """
        Inicializa el panel inferior izquierdo.

        Args:
            parent_frame: Frame padre donde se montará este componente
        """
        self.parent_frame = parent_frame
        self.config_vars = {}
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura los widgets del panel."""
        # Configurar expansión del frame
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(1, weight=1)

        # Título del panel
        self.title_label = ttk.Label(
            self.parent_frame,
            text="⚙️ CONFIGURACIÓN",
            font=("Arial", 10, "bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Frame para controles básicos
        self.controls_frame = ttk.Frame(self.parent_frame)
        self.controls_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.controls_frame.columnconfigure(0, weight=1)

        # Variables básicas de configuración
        self.config_vars['auto_mode'] = tk.BooleanVar(value=False)
        self.config_vars['debug_mode'] = tk.BooleanVar(value=True)

        # Checkbox para modo automático
        self.auto_mode_check = ttk.Checkbutton(
            self.controls_frame,
            text="Modo Automático",
            variable=self.config_vars['auto_mode']
        )
        self.auto_mode_check.grid(row=0, column=0, sticky="w", pady=5)

        # Checkbox para modo debug
        self.debug_mode_check = ttk.Checkbutton(
            self.controls_frame,
            text="Modo Debug",
            variable=self.config_vars['debug_mode']
        )
        self.debug_mode_check.grid(row=1, column=0, sticky="w", pady=5)

        # Área de logs simple
        self.logs_frame = ttk.Frame(self.controls_frame)
        self.logs_frame.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        self.logs_frame.columnconfigure(0, weight=1)
        self.logs_frame.rowconfigure(1, weight=1)
        self.controls_frame.rowconfigure(2, weight=1)

        ttk.Label(self.logs_frame, text="Logs:", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # Listbox simple para logs
        self.logs_listbox = tk.Listbox(
            self.logs_frame,
            height=8,
            font=("Consolas", 8)
        )
        self.logs_listbox.grid(row=1, column=0, sticky="nsew")

        # Log inicial
        self._add_log("Panel inicializado")

    def _add_log(self, message):
        """
        Agrega un mensaje al log.

        Args:
            message (str): Mensaje a agregar
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.logs_listbox.insert(tk.END, log_entry)
        self.logs_listbox.see(tk.END)

        # Mantener solo los últimos 20 logs
        if self.logs_listbox.size() > 20:
            self.logs_listbox.delete(0)

    def get_config(self):
        """
        Retorna la configuración actual del panel.

        Returns:
            dict: Configuración actual
        """
        return {
            'auto_mode': self.config_vars['auto_mode'].get(),
            'debug_mode': self.config_vars['debug_mode'].get()
        }

    def add_log_entry(self, message):
        """
        Método público para agregar logs desde otros componentes.

        Args:
            message (str): Mensaje a agregar al log
        """
        self._add_log(message)