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
        self.modal.geometry("480x520")  # Aumentamos altura para incluir plantilla mensual
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variables
        self.recipient_email = tk.StringVar()
        self.cc_emails = tk.StringVar()
        self.subject_template_daily = tk.StringVar(value="Reporte Diario de Búsqueda de Correos - {date}")
        self.subject_template_weekly = tk.StringVar(value="Reporte Semanal de Búsqueda de Correos - {date}")
        self.subject_template_monthly = tk.StringVar(value="Reporte Mensual de Búsqueda de Correos - {date}")

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
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Destinatario principal
        ttk.Label(
            main_frame,
            text="Destinatario Principal:",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        recipient_entry = ttk.Entry(
            main_frame,
            textvariable=self.recipient_email,
            width=50,
            font=("Arial", 10)
        )
        recipient_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # CC (opcional)
        ttk.Label(
            main_frame,
            text="CC (separar múltiples emails con coma):",
            font=("Arial", 10, "bold")
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))

        cc_entry = ttk.Entry(
            main_frame,
            textvariable=self.cc_emails,
            width=50,
            font=("Arial", 10)
        )
        cc_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Separador
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Título sección plantillas
        templates_title = ttk.Label(
            main_frame,
            text="Plantillas de Asunto",
            font=("Arial", 11, "bold"),
            foreground="navy"
        )
        templates_title.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Plantilla de asunto para reportes diarios
        ttk.Label(
            main_frame,
            text="Plantilla para Reportes Diarios:",
            font=("Arial", 10, "bold")
        ).grid(row=7, column=0, sticky="w", pady=(0, 5))

        daily_subject_entry = ttk.Entry(
            main_frame,
            textvariable=self.subject_template_daily,
            width=50,
            font=("Arial", 10)
        )
        daily_subject_entry.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Plantilla de asunto para reportes semanales
        ttk.Label(
            main_frame,
            text="Plantilla para Reportes Semanales:",
            font=("Arial", 10, "bold")
        ).grid(row=9, column=0, sticky="w", pady=(0, 5))

        weekly_subject_entry = ttk.Entry(
            main_frame,
            textvariable=self.subject_template_weekly,
            width=50,
            font=("Arial", 10)
        )
        weekly_subject_entry.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Plantilla de asunto para reportes mensuales
        ttk.Label(
            main_frame,
            text="Plantilla para Reportes Mensuales:",
            font=("Arial", 10, "bold")
        ).grid(row=11, column=0, sticky="w", pady=(0, 5))

        monthly_subject_entry = ttk.Entry(
            main_frame,
            textvariable=self.subject_template_monthly,
            width=50,
            font=("Arial", 10)
        )
        monthly_subject_entry.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Nota explicativa
        note_label = ttk.Label(
            main_frame,
            text="Nota: Use {date} en el asunto para incluir la fecha actual",
            font=("Arial", 9),
            foreground="gray"
        )
        note_label.grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=14, column=0, columnspan=2, sticky="ew")
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

    def _load_config(self):
        """Carga configuración guardada."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config = json.load(file)

                    self.recipient_email.set(config.get("recipient", ""))
                    self.cc_emails.set(config.get("cc", ""))

                    # Cargar plantillas de asunto
                    self.subject_template_daily.set(
                        config.get("subject_template_daily", "Reporte Diario de Búsqueda de Correos - {date}")
                    )
                    self.subject_template_weekly.set(
                        config.get("subject_template_weekly", "Reporte Semanal de Búsqueda de Correos - {date}")
                    )
                    self.subject_template_monthly.set(
                        config.get("subject_template_monthly", "Reporte Mensual de Búsqueda de Correos - {date}")
                    )

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración de destinatarios cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración de destinatarios: {e}")

    def _save_config(self):
        """Guarda la configuración de destinatarios."""
        recipient = self.recipient_email.get().strip()
        cc = self.cc_emails.get().strip()
        subject_daily = self.subject_template_daily.get().strip()
        subject_weekly = self.subject_template_weekly.get().strip()
        subject_monthly = self.subject_template_monthly.get().strip()

        if not recipient:
            messagebox.showerror("Error", "El destinatario principal es obligatorio")
            return

        # Validar formato de email del destinatario principal
        if not self._validate_email(recipient):
            messagebox.showerror("Error", "El formato del destinatario principal no es válido")
            return

        # Validar emails CC si se proporcionaron
        if cc:
            cc_list = [email.strip() for email in cc.split(",")]
            for email in cc_list:
                if email and not self._validate_email(email):
                    messagebox.showerror("Error", f"El formato del email CC '{email}' no es válido")
                    return

        # Validar que las plantillas de asunto no estén vacías
        if not subject_daily:
            subject_daily = "Reporte Diario de Búsqueda de Correos - {date}"

        if not subject_weekly:
            subject_weekly = "Reporte Semanal de Búsqueda de Correos - {date}"

        if not subject_monthly:
            subject_monthly = "Reporte Mensual de Búsqueda de Correos - {date}"

        config = {
            "recipient": recipient,
            "cc": cc,
            "subject_template_daily": subject_daily,
            "subject_template_weekly": subject_weekly,
            "subject_template_monthly": subject_monthly
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
                    return json.load(file)
            except:
                return None
        return None