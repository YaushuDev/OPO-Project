# gui/components/bottom_left_panel.py
"""
Componente del panel inferior izquierdo del bot.
Maneja configuración SMTP y destinatarios de correo.
"""

import tkinter as tk
from tkinter import ttk
from gui.components.smtp_modal import SMTPModal
from gui.components.email_recipients_modal import EmailRecipientsModal


class BottomLeftPanel:
    """Maneja el contenido y funcionalidad del panel de configuración."""

    def __init__(self, parent_frame, bottom_right_panel=None):
        """
        Inicializa el panel inferior izquierdo.

        Args:
            parent_frame: Frame padre donde se montará este componente
            bottom_right_panel: Referencia al panel de logs para enviar mensajes
        """
        self.parent_frame = parent_frame
        self.bottom_right_panel = bottom_right_panel
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
            font=("Arial", 12, "bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(5, 20))

        # Frame para controles
        self.controls_frame = ttk.Frame(self.parent_frame)
        self.controls_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.controls_frame.columnconfigure(0, weight=1)
        self.controls_frame.rowconfigure(2, weight=1)

        # Botón para configuración SMTP
        self.smtp_btn = ttk.Button(
            self.controls_frame,
            text="Configurar SMTP",
            command=self._open_smtp_modal
        )
        self.smtp_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Botón para configurar destinatarios de correo
        self.email_recipients_btn = ttk.Button(
            self.controls_frame,
            text="Envío de Correos",
            command=self._open_email_recipients_modal
        )
        self.email_recipients_btn.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Espacio adicional para futuros controles
        self.additional_frame = ttk.Frame(self.controls_frame)
        self.additional_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        self.additional_frame.columnconfigure(0, weight=1)
        self.additional_frame.rowconfigure(0, weight=1)

        # Log inicial
        self._add_log("Panel de configuración inicializado")
        self._add_log("Configuración SMTP y correos disponible")

    def _open_smtp_modal(self):
        """Abre el modal de configuración SMTP."""
        self._add_log("Abriendo configuración SMTP")
        smtp_modal = SMTPModal(self.parent_frame, self)

    def _open_email_recipients_modal(self):
        """Abre el modal de configuración de destinatarios de correo."""
        self._add_log("Abriendo configuración de envío de correos")
        email_modal = EmailRecipientsModal(self.parent_frame, self)

    def _add_log(self, message):
        """
        Redirige el mensaje de log al panel derecho.

        Args:
            message (str): Mensaje a agregar
        """
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(message)

    def add_log_entry(self, message):
        """
        Método público para agregar logs desde otros componentes.

        Args:
            message (str): Mensaje a agregar al log
        """
        self._add_log(message)