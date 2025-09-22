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
        self.modal.geometry("960x520")
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
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="📋 " + ("Editar Perfil de Búsqueda" if self.edit_mode else "Nuevo Perfil de Búsqueda"),
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Contenedor principal con diseño horizontal
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Columna izquierda: información del perfil
        left_column = ttk.Frame(content_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_column.columnconfigure(0, weight=1)

        info_frame = ttk.LabelFrame(left_column, text="Información del Perfil", padding="15 10 15 15")
        info_frame.grid(row=0, column=0, sticky="nsew")
        info_frame.columnconfigure(0, weight=0)
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(
            info_frame,
            text="Nombre del Perfil:",
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 12), padx=(0, 10))

        name_entry = ttk.Entry(
            info_frame,
            textvariable=self.profile_name,
            width=40,
            font=("Arial", 10)
        )
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 12))
        name_entry.focus()

        ttk.Label(
            info_frame,
            text="Responsable (opcional):",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", pady=(0, 12), padx=(0, 10))

        responsable_entry = ttk.Entry(
            info_frame,
            textvariable=self.responsable,
            width=40,
            font=("Arial", 10)
        )
        responsable_entry.grid(row=1, column=1, sticky="ew", pady=(0, 12))

        ttk.Label(
            info_frame,
            text="Última Actualización (opcional):",
            font=("Arial", 10)
        ).grid(row=2, column=0, sticky="w", pady=(0, 12), padx=(0, 10))

        last_update_entry = ttk.Entry(
            info_frame,
            textvariable=self.last_update_text,
            width=40,
            font=("Arial", 10)
        )
        last_update_entry.grid(row=2, column=1, sticky="ew", pady=(0, 12))

        ttk.Label(
            info_frame,
            text="Fecha de entrega (opcional):",
            font=("Arial", 10)
        ).grid(row=3, column=0, sticky="w", pady=(0, 0), padx=(0, 10))

        delivery_entry = ttk.Entry(
            info_frame,
            textvariable=self.delivery_date_text,
            width=40,
            font=("Arial", 10)
        )
        delivery_entry.grid(row=3, column=1, sticky="ew", pady=(0, 0))

        left_column.rowconfigure(1, weight=1)

        # Columna derecha: criterios, filtros y opciones
        right_column = ttk.Frame(content_frame)
        right_column.grid(row=0, column=1, sticky="nsew")
        right_column.columnconfigure(0, weight=1)

        criteria_frame = ttk.LabelFrame(
            right_column,
            text="Criterios de Búsqueda",
            padding="15 10 15 15"
        )
        criteria_frame.grid(row=0, column=0, sticky="nsew")
        criteria_frame.columnconfigure(0, weight=0)
        criteria_frame.columnconfigure(1, weight=1)

        ttk.Label(
            criteria_frame,
            text="Completa al menos un criterio",
            font=("Arial", 9),
            foreground="navy"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(
            criteria_frame,
            text="Criterio 1 (principal):",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 10))

        criteria_1_entry = ttk.Entry(
            criteria_frame,
            textvariable=self.search_criteria_1,
            width=40,
            font=("Arial", 10)
        )
        criteria_1_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(
            criteria_frame,
            text="Criterio 2 (opcional):",
            font=("Arial", 10)
        ).grid(row=2, column=0, sticky="w", pady=(0, 10), padx=(0, 10))

        criteria_2_entry = ttk.Entry(
            criteria_frame,
            textvariable=self.search_criteria_2,
            width=40,
            font=("Arial", 10)
        )
        criteria_2_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(
            criteria_frame,
            text="Criterio 3 (opcional):",
            font=("Arial", 10)
        ).grid(row=3, column=0, sticky="w", pady=(0, 0), padx=(0, 10))

        criteria_3_entry = ttk.Entry(
            criteria_frame,
            textvariable=self.search_criteria_3,
            width=40,
            font=("Arial", 10)
        )
        criteria_3_entry.grid(row=3, column=1, sticky="ew")

        filter_frame = ttk.LabelFrame(
            right_column,
            text="Filtros adicionales",
            padding="15 10 15 15"
        )
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        filter_frame.columnconfigure(0, weight=0)
        filter_frame.columnconfigure(1, weight=1)

        ttk.Label(
            filter_frame,
            text="Remitentes (opcional):",
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        sender_entry = ttk.Entry(
            filter_frame,
            textvariable=self.sender_filter,
            width=40,
            font=("Arial", 10)
        )
        sender_entry.grid(row=0, column=1, sticky="ew")

        sender_hint = ttk.Label(
            filter_frame,
            text="Puedes ingresar varios remitentes separados por coma.",
            font=("Arial", 9),
            foreground="gray"
        )
        sender_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        bot_frame = ttk.LabelFrame(
            right_column,
            text="Tipo de Bot",
            padding="15 10 15 15"
        )
        bot_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        bot_frame.columnconfigure(0, weight=1)

        ttk.Label(
            bot_frame,
            text="Selecciona el modo de ejecución:",
            font=("Arial", 10),
            foreground="purple"
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        bot_type_frame = ttk.Frame(bot_frame)
        bot_type_frame.grid(row=1, column=0, sticky="ew")

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

        optimal_frame = ttk.LabelFrame(
            right_column,
            text="Seguimiento de ejecuciones óptimas",
            padding="15 10 15 15"
        )
        optimal_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        optimal_frame.columnconfigure(0, weight=0)
        optimal_frame.columnconfigure(1, weight=1)

        self.track_checkbox = ttk.Checkbutton(
            optimal_frame,
            text="Habilitar seguimiento",
            variable=self.track_optimal,
            command=self._toggle_optimal_tracking
        )
        self.track_checkbox.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(
            optimal_frame,
            text="Cantidad de ejecuciones óptimas:",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", padx=(0, 10))

        self.optimal_entry = ttk.Entry(
            optimal_frame,
            textvariable=self.optimal_executions,
            width=20,
            font=("Arial", 10)
        )
        self.optimal_entry.grid(row=1, column=1, sticky="ew")

        # Alinear peso de filas en la columna derecha
        right_column.rowconfigure(0, weight=1)
        right_column.rowconfigure(1, weight=0)
        right_column.rowconfigure(2, weight=0)
        right_column.rowconfigure(3, weight=0)

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(25, 0))
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