# gui/components/bottom_left_panel.py
"""
Componente del panel inferior izquierdo del bot.
Maneja configuración SMTP y logs.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
from gui.components.smtp_modal import SMTPModal


class BottomLeftPanel:
    """Maneja el contenido y funcionalidad del panel de configuración."""

    def __init__(self, parent_frame):
        """
        Inicializa el panel inferior izquierdo.

        Args:
            parent_frame: Frame padre donde se montará este componente
        """
        self.parent_frame = parent_frame
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

        # Frame para controles
        self.controls_frame = ttk.Frame(self.parent_frame)
        self.controls_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.controls_frame.columnconfigure(0, weight=1)

        # Botón para configuración SMTP
        self.smtp_btn = ttk.Button(
            self.controls_frame,
            text="Configurar SMTP",
            command=self._open_smtp_modal
        )
        self.smtp_btn.grid(row=0, column=0, sticky="ew", pady=10)

        # Área de logs
        self.logs_frame = ttk.Frame(self.controls_frame)
        self.logs_frame.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.logs_frame.columnconfigure(0, weight=1)
        self.logs_frame.rowconfigure(1, weight=1)
        self.controls_frame.rowconfigure(1, weight=1)

        ttk.Label(self.logs_frame, text="Logs:", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # Listbox para logs
        self.logs_listbox = tk.Listbox(
            self.logs_frame,
            height=12,
            font=("Consolas", 8)
        )
        self.logs_listbox.grid(row=1, column=0, sticky="nsew")

        # Agregar scrollbar al listbox
        scrollbar = ttk.Scrollbar(
            self.logs_frame,
            orient="vertical",
            command=self.logs_listbox.yview
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.logs_listbox.configure(yscrollcommand=scrollbar.set)

        # Log inicial
        self._add_log("Panel inicializado")
        self._add_log("Esperando configuración SMTP")

    def _open_smtp_modal(self):
        """Abre el modal de configuración SMTP."""
        self._add_log("Abriendo configuración SMTP")
        smtp_modal = SMTPModal(self.parent_frame, self)

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

        # Mantener solo los últimos 100 logs
        if self.logs_listbox.size() > 100:
            self.logs_listbox.delete(0)

    def add_log_entry(self, message):
        """
        Método público para agregar logs desde otros componentes.

        Args:
            message (str): Mensaje a agregar al log
        """
        self._add_log(message)