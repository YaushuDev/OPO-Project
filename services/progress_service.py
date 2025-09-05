# progress_service.py
"""
Servicio centralizado para manejo de progreso y indicadores visuales.
Previene bloqueos de UI durante operaciones pesadas con threading optimizado.
"""

import tkinter as tk
from tkinter import ttk
import threading
import queue
from datetime import datetime


class ProgressService:
    """Servicio para manejo de operaciones asíncronas con indicadores de progreso."""

    def __init__(self, parent_widget, log_callback=None):
        """
        Inicializa el servicio de progreso.

        Args:
            parent_widget: Widget padre para mostrar progreso
            log_callback: Función para logs
        """
        self.parent_widget = parent_widget
        self.log_callback = log_callback
        self.progress_window = None
        self.progress_bar = None
        self.status_label = None
        self.cancel_requested = False
        self.current_operation = None

        # Queue para comunicación thread-safe
        self.update_queue = queue.Queue()

        # Configurar verificación periódica de updates
        self._check_updates()

    def _check_updates(self):
        """Verifica actualizaciones del queue de manera thread-safe."""
        try:
            while True:
                update_type, data = self.update_queue.get_nowait()

                if update_type == "progress":
                    self._update_progress_bar(data["value"], data["text"])
                elif update_type == "log":
                    if self.log_callback:
                        self.log_callback(data)
                elif update_type == "complete":
                    self._complete_operation(data)
                elif update_type == "error":
                    self._handle_error(data)

        except queue.Empty:
            pass

        # Programar próxima verificación
        if self.parent_widget.winfo_exists():
            self.parent_widget.after(100, self._check_updates)

    def start_operation(self, title, max_steps=100, can_cancel=True):
        """
        Inicia una operación con indicador de progreso.

        Args:
            title (str): Título de la operación
            max_steps (int): Número máximo de pasos
            can_cancel (bool): Si se puede cancelar la operación
        """
        self.cancel_requested = False
        self.current_operation = title

        # Crear ventana de progreso
        self._create_progress_window(title, can_cancel)

        # Log inicial
        self._queue_log(f"🚀 Iniciando: {title}")

    def _create_progress_window(self, title, can_cancel):
        """Crea la ventana de progreso."""
        if self.progress_window:
            self.progress_window.destroy()

        self.progress_window = tk.Toplevel(self.parent_widget)
        self.progress_window.title("Operación en Progreso")
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        self.progress_window.transient(self.parent_widget)
        self.progress_window.grab_set()

        # Centrar ventana
        self._center_progress_window()

        # Frame principal
        main_frame = ttk.Frame(self.progress_window, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text=title,
            font=("Arial", 11, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode="determinate",
            length=350
        )
        self.progress_bar.pack(pady=(0, 10))

        # Etiqueta de estado
        self.status_label = ttk.Label(
            main_frame,
            text="Preparando...",
            font=("Arial", 9)
        )
        self.status_label.pack(pady=(0, 15))

        # Botón cancelar (opcional)
        if can_cancel:
            cancel_btn = ttk.Button(
                main_frame,
                text="Cancelar",
                command=self._request_cancel
            )
            cancel_btn.pack()

    def _center_progress_window(self):
        """Centra la ventana de progreso."""
        self.progress_window.update_idletasks()
        width = self.progress_window.winfo_width()
        height = self.progress_window.winfo_height()
        x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (height // 2)
        self.progress_window.geometry(f"{width}x{height}+{x}+{y}")

    def update_progress(self, current_step, total_steps, status_text):
        """
        Actualiza el progreso de manera thread-safe.

        Args:
            current_step (int): Paso actual
            total_steps (int): Total de pasos
            status_text (str): Texto de estado
        """
        if total_steps > 0:
            percentage = (current_step / total_steps) * 100
        else:
            percentage = 0

        self.update_queue.put(("progress", {
            "value": percentage,
            "text": status_text
        }))

    def _update_progress_bar(self, percentage, text):
        """Actualiza la barra de progreso en el hilo principal."""
        if self.progress_bar and self.status_label:
            self.progress_bar["value"] = percentage
            self.status_label.config(text=text)

    def log_progress(self, message):
        """Envía log de manera thread-safe."""
        self._queue_log(message)

    def _queue_log(self, message):
        """Encola mensaje de log."""
        self.update_queue.put(("log", message))

    def complete_operation(self, success_message):
        """
        Completa la operación exitosamente.

        Args:
            success_message (str): Mensaje de éxito
        """
        self.update_queue.put(("complete", {
            "success": True,
            "message": success_message
        }))

    def error_operation(self, error_message):
        """
        Marca la operación como fallida.

        Args:
            error_message (str): Mensaje de error
        """
        self.update_queue.put(("error", error_message))

    def _complete_operation(self, data):
        """Completa la operación en el hilo principal."""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

        if self.log_callback:
            if data["success"]:
                self.log_callback(f"✅ {data['message']}")
            else:
                self.log_callback(f"❌ Error: {data['message']}")

    def _handle_error(self, error_message):
        """Maneja errores en el hilo principal."""
        self._complete_operation({
            "success": False,
            "message": error_message
        })

    def _request_cancel(self):
        """Solicita cancelación de la operación."""
        self.cancel_requested = True
        self._queue_log("🛑 Cancelación solicitada...")

    def is_cancelled(self):
        """Verifica si se solicitó cancelación."""
        return self.cancel_requested

    def cleanup(self):
        """Limpia recursos del servicio."""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None