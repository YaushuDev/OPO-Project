# profile_modal.py
"""
Modal para crear o editar perfiles de búsqueda.
Permite configurar nombre, hasta 3 criterios de búsqueda diferentes,
configuración de seguimiento de ejecuciones óptimas y tipo de bot (Automático/Manual/Offline).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gui.models.search_profile import SearchProfile


BOT_TYPE_DISPLAY = {
    "automatico": "Automático",
    "manual": "Manual",
    "offline": "Offline"
}

BOT_TYPE_RADIO_TEXT = {
    "automatico": "🤖 Bot Automático",
    "manual": "👤 Bot Manual",
    "offline": "📴 Bot Offline"
}


class ProfileModal:
    """Modal para gestionar perfiles de búsqueda con múltiples criterios, seguimiento óptimo y tipo de bot."""

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

        # Variables para el nombre del perfil y responsable
        self.profile_name = tk.StringVar(value=profile.name if profile else "")
        self.responsable = tk.StringVar(value=getattr(profile, "responsable", "") if profile else "")
        self.last_update_text = tk.StringVar(
            value=getattr(profile, "last_update_text", "") if profile else ""
        )
        self.delivery_date_text = tk.StringVar(
            value=getattr(profile, "delivery_date_text", "") if profile else ""
        )

        # Variables para los 3 criterios de búsqueda
        self.search_criteria_1 = tk.StringVar()
        self.search_criteria_2 = tk.StringVar()
        self.search_criteria_3 = tk.StringVar()

        # Variable para filtro de remitente
        self.sender_filter = tk.StringVar()

        # Variables para seguimiento óptimo
        self.track_optimal = tk.BooleanVar(value=profile.track_optimal if profile else False)
        self.optimal_executions = tk.StringVar(
            value=str(profile.optimal_executions) if profile and profile.optimal_executions > 0 else "")

        # Variable para tipo de bot
        self.bot_type = tk.StringVar(value=profile.bot_type if profile else "manual")

        # Cargar criterios existentes si estamos editando
        if profile and profile.search_criteria:
            if len(profile.search_criteria) >= 1:
                self.search_criteria_1.set(profile.search_criteria[0])
            if len(profile.search_criteria) >= 2:
                self.search_criteria_2.set(profile.search_criteria[1])
            if len(profile.search_criteria) >= 3:
                self.search_criteria_3.set(profile.search_criteria[2])

        if profile and profile.has_sender_filters():
            self.sender_filter.set(", ".join(profile.sender_filters))

        # Crear ventana modal
        self.modal = tk.Toplevel(parent)
        self.modal.title("Editar Perfil" if self.edit_mode else "Nuevo Perfil")
        self.modal.geometry("520x860")
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
            text="📋 " + ("Editar Perfil de Búsqueda" if self.edit_mode else "Nuevo Perfil de Búsqueda"),
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
            width=50,
            font=("Arial", 10)
        )
        name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        name_entry.focus()

        # Responsable del perfil
        ttk.Label(
            main_frame,
            text="Responsable (opcional):",
            font=("Arial", 10)
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))

        responsable_entry = ttk.Entry(
            main_frame,
            textvariable=self.responsable,
            width=50,
            font=("Arial", 10)
        )
        responsable_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Campos adicionales: última actualización y fecha de entrega
        ttk.Label(
            main_frame,
            text="Última Actualización (opcional):",
            font=("Arial", 10)
        ).grid(row=5, column=0, sticky="w", pady=(0, 5))

        last_update_entry = ttk.Entry(
            main_frame,
            textvariable=self.last_update_text,
            width=50,
            font=("Arial", 10)
        )
        last_update_entry.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Fecha de entrega (opcional):",
            font=("Arial", 10)
        ).grid(row=7, column=0, sticky="w", pady=(0, 5))

        delivery_entry = ttk.Entry(
            main_frame,
            textvariable=self.delivery_date_text,
            width=50,
            font=("Arial", 10)
        )
        delivery_entry.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Sección de criterios de búsqueda
        criteria_label = ttk.Label(
            main_frame,
            text="Criterios de Búsqueda (llenar al menos uno):",
            font=("Arial", 11, "bold"),
            foreground="navy"
        )
        criteria_label.grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Criterio 1 (obligatorio)
        ttk.Label(
            main_frame,
            text="Criterio 1 (principal):",
            font=("Arial", 10, "bold")
        ).grid(row=10, column=0, sticky="w", pady=(0, 5))

        criteria_1_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_1,
            width=50,
            font=("Arial", 10)
        )
        criteria_1_entry.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Criterio 2 (opcional)
        ttk.Label(
            main_frame,
            text="Criterio 2 (opcional):",
            font=("Arial", 10)
        ).grid(row=12, column=0, sticky="w", pady=(0, 5))

        criteria_2_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_2,
            width=50,
            font=("Arial", 10)
        )
        criteria_2_entry.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Criterio 3 (opcional)
        ttk.Label(
            main_frame,
            text="Criterio 3 (opcional):",
            font=("Arial", 10)
        ).grid(row=14, column=0, sticky="w", pady=(0, 5))

        criteria_3_entry = ttk.Entry(
            main_frame,
            textvariable=self.search_criteria_3,
            width=50,
            font=("Arial", 10)
        )
        criteria_3_entry.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Filtro de remitente
        sender_label = ttk.Label(
            main_frame,
            text="Filtrar por Remitente (opcional):",
            font=("Arial", 10, "bold")
        )
        sender_label.grid(row=16, column=0, columnspan=2, sticky="w", pady=(0, 5))

        sender_entry = ttk.Entry(
            main_frame,
            textvariable=self.sender_filter,
            width=50,
            font=("Arial", 10)
        )
        sender_entry.grid(row=17, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        sender_hint = ttk.Label(
            main_frame,
            text="Puedes ingresar varios remitentes separados por coma.",
            font=("Arial", 9),
            foreground="gray"
        )
        sender_hint.grid(row=18, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Separador visual
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.grid(row=19, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Sección: Tipo de Bot
        bot_type_label = ttk.Label(
            main_frame,
            text="Tipo de Bot:",
            font=("Arial", 11, "bold"),
            foreground="purple"
        )
        bot_type_label.grid(row=20, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Frame para radio buttons del tipo de bot
        bot_type_frame = ttk.Frame(main_frame)
        bot_type_frame.grid(row=21, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        for idx in range(len(SearchProfile.BOT_TYPES)):
            bot_type_frame.columnconfigure(idx, weight=1)

        for idx, bot_type_value in enumerate(SearchProfile.BOT_TYPES):
            radio = ttk.Radiobutton(
                bot_type_frame,
                text=BOT_TYPE_RADIO_TEXT.get(bot_type_value, bot_type_value.title()),
                variable=self.bot_type,
                value=bot_type_value
            )
            padx = (0, 20) if idx < len(SearchProfile.BOT_TYPES) - 1 else (0, 0)
            radio.grid(row=0, column=idx, sticky="w", padx=padx)

        # Separador visual
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.grid(row=22, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Sección de seguimiento óptimo
        optimal_label = ttk.Label(
            main_frame,
            text="Seguimiento de Ejecuciones Óptimas:",
            font=("Arial", 11, "bold"),
            foreground="darkgreen"
        )
        optimal_label.grid(row=23, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Checkbox para habilitar seguimiento óptimo
        self.track_checkbox = ttk.Checkbutton(
            main_frame,
            text="Habilitar seguimiento de ejecuciones óptimas",
            variable=self.track_optimal,
            command=self._toggle_optimal_tracking
        )
        self.track_checkbox.grid(row=24, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Campo para cantidad de ejecuciones óptimas
        ttk.Label(
            main_frame,
            text="Cantidad de Ejecuciones Óptimas:",
            font=("Arial", 10)
        ).grid(row=25, column=0, sticky="w", pady=(0, 5))

        self.optimal_entry = ttk.Entry(
            main_frame,
            textvariable=self.optimal_executions,
            width=50,
            font=("Arial", 10)
        )
        self.optimal_entry.grid(row=26, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=27, column=0, columnspan=2, sticky="ew")
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

        # Aplicar estado inicial del seguimiento óptimo
        self._toggle_optimal_tracking()

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.modal.update_idletasks()
        width = self.modal.winfo_width()
        height = self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (width // 2)
        y = (self.modal.winfo_screenheight() // 2) - (height // 2)
        self.modal.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_optimal_tracking(self):
        """Habilita/deshabilita el campo de ejecuciones óptimas según el checkbox."""
        if self.track_optimal.get():
            self.optimal_entry.configure(state="normal")
        else:
            self.optimal_entry.configure(state="disabled")
            self.optimal_executions.set("")

    def _get_bot_type_display(self, bot_type):
        """Retorna el nombre formateado del tipo de bot."""
        return BOT_TYPE_DISPLAY.get(bot_type, "No definido")

    def _save_profile(self):
        """Guarda o actualiza el perfil con los múltiples criterios, seguimiento óptimo y tipo de bot."""
        name = self.profile_name.get().strip()
        bot_type = self.bot_type.get()

        # Recopilar criterios no vacíos
        criterios = []
        if self.search_criteria_1.get().strip():
            criterios.append(self.search_criteria_1.get().strip())
        if self.search_criteria_2.get().strip():
            criterios.append(self.search_criteria_2.get().strip())
        if self.search_criteria_3.get().strip():
            criterios.append(self.search_criteria_3.get().strip())

        # Validaciones básicas
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

        # Validar que se haya seleccionado un tipo de bot
        if not bot_type or bot_type not in SearchProfile.BOT_TYPES:
            allowed_types = ", ".join(BOT_TYPE_DISPLAY[bt] for bt in SearchProfile.BOT_TYPES)
            messagebox.showerror("Error", f"Debe seleccionar un tipo de bot ({allowed_types})")
            return

        # Validar seguimiento óptimo si está habilitado
        optimal_value = 0
        if self.track_optimal.get():
            optimal_text = self.optimal_executions.get().strip()
            if not optimal_text:
                messagebox.showerror("Error",
                                     "Debe ingresar la cantidad de ejecuciones óptimas si está habilitado el seguimiento")
                return

            try:
                optimal_value = int(optimal_text)
                if optimal_value <= 0:
                    messagebox.showerror("Error", "La cantidad de ejecuciones óptimas debe ser un número mayor a 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "La cantidad de ejecuciones óptimas debe ser un número válido")
                return

        sender_filters = self.sender_filter.get().strip()
        responsable = self.responsable.get().strip()
        last_update_text = self.last_update_text.get().strip()
        delivery_date_text = self.delivery_date_text.get().strip()

        try:
            if self.edit_mode:
                updated_profile = self.profile_manager.update_profile(
                    self.profile.profile_id,
                    name,
                    criterios,
                    sender_filters=sender_filters,
                    responsable=responsable,
                    optimal_executions=optimal_value,
                    track_optimal=self.track_optimal.get(),
                    bot_type=bot_type,
                    last_update_text=last_update_text,
                    delivery_date_text=delivery_date_text
                )

                if updated_profile:
                    bot_type_display = self._get_bot_type_display(bot_type)
                    mensaje = (
                        "Perfil actualizado correctamente\n\n"
                        f"Criterios configurados: {len(criterios)}\n"
                        f"Tipo de bot: {bot_type_display}"
                    )
                    if self.track_optimal.get():
                        mensaje += f"\nSeguimiento óptimo: {optimal_value} ejecuciones"
                    if updated_profile.has_sender_filters():
                        remitentes = ", ".join(updated_profile.sender_filters)
                        mensaje += f"\nRemitentes filtrados: {remitentes}"
                    if updated_profile.has_responsable():
                        mensaje += f"\nResponsable: {updated_profile.responsable}"
                    if updated_profile.has_last_update_text():
                        mensaje += f"\nÚltima actualización: {updated_profile.last_update_text}"
                    if updated_profile.has_delivery_date_text():
                        mensaje += f"\nFecha de entrega: {updated_profile.delivery_date_text}"
                    messagebox.showinfo("Éxito", mensaje)
            else:
                new_profile = self.profile_manager.add_profile(
                    name,
                    criterios,
                    sender_filters=sender_filters,
                    responsable=responsable,
                    bot_type=bot_type,
                    track_optimal=self.track_optimal.get(),
                    optimal_executions=optimal_value,
                    last_update_text=last_update_text,
                    delivery_date_text=delivery_date_text
                )
                if new_profile:
                    bot_type_display = self._get_bot_type_display(bot_type)
                    mensaje = (
                        "Perfil creado correctamente\n\n"
                        f"Criterios configurados: {len(criterios)}\n"
                        f"Tipo de bot: {bot_type_display}"
                    )
                    if self.track_optimal.get():
                        mensaje += f"\nSeguimiento óptimo: {optimal_value} ejecuciones"
                    if new_profile.has_sender_filters():
                        remitentes = ", ".join(new_profile.sender_filters)
                        mensaje += f"\nRemitentes filtrados: {remitentes}"
                    if new_profile.has_responsable():
                        mensaje += f"\nResponsable: {new_profile.responsable}"
                    if new_profile.has_last_update_text():
                        mensaje += f"\nÚltima actualización: {new_profile.last_update_text}"
                    if new_profile.has_delivery_date_text():
                        mensaje += f"\nFecha de entrega: {new_profile.delivery_date_text}"
                    messagebox.showinfo("Éxito", mensaje)

            # Llamar al callback si existe
            if self.callback:
                self.callback()

            # Cerrar ventana
            self.modal.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el perfil: {e}")