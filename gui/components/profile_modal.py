# gui/components/profile_modal.py
"""
Modal para crear o editar perfiles de búsqueda.
Permite configurar nombre y criterios de búsqueda.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ProfileModal:
    """Modal para gestionar perfiles de búsqueda."""

    def __init__(self, parent, profile_manager, profile=None, callback=None):
        """
        Inicializa el modal de perfil.

        Args:
            parent: Widget padre
            profile_manager: Gestor de perfiles
            profile (SearchProfile, optional): Perfil a editar. Si es None, se crea uno nuevo.
            callback: Función a llamar después de guardar/actualizar
        """
        self.parent = parent
        self.profile_manager = profile_manager
        self.profile = profile
        self.callback = callback
        self.edit_mode = profile is not None

        # Variables
        self.profile_name = tk.StringVar(value=profile.name if profile else "")
        self.search_criteria = tk.StringVar(value=profile.search_criteria if profile else "")

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Editar Perfil" if self.edit_mode else "Nuevo Perfil")
        self.modal.geometry("450x250")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()

        # Centrar ventana
        self._center_window()

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
            text="🔍 " + ("Editar Perfil de Búsqueda" if self.edit_mode else "Nuevo Perfil de Búsqueda"),
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Nombre del perfil
        ttk.Label(
            main_frame,
            text="Nombre:",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        name_entry = ttk.Entry(
            main_frame,
            textvariable=self.profile_name,
            width=38,
            font=("Arial", 10)
        )
        name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        name_entry.focus()  # Establecer foco inicial

        # Criterio de búsqueda
        ttk.Label(
            main_frame,
            text="Criterio de búsqueda (título o texto similar):",
            font=("Arial", 10, "bold")
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))

        criteria_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria,
            width=38,
            font=("Arial", 10)
        )
        criteria_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 25))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        save_btn = ttk.Button(
            button_frame,
            text="Guardar",
            command=self._save_profile
        )
        save_btn.grid(row=0, column=0, padx=(0, 5), sticky="e")

        cancel_btn = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self.modal.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=(5, 0), sticky="w")

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

    def _save_profile(self):
        """Guarda o actualiza el perfil."""
        name = self.profile_name.get().strip()
        criteria = self.search_criteria.get().strip()

        if not name or not criteria:
            messagebox.showerror("Error", "Por favor complete todos los campos")
            return

        try:
            if self.edit_mode:
                # Actualizar perfil existente
                updated_profile = self.profile_manager.update_profile(
                    self.profile.profile_id, name, criteria
                )
                if updated_profile:
                    messagebox.showinfo("Éxito", "Perfil actualizado correctamente")
            else:
                # Crear nuevo perfil
                new_profile = self.profile_manager.add_profile(name, criteria)
                if new_profile:
                    messagebox.showinfo("Éxito", "Perfil creado correctamente")

            # Llamar al callback si existe
            if self.callback:
                self.callback()

            # Cerrar ventana
            self.modal.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el perfil: {e}")