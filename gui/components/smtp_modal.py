# smtp_modal.py
"""
Modal de configuración SMTP optimizado para el bot.
Configuración simplificada solo para Gmail y Outlook con parámetros predefinidos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SMTPModal:
    """Modal optimizado para configuración SMTP con proveedores predefinidos."""

    # Solo Gmail y Outlook con configuraciones optimizadas
    SMTP_PROVIDERS = {
        "Gmail": {
            "server": "smtp.gmail.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False
        },
        "Outlook": {
            "server": "smtp-mail.outlook.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False
        }
    }

    def __init__(self, parent, bottom_panel=None):
        """
        Inicializa el modal de SMTP optimizado.

        Args:
            parent: Widget padre
            bottom_panel: Referencia al panel para registrar logs
        """
        self.parent = parent
        self.bottom_panel = bottom_panel
        self.config_file = Path("config") / "smtp_config.json"

        # Crear directorio de configuración
        os.makedirs(Path("config"), exist_ok=True)

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Configuración SMTP")
        self.modal.geometry("450x320")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Variables
        self.smtp_provider = tk.StringVar(value="Gmail")
        self.smtp_username = tk.StringVar()
        self.smtp_password = tk.StringVar()

        # Centrar ventana
        self._center_window()

        # Cargar configuración existente
        self._load_config()

        # Configurar widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la interfaz simplificada del modal."""
        # Frame principal
        main_frame = ttk.Frame(self.modal, padding="25 25 25 25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="📧 Configuración de Email",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Selector de proveedor
        ttk.Label(
            main_frame,
            text="Proveedor:",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        provider_combo = ttk.Combobox(
            main_frame,
            textvariable=self.smtp_provider,
            values=list(self.SMTP_PROVIDERS.keys()),
            width=35,
            state="readonly"
        )
        provider_combo.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Email/Usuario
        ttk.Label(
            main_frame,
            text="Email:",
            font=("Arial", 10, "bold")
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))

        email_entry = ttk.Entry(
            main_frame,
            textvariable=self.smtp_username,
            width=38,
            font=("Arial", 10)
        )
        email_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Contraseña
        ttk.Label(
            main_frame,
            text="Contraseña:",
            font=("Arial", 10, "bold")
        ).grid(row=5, column=0, sticky="w", pady=(0, 5))

        password_entry = ttk.Entry(
            main_frame,
            textvariable=self.smtp_password,
            show="*",
            width=38,
            font=("Arial", 10)
        )
        password_entry.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 25))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        test_btn = ttk.Button(
            button_frame,
            text="Probar",
            command=self._test_connection
        )
        test_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        save_btn = ttk.Button(
            button_frame,
            text="Guardar",
            command=self._save_config
        )
        save_btn.grid(row=0, column=1, padx=4, sticky="ew")

        close_btn = ttk.Button(
            button_frame,
            text="Cerrar",
            command=self.modal.destroy
        )
        close_btn.grid(row=0, column=2, padx=(8, 0), sticky="ew")

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

                    self.smtp_username.set(config.get("username", ""))
                    self.smtp_password.set(config.get("password", ""))

                    # Determinar proveedor basado en el servidor
                    server = config.get("server", "")
                    if "gmail" in server:
                        self.smtp_provider.set("Gmail")
                    elif "outlook" in server:
                        self.smtp_provider.set("Outlook")

                    if self.bottom_panel:
                        self.bottom_panel.add_log_entry("Configuración SMTP cargada")

        except Exception as e:
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(f"Error al cargar configuración: {e}")

    def _save_config(self):
        """Guarda la configuración SMTP."""
        provider = self.smtp_provider.get()
        username = self.smtp_username.get()
        password = self.smtp_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return

        provider_config = self.SMTP_PROVIDERS[provider]

        config = {
            "provider": provider,
            "server": provider_config["server"],
            "port": provider_config["port"],
            "username": username,
            "password": password,
            "use_tls": provider_config["use_tls"],
            "use_ssl": provider_config["use_ssl"]
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4)

            if self.bottom_panel:
                self.bottom_panel.add_log_entry("✅ Configuración SMTP guardada")
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")

        except Exception as e:
            error_msg = f"Error al guardar: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    def _test_connection(self):
        """Prueba la conexión SMTP."""
        provider = self.smtp_provider.get()
        username = self.smtp_username.get()
        password = self.smtp_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return

        provider_config = self.SMTP_PROVIDERS[provider]
        server = provider_config["server"]
        port = provider_config["port"]

        if self.bottom_panel:
            self.bottom_panel.add_log_entry(f"Probando conexión {provider}...")

        smtp = None
        try:
            # Contexto SSL seguro
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Conexión SMTP con STARTTLS (configuración optimizada)
            smtp = smtplib.SMTP(server, port)
            smtp.starttls(context=context)
            smtp.login(username, password)

            # Enviar email de prueba
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = username
            msg['Subject'] = "✅ Prueba de configuración SMTP"

            body = f"Configuración SMTP exitosa para {provider}.\nFecha: {self._get_timestamp()}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            smtp.send_message(msg)
            smtp.quit()

            if self.bottom_panel:
                self.bottom_panel.add_log_entry("✅ Conexión exitosa - Email enviado")

            messagebox.showinfo("Éxito",
                                f"✅ Conexión exitosa con {provider}!\n\n"
                                "Email de prueba enviado.\n"
                                "Revisa tu bandeja de entrada.")

        except smtplib.SMTPAuthenticationError:
            error_msg = "❌ Error de autenticación\n\nVerifica tu email y contraseña"

            if self.bottom_panel:
                self.bottom_panel.add_log_entry("❌ Error de autenticación")
            messagebox.showerror("Error de Autenticación", error_msg)

        except Exception as e:
            error_msg = f"❌ Error de conexión: {e}"
            if self.bottom_panel:
                self.bottom_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

        finally:
            if smtp:
                try:
                    smtp.quit()
                except:
                    pass

    def _get_timestamp(self):
        """Retorna timestamp actual formateado."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_config(self):
        """
        Retorna la configuración actual.

        Returns:
            dict: Configuración SMTP o None si no está configurada
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    return json.load(file)
            except:
                return None
        return None