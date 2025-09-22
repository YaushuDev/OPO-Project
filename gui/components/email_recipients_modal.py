# gui/components/email_recipients_modal.py
"""
Modal de configuración de destinatarios de correo.
Permite configurar destinatario principal, CC y plantillas
de asunto personalizadas para reportes diarios, semanales y mensuales.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path

from services.email_config import (
    DEFAULT_SUBJECT_TEMPLATES,
    FREQUENCIES,
    FREQUENCY_DISPLAY_NAMES,
    normalize_recipients_config,
)


class EmailRecipientsModal:
    """Modal para configurar destinatarios de correo y plantillas de asunto."""

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de destinatarios.

        Args:
            parent: Widget padre
            bottom_panel: Referencia al panel para registrar logs
        """
        self.parent = parent
        self.bottom_panel = bottom_panel
        self.config_file = Path("config") / "email_recipients.json"

        # Crear directorio de configuración
        os.makedirs(Path("config"), exist_ok=True)

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Configuración de Envío de Correos")
        self.modal.geometry("520x720")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variables
        self.recipient_vars = {freq: tk.StringVar() for freq in FREQUENCIES}
        self.cc_vars = {freq: tk.StringVar() for freq in FREQUENCIES}
        self.subject_vars = {
            freq: tk.StringVar(value=DEFAULT_SUBJECT_TEMPLATES[freq])
            for freq in FREQUENCIES
        }

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
            text="📧 Configuración de Envío",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 25))

        row = 1
        for freq in FREQUENCIES:
            section = ttk.LabelFrame(
                main_frame,
                text=FREQUENCY_DISPLAY_NAMES[freq],
                padding="10 10 10 10"
            )
            section.grid(row=row, column=0, sticky="ew", pady=(0, 15))
            section.columnconfigure(0, weight=1)

            ttk.Label(
                section,
                text="Destinatario Principal:",
                font=("Arial", 10, "bold")
            ).grid(row=0, column=0, sticky="w")

            ttk.Entry(
                section,
                textvariable=self.recipient_vars[freq],
                width=50,
                font=("Arial", 10)
            ).grid(row=1, column=0, sticky="ew", pady=(0, 10))

            ttk.Label(
                section,
                text="CC (separar múltiples emails con coma):",
                font=("Arial", 10, "bold")
            ).grid(row=2, column=0, sticky="w")

            ttk.Entry(
                section,
                textvariable=self.cc_vars[freq],
                width=50,
                font=("Arial", 10)
            ).grid(row=3, column=0, sticky="ew")

            row += 1

        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=row, column=0, sticky="ew", pady=10)
        row += 1

        templates_title = ttk.Label(
            main_frame,
            text="Plantillas de Asunto",
            font=("Arial", 11, "bold"),
            foreground="navy"
        )
        templates_title.grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1

        for freq in FREQUENCIES:
            ttk.Label(
                main_frame,
                text=f"Plantilla para {FREQUENCY_DISPLAY_NAMES[freq]}:",
                font=("Arial", 10, "bold")
            ).grid(row=row, column=0, sticky="w", pady=(0, 5))
            row += 1

            ttk.Entry(
                main_frame,
                textvariable=self.subject_vars[freq],
                width=50,
                font=("Arial", 10)
            ).grid(row=row, column=0, sticky="ew", pady=(0, 15))
            row += 1

        note_label = ttk.Label(
            main_frame,
            text="Nota: Use {date} en el asunto para incluir la fecha actual",
            font=("Arial", 9),
            foreground="gray"
        )
        note_label.grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, sticky="ew")
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

        main_frame.columnconfigure(0, weight=1)

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    raw_config = json.load(file)
                    config = normalize_recipients_config(raw_config)

                    for freq in FREQUENCIES:
                        freq_config = config.get(freq, {})
                        self.recipient_vars[freq].set(freq_config.get("recipient", ""))
                        self.cc_vars[freq].set(freq_config.get("cc", ""))
                        self.subject_vars[freq].set(
                            freq_config.get("subject_template", DEFAULT_SUBJECT_TEMPLATES[freq])
                        )

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de destinatarios cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de destinatarios: {e}")

    def _save_config(self):
        """Guarda la configuración de destinatarios."""
        config = {}

        for freq in FREQUENCIES:
            recipient = self.recipient_vars[freq].get().strip()
            cc_value = self.cc_vars[freq].get().strip()
            subject_template = self.subject_vars[freq].get().strip()

            if not recipient:
                messagebox.showerror(
                    "Error",
                    f"El destinatario para {FREQUENCY_DISPLAY_NAMES[freq]} es obligatorio",
                )
                return

            if not self._validate_email(recipient):
                messagebox.showerror(
                    "Error",
                    f"El formato del destinatario para {FREQUENCY_DISPLAY_NAMES[freq]} no es válido",
                )
                return

            cleaned_cc = []
            if cc_value:
                for email in cc_value.split(","):
                    email = email.strip()
                    if not email:
                        continue
                    if not self._validate_email(email):
                        messagebox.showerror(
                            "Error",
                            f"El formato del email CC '{email}' en {FREQUENCY_DISPLAY_NAMES[freq]} no es válido",
                        )
                        return
                    cleaned_cc.append(email)

            if not subject_template:
                subject_template = DEFAULT_SUBJECT_TEMPLATES[freq]

            config[freq] = {
                "recipient": recipient,
                "cc": ", ".join(cleaned_cc) if cleaned_cc else "",
                "subject_template": subject_template,
            }

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

            if self.bottom_panel:
                self.bottom_panel.add_log_entry("✅ Configuración de destinatarios guardada")
            messagebox.showinfo("Éxito", "Configuración de destinatarios guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar configuración: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    def _validate_email(self, email):
        """
        Valida formato básico de email.

        Args:
            email (str): Email a validar

        Returns:
            bool: True si el formato es válido
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def get_config(self):
        """
        Retorna la configuración actual.

        Returns:
            dict: Configuración de destinatarios o None si no está configurada
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    raw_config = json.load(file)
                return normalize_recipients_config(raw_config)
            except Exception:
                return None
        return None
