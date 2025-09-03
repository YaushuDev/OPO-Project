# bottom_right_panel.py
"""
Componente del panel inferior derecho del bot.
Maneja información básica de estado y estadísticas simples.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class BottomRightPanel:
    """Maneja el contenido y funcionalidad del panel de estado."""

    def __init__(self, parent_frame):
        """
        Inicializa el panel inferior derecho.

        Args:
            parent_frame: Frame padre donde se montará este componente
        """
        self.parent_frame = parent_frame
        self.stats = {
            'start_time': datetime.now(),
            'status': 'Iniciado'
        }
        self._setup_widgets()
        self._start_update_timer()

    def _setup_widgets(self):
        """Configura los widgets del panel."""
        # Configurar expansión del frame
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(1, weight=1)

        # Título del panel
        self.title_label = ttk.Label(
            self.parent_frame,
            text="📊 ESTADO",
            font=("Arial", 10, "bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Frame principal para el contenido
        self.content_frame = ttk.Frame(self.parent_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.columnconfigure(1, weight=1)

        # Estado actual
        ttk.Label(self.content_frame, text="Estado:").grid(row=0, column=0, sticky="w", pady=5)
        self.status_label = ttk.Label(
            self.content_frame,
            text="✅ Activo",
            foreground="green"
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)

        # Tiempo activo
        ttk.Label(self.content_frame, text="Tiempo:").grid(row=1, column=0, sticky="w", pady=5)
        self.uptime_label = ttk.Label(self.content_frame, text="00:00:00")
        self.uptime_label.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)

        # Botones básicos
        self.buttons_frame = ttk.Frame(self.content_frame)
        self.buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)

        self.start_btn = ttk.Button(
            self.buttons_frame,
            text="▶ Iniciar",
            command=self._on_start
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.stop_btn = ttk.Button(
            self.buttons_frame,
            text="⏸ Pausar",
            command=self._on_stop
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew")

    def _start_update_timer(self):
        """Inicia el timer para actualizar el tiempo activo."""
        self._update_uptime()
        self.parent_frame.after(1000, self._start_update_timer)

    def _update_uptime(self):
        """Actualiza el tiempo de funcionamiento mostrado."""
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.uptime_label.config(text=uptime_str)

    def _on_start(self):
        """Callback para el botón de iniciar."""
        self.status_label.config(text="🔄 Ejecutando", foreground="orange")
        self.stats['status'] = 'Ejecutando'

    def _on_stop(self):
        """Callback para el botón de pausar."""
        self.status_label.config(text="⏸ Pausado", foreground="red")
        self.stats['status'] = 'Pausado'

    def update_status(self, status, color="black"):
        """
        Actualiza el estado del sistema.

        Args:
            status (str): Nuevo estado
            color (str): Color del texto
        """
        self.status_label.config(text=status, foreground=color)
        self.stats['status'] = status

    def get_stats(self):
        """
        Retorna las estadísticas actuales.

        Returns:
            dict: Estadísticas básicas
        """
        uptime = datetime.now() - self.stats['start_time']
        return {
            'uptime_seconds': int(uptime.total_seconds()),
            'status': self.stats['status']
        }