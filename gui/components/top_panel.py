# gui/components/top_panel.py
"""
Componente del panel superior del bot.
Muestra perfiles de búsqueda de correos y permite gestionarlos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
from pathlib import Path
from gui.models.profile_manager import ProfileManager
from gui.components.profile_modal import ProfileModal
from services.report_service import ReportService
from services.email_service import EmailService


class TopPanel:
    """Maneja el contenido y funcionalidad del panel superior con perfiles de búsqueda."""

    def __init__(self, parent_frame, bottom_right_panel=None):
        """
        Inicializa el panel superior.

        Args:
            parent_frame: Frame padre donde se montará este componente
            bottom_right_panel: Referencia opcional al panel de logs
        """
        self.parent_frame = parent_frame
        self.bottom_right_panel = bottom_right_panel
        self.profile_manager = ProfileManager()
        self.report_service = ReportService()
        self.email_service = EmailService()
        self._setup_widgets()
        self._load_profiles()

    def _setup_widgets(self):
        """Configura los widgets del panel superior."""
        # Configurar expansión del frame
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(0, weight=0)  # Cabecera - no expandible
        self.parent_frame.rowconfigure(1, weight=1)  # Grid - expandible

        # Cabecera con título y botones
        self.header_frame = ttk.Frame(self.parent_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.columnconfigure(0, weight=1)  # Título expandible
        self.header_frame.columnconfigure(1, weight=0)  # Botones no expandibles

        # Título del panel
        self.title_label = ttk.Label(
            self.header_frame,
            text="🔎 PERFILES DE BÚSQUEDA",
            font=("Arial", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=5)

        # Frame para botones
        self.button_frame = ttk.Frame(self.header_frame)
        self.button_frame.grid(row=0, column=1, sticky="e")

        # Botones de acción
        self.generate_report_btn = ttk.Button(
            self.button_frame,
            text="Generar Reporte",
            command=self._generate_report
        )
        self.generate_report_btn.grid(row=0, column=0, padx=(0, 5))

        self.search_all_btn = ttk.Button(
            self.button_frame,
            text="Buscar Todos",
            command=self._run_global_search
        )
        self.search_all_btn.grid(row=0, column=1, padx=(0, 5))

        self.new_btn = ttk.Button(
            self.button_frame,
            text="Nuevo Perfil",
            command=self._open_new_profile_modal
        )
        self.new_btn.grid(row=0, column=2, padx=(0, 5))

        # Frame para el grid con scrollbar
        self.grid_frame = ttk.Frame(self.parent_frame)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.rowconfigure(0, weight=1)

        # Crear Treeview para la tabla de perfiles
        self.profiles_tree = ttk.Treeview(
            self.grid_frame,
            columns=("name", "criteria", "found", "last_search", "actions"),
            show="headings",
            selectmode="browse"
        )

        # Definir columnas
        self.profiles_tree.heading("name", text="Nombre del Perfil")
        self.profiles_tree.heading("criteria", text="Criterio de Búsqueda")
        self.profiles_tree.heading("found", text="Correos Encontrados")
        self.profiles_tree.heading("last_search", text="Última Búsqueda")
        self.profiles_tree.heading("actions", text="Acciones")

        # Configurar ancho de columnas
        self.profiles_tree.column("name", width=150, minwidth=100)
        self.profiles_tree.column("criteria", width=250, minwidth=150)
        self.profiles_tree.column("found", width=150, minwidth=100, anchor="center")
        self.profiles_tree.column("last_search", width=150, minwidth=100, anchor="center")
        self.profiles_tree.column("actions", width=150, minwidth=100, anchor="center")

        # Colocar el Treeview
        self.profiles_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar vertical
        vsb = ttk.Scrollbar(self.grid_frame, orient="vertical", command=self.profiles_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.profiles_tree.configure(yscrollcommand=vsb.set)

        # Scrollbar horizontal
        hsb = ttk.Scrollbar(self.grid_frame, orient="horizontal", command=self.profiles_tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.profiles_tree.configure(xscrollcommand=hsb.set)

        # Enlazar eventos
        self.profiles_tree.bind("<Double-1>", self._on_tree_double_click)
        self.profiles_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Mensaje cuando no hay perfiles
        self.empty_label = ttk.Label(
            self.grid_frame,
            text="No hay perfiles de búsqueda. Crea uno nuevo con el botón 'Nuevo Perfil'.",
            font=("Arial", 11),
            foreground="gray",
            anchor="center",
            justify="center"
        )

    def _load_profiles(self):
        """Carga y muestra los perfiles en el grid."""
        # Limpiar el grid actual
        for item in self.profiles_tree.get_children():
            self.profiles_tree.delete(item)

        # Obtener perfiles del gestor
        profiles = self.profile_manager.get_all_profiles()

        # Mostrar/ocultar mensaje de vacío
        if not profiles:
            self.empty_label.grid(row=0, column=0, sticky="nsew")
        else:
            self.empty_label.grid_remove()

        # Añadir perfiles al grid
        for profile in profiles:
            # Formatear la fecha de última búsqueda
            last_search = "Nunca" if not profile.last_search else profile.last_search.strftime("%d/%m/%Y %H:%M")

            # Añadir fila a la tabla
            item_id = self.profiles_tree.insert("", "end", text=profile.profile_id, values=(
                profile.name,
                profile.search_criteria,
                profile.found_emails,
                last_search,
                "🗑️ Eliminar"
            ))

            # Guardar el profile_id como tag
            self.profiles_tree.item(item_id, tags=(profile.profile_id,))

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(f"Perfiles cargados: {len(profiles)}")

    def _on_tree_click(self, event):
        """Maneja los clics en el árbol para la acción de eliminar."""
        region = self.profiles_tree.identify_region(event.x, event.y)

        if region == "cell":
            column = self.profiles_tree.identify_column(event.x)
            item = self.profiles_tree.identify_row(event.y)

            if not item:
                return

            # Si es la columna de acciones (5)
            if column == "#5":
                profile_id = self.profiles_tree.item(item, "tags")[0]
                profile = self.profile_manager.get_profile_by_id(profile_id)

                if profile:
                    self._delete_profile(profile)

    def _on_tree_double_click(self, event):
        """Maneja doble clic en un perfil para editarlo."""
        item = self.profiles_tree.identify_row(event.y)
        if not item:
            return

        profile_id = self.profiles_tree.item(item, "tags")[0]
        profile = self.profile_manager.get_profile_by_id(profile_id)

        if profile:
            self._edit_profile(profile)

    def _open_new_profile_modal(self):
        """Abre el modal para crear un nuevo perfil."""
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry("Creando nuevo perfil")

        ProfileModal(self.parent_frame, self.profile_manager, callback=self._load_profiles)

    def _edit_profile(self, profile):
        """Abre el modal para editar un perfil."""
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(f"Editando perfil: {profile.name}")

        ProfileModal(
            self.parent_frame,
            self.profile_manager,
            profile=profile,
            callback=self._load_profiles
        )

    def _delete_profile(self, profile):
        """Elimina un perfil tras confirmación."""
        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar el perfil '{profile.name}'?",
            icon=messagebox.WARNING
        )

        if confirm:
            if self.profile_manager.delete_profile(profile.profile_id):
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry(f"Perfil eliminado: {profile.name}")
                self._load_profiles()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el perfil")

    def _run_search(self, profile):
        """Ejecuta la búsqueda con el perfil seleccionado."""
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(f"Ejecutando búsqueda con perfil: {profile.name}")

        # Simulación de búsqueda
        import random
        found = random.randint(1, 20)

        # Actualizar resultados
        self.profile_manager.update_search_results(profile.profile_id, found)

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(f"Búsqueda completada: {found} correos encontrados")

        # Actualizar el grid
        self._load_profiles()
        return found

    def _run_global_search(self):
        """Ejecuta la búsqueda para todos los perfiles."""
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles de búsqueda para ejecutar.")
            return

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry("Iniciando búsqueda global con todos los perfiles")

        total_found = 0
        profiles_searched = 0

        for profile in profiles:
            found = self._run_search(profile)
            total_found += found
            profiles_searched += 1

        self._load_profiles()

        messagebox.showinfo(
            "Búsqueda global completada",
            f"Se han procesado {profiles_searched} perfiles.\n"
            f"Total de correos encontrados: {total_found}."
        )

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(f"Búsqueda global completada. Total: {total_found} correos")

    def _generate_report(self):
        """Genera y envía reporte Excel con información de perfiles."""
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles para generar reporte.")
            return

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry("Iniciando generación de reporte")

        try:
            # Generar archivo Excel
            report_path = self.report_service.generate_profiles_report(profiles)

            if self.bottom_right_panel:
                self.bottom_right_panel.add_log_entry(f"Reporte generado: {report_path}")

            # Enviar por correo
            success = self.email_service.send_report(report_path)

            if success:
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry("✅ Reporte enviado por correo exitosamente")
                messagebox.showinfo("Éxito", "Reporte generado y enviado por correo correctamente.")
            else:
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry("❌ Error al enviar reporte por correo")
                messagebox.showwarning("Advertencia",
                                       "Reporte generado pero no se pudo enviar por correo.\nVerifica la configuración de email.")

        except Exception as e:
            error_msg = f"Error al generar reporte: {e}"
            if self.bottom_right_panel:
                self.bottom_right_panel.add_log_entry(error_msg)
            messagebox.showerror("Error", error_msg)

    def get_data(self):
        """Retorna los datos actuales del panel."""
        return {
            "panel_type": "top_panel",
            "profiles_count": len(self.profile_manager.get_all_profiles())
        }