# gui/components/profile_modal.py
"""
Modal para crear o editar perfiles de búsqueda.
Permite configurar nombre y hasta 3 criterios de búsqueda diferentes.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ProfileModal:
    """Modal para gestionar perfiles de búsqueda con múltiples criterios."""

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

        # Variables para el nombre del perfil
        self.profile_name = tk.StringVar(value=profile.name if profile else "")

        # Variables para los 3 criterios de búsqueda
        self.search_criteria_1 = tk.StringVar()
        self.search_criteria_2 = tk.StringVar()
        self.search_criteria_3 = tk.StringVar()

        # Cargar criterios existentes si estamos editando
        if profile and profile.search_criteria:
            if len(profile.search_criteria) >= 1:
                self.search_criteria_1.set(profile.search_criteria[0])
            if len(profile.search_criteria) >= 2:
                self.search_criteria_2.set(profile.search_criteria[1])
            if len(profile.search_criteria) >= 3:
                self.search_criteria_3.set(profile.search_criteria[2])

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Editar Perfil" if self.edit_mode else "Nuevo Perfil")
        self.modal.geometry("480x420")
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
            text="Nombre del Perfil:",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        name_entry = ttk.Entry(
            main_frame,
            textvariable=self.profile_name,
            width=45,
            font=("Arial", 10)
        )
        name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        name_entry.focus()  # Establecer foco inicial

        # Sección de criterios de búsqueda
        criteria_label = ttk.Label(
            main_frame,
            text="Criterios de Búsqueda (llenar al menos uno):",
            font=("Arial", 11, "bold"),
            foreground="navy"
        )
        criteria_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Criterio 1 (obligatorio)
        ttk.Label(
            main_frame,
            text="Criterio 1 (principal):",
            font=("Arial", 10, "bold")
        ).grid(row=4, column=0, sticky="w", pady=(0, 5))

        criteria_1_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_1,
            width=45,
            font=("Arial", 10)
        )
        criteria_1_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Criterio 2 (opcional)
        ttk.Label(
            main_frame,
            text="Criterio 2 (opcional):",
            font=("Arial", 10)
        ).grid(row=6, column=0, sticky="w", pady=(0, 5))

        criteria_2_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_2,
            width=45,
            font=("Arial", 10)
        )
        criteria_2_entry.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Criterio 3 (opcional)
        ttk.Label(
            main_frame,
            text="Criterio 3 (opcional):",
            font=("Arial", 10)
        ).grid(row=8, column=0, sticky="w", pady=(0, 5))

        criteria_3_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_3,
            width=45,
            font=("Arial", 10)
        )
        criteria_3_entry.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Nota explicativa
        note_label = ttk.Label(
            main_frame,
            text="💡 El bot buscará correos que coincidan con cualquiera de los criterios\ny sumará todos los resultados encontrados.",
            font=("Arial", 9),
            foreground="gray",
            justify="left"
        )
        note_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, sticky="ew")
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
        """Guarda o actualiza el perfil con los múltiples criterios."""
        name = self.profile_name.get().strip()

        # Recopilar criterios no vacíos
        criterios = []
        if self.search_criteria_1.get().strip():
            criterios.append(self.search_criteria_1.get().strip())
        if self.search_criteria_2.get().strip():
            criterios.append(self.search_criteria_2.get().strip())
        if self.search_criteria_3.get().strip():
            criterios.append(self.search_criteria_3.get().strip())

        # Validaciones
        if not name:
            messagebox.showerror("Error", "El nombre del perfil es obligatorio")
            return

        if not criterios:
            messagebox.showerror("Error", "Debe ingresar al menos un criterio de búsqueda")
            return

        # Verificar que no haya criterios duplicados
        if len(criterios) != len(set(criterios)):
            messagebox.showerror("Error", "No puede haber criterios de búsqueda duplicados")
            return

        try:
            if self.edit_mode:
                # Actualizar perfil existente
                updated_profile = self.profile_manager.update_profile(
                    self.profile.profile_id, name, criterios
                )
                if updated_profile:
                    mensaje = f"Perfil actualizado correctamente\n\nCriterios configurados: {len(criterios)}"
                    messagebox.showinfo("Éxito", mensaje)
            else:
                # Crear nuevo perfil
                new_profile = self.profile_manager.add_profile(name, criterios)
                if new_profile:
                    mensaje = f"Perfil creado correctamente\n\nCriterios configurados: {len(criterios)}"
                    messagebox.showinfo("Éxito", mensaje)

            # Llamar al callback si existe
            if self.callback:
                self.callback()

            # Cerrar ventana
            self.modal.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el perfil: {e}")