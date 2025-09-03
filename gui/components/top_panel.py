# top_panel.py
"""
Componente del panel superior del bot.
Área principal para el contenido del bot.
"""

import tkinter as tk
from tkinter import ttk


class TopPanel:
    """Maneja el contenido y funcionalidad del panel superior."""

    def __init__(self, parent_frame):
        """
        Inicializa el panel superior.

        Args:
            parent_frame: Frame padre donde se montará este componente
        """
        self.parent_frame = parent_frame
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura los widgets del panel superior."""
        # Configurar expansión del frame
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)

        # Contenedor principal
        self.main_container = ttk.Frame(self.parent_frame)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=1)

        # Placeholder simple
        self.placeholder_label = ttk.Label(
            self.main_container,
            text="🤖 ÁREA PRINCIPAL\n\nContenido del bot aquí...",
            font=("Arial", 12),
            anchor="center",
            justify="center"
        )
        self.placeholder_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def get_data(self):
        """
        Retorna los datos actuales del panel.

        Returns:
            dict: Información del panel
        """
        return {"panel_type": "top_panel"}