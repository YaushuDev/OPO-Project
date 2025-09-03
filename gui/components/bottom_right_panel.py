# gui/components/bottom_right_panel.py
"""
Componente del panel inferior derecho del bot.
Muestra un log de eventos del sistema.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class BottomRightPanel:
    """Maneja el contenido y funcionalidad del panel de logs."""

    def __init__(self, parent_frame):
        """
        Inicializa el panel inferior derecho.

        Args:
            parent_frame: Frame padre donde se montará este componente
        """
        self.parent_frame = parent_frame
        self.start_time = datetime.now()
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura los widgets del panel."""
        # Configurar expansión del frame
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(1, weight=1)

        # Título del panel
        self.title_label = ttk.Label(
            self.parent_frame,
            text="📊 REGISTRO DE ACTIVIDAD",
            font=("Arial", 10, "bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Frame principal para el log
        self.log_frame = ttk.Frame(self.parent_frame)
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        # Crear área de log
        self.log_text = tk.Text(
            self.log_frame,
            height=10,
            width=30,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(
            self.log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Log inicial
        self.add_log_entry("Sistema iniciado")
        self.add_log_entry(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def add_log_entry(self, message):
        """
        Agrega un mensaje al log.

        Args:
            message (str): Mensaje a agregar al log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_log(self):
        """Limpia el contenido del log."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.add_log_entry("Log limpiado")