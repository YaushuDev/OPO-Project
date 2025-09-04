# gui/components/top_panel.py
"""
Componente del panel superior del bot.
Muestra perfiles de búsqueda de correos con múltiples criterios, seguimiento de ejecuciones
óptimas con porcentajes de éxito y colores indicativos, y permite gestionarlos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
from pathlib import Path
from gui.models.profile_manager import ProfileManager
from gui.components.profile_modal import ProfileModal
from gui.components.scheduler_modal import SchedulerModal
from services.report_service import ReportService
from services.email_service import EmailService
from services.scheduler_service import SchedulerService
from services.search_service import SearchService


class TopPanel:
    """Maneja el contenido y funcionalidad del panel superior con perfiles de búsqueda múltiple y seguimiento óptimo."""

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

        # Inicializar el servicio de búsqueda
        self.search_service = SearchService(log_callback=self._add_log)

        # Inicializar el servicio de programación con referencia a la función de generación de reportes
        self.scheduler_service = SchedulerService(
            report_generator=self._generate_scheduled_report,
            log_callback=self._add_log
        )

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
            text="📋 PERFILES DE BÚSQUEDA",
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

        # Botón de programación
        self.schedule_btn = ttk.Button(
            self.button_frame,
            text="Programar Envíos",
            command=self._open_scheduler_modal
        )
        self.schedule_btn.grid(row=0, column=1, padx=(0, 5))

        self.search_all_btn = ttk.Button(
            self.button_frame,
            text="Buscar Todos",
            command=self._run_global_search
        )
        self.search_all_btn.grid(row=0, column=2, padx=(0, 5))

        self.new_btn = ttk.Button(
            self.button_frame,
            text="Nuevo Perfil",
            command=self._open_new_profile_modal
        )
        self.new_btn.grid(row=0, column=3)

        # Frame para el grid con scrollbar
        self.grid_frame = ttk.Frame(self.parent_frame)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.rowconfigure(0, weight=1)

        # Crear Treeview para la tabla de perfiles con nuevas columnas
        self.profiles_tree = ttk.Treeview(
            self.grid_frame,
            columns=("name", "criteria", "executions", "optimal", "success", "last_search", "actions"),
            show="headings",
            selectmode="browse"
        )

        # Definir columnas con las nuevas columnas de seguimiento óptimo
        self.profiles_tree.heading("name", text="Nombre del Perfil")
        self.profiles_tree.heading("criteria", text="Criterios de Búsqueda")
        self.profiles_tree.heading("executions", text="Cantidad de ejecuciones")  # Cambio de "Correos Encontrados"
        self.profiles_tree.heading("optimal", text="Ejecuciones Óptimas")  # NUEVA COLUMNA
        self.profiles_tree.heading("success", text="Porcentaje de Éxito")  # NUEVA COLUMNA
        self.profiles_tree.heading("last_search", text="Última Búsqueda")
        self.profiles_tree.heading("actions", text="Acciones")

        # Configurar ancho de columnas (redistribuido para las nuevas columnas)
        self.profiles_tree.column("name", width=120, minwidth=100)
        self.profiles_tree.column("criteria", width=240, minwidth=200)  # Reducido para hacer espacio
        self.profiles_tree.column("executions", width=110, minwidth=90, anchor="center")  # Renombrado
        self.profiles_tree.column("optimal", width=110, minwidth=90, anchor="center")  # NUEVA
        self.profiles_tree.column("success", width=110, minwidth=90, anchor="center")  # NUEVA
        self.profiles_tree.column("last_search", width=130, minwidth=120, anchor="center")
        self.profiles_tree.column("actions", width=80, minwidth=70, anchor="center")

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

        # Configurar estilos para el Treeview (colores para éxito óptimo)
        style = ttk.Style()

        # Estilo para filas con éxito óptimo (verde)
        style.configure("Success.Treeview", background="#e8f5e8", foreground="darkgreen")

        # Enlazar eventos
        self.profiles_tree.bind("<Double-1>", self._on_tree_double_click)
        self.profiles_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Mensaje cuando no hay perfiles
        self.empty_label = ttk.Label(
            self.grid_frame,
            text="No hay perfiles de búsqueda. Crea uno nuevo con el botón 'Nuevo Perfil'.\n"
                 "Ahora puedes configurar hasta 3 criterios diferentes por perfil\n"
                 "y hacer seguimiento de ejecuciones óptimas con porcentajes de éxito.",
            font=("Arial", 11),
            foreground="gray",
            anchor="center",
            justify="center"
        )

    def _load_profiles(self):
        """Carga y muestra los perfiles con múltiples criterios y seguimiento óptimo en el grid."""
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
            try:
                # Formatear la fecha de última búsqueda
                last_search = "Nunca" if not profile.last_search else profile.last_search.strftime("%d/%m/%Y %H:%M")

                # Usar el método get_criteria_display() para mostrar criterios de manera legible
                criteria_display = profile.get_criteria_display()

                # Mostrar información de seguimiento óptimo
                optimal_display = profile.get_optimal_display()
                success_display = profile.get_success_display()

                # Añadir fila a la tabla con las nuevas columnas
                item_id = self.profiles_tree.insert("", "end", text=profile.profile_id, values=(
                    profile.name,
                    criteria_display,
                    profile.found_emails,  # Cantidad de ejecuciones (antes "correos encontrados")
                    optimal_display,  # NUEVA: Ejecuciones óptimas
                    success_display,  # NUEVA: Porcentaje de éxito
                    last_search,
                    "🗑️ Eliminar"
                ))

                # Guardar el profile_id como tag
                self.profiles_tree.item(item_id, tags=(profile.profile_id,))

                # Aplicar color verde si tiene éxito óptimo
                if profile.is_success_optimal():
                    # Configurar fondo verde para toda la fila
                    self.profiles_tree.set(item_id, "success", f"✅ {success_display}")

            except Exception as e:
                self._add_log(f"Error al cargar perfil {profile.name}: {e}")
                continue

        # Mostrar estadísticas ampliadas en el log
        if profiles and self.bottom_right_panel:
            summary = self.profile_manager.get_profiles_summary()
            self.bottom_right_panel.add_log_entry(
                f"Perfiles cargados: {summary['total_profiles']} "
                f"({summary['total_criteria']} criterios, "
                f"{summary['profiles_with_tracking']} con seguimiento óptimo)"
            )

            if summary['profiles_with_tracking'] > 0:
                self.bottom_right_panel.add_log_entry(
                    f"Éxito promedio: {summary['avg_success_percentage']}% "
                    f"({summary['optimal_profiles']} perfiles óptimos)"
                )

    def _on_tree_click(self, event):
        """Maneja los clics en el árbol para la acción de eliminar."""
        region = self.profiles_tree.identify_region(event.x, event.y)

        if region == "cell":
            column = self.profiles_tree.identify_column(event.x)
            item = self.profiles_tree.identify_row(event.y)

            if not item:
                return

            # Si es la columna de acciones (7, antes era 5)
            if column == "#7":
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
            self.bottom_right_panel.add_log_entry("Creando nuevo perfil con múltiples criterios y seguimiento óptimo")

        ProfileModal(self.parent_frame, self.profile_manager, callback=self._load_profiles)

    def _open_scheduler_modal(self):
        """Abre el modal para configurar la programación de reportes."""
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry("Abriendo configuración de programación de reportes")

        # Abrir modal de configuración
        scheduler_modal = SchedulerModal(self.parent_frame, self.bottom_right_panel)

        # Reiniciar el servicio cuando se cierre el modal para aplicar los cambios
        self.parent_frame.after(500, self.scheduler_service.restart)

    def _edit_profile(self, profile):
        """Abre el modal para editar un perfil."""
        if self.bottom_right_panel:
            criterios_count = len(profile.search_criteria)
            optimal_text = f" (óptimo: {profile.optimal_executions})" if profile.track_optimal else ""
            self.bottom_right_panel.add_log_entry(
                f"Editando perfil: {profile.name} ({criterios_count} criterios{optimal_text})"
            )

        ProfileModal(
            self.parent_frame,
            self.profile_manager,
            profile=profile,
            callback=self._load_profiles
        )

    def _delete_profile(self, profile):
        """Elimina un perfil tras confirmación."""
        criterios_count = len(profile.search_criteria)
        criterios_text = "criterio" if criterios_count == 1 else "criterios"

        optimal_text = ""
        if profile.track_optimal:
            optimal_text = f"\nSeguimiento óptimo: {profile.optimal_executions} ejecuciones"

        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar el perfil '{profile.name}'?\n"
            f"Se perderán {criterios_count} {criterios_text} de búsqueda.{optimal_text}",
            icon=messagebox.WARNING
        )

        if confirm:
            if self.profile_manager.delete_profile(profile.profile_id):
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry(
                        f"Perfil eliminado: {profile.name} ({criterios_count} criterios)"
                    )
                self._load_profiles()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el perfil")

    def _run_search(self, profile):
        """
        Ejecuta la búsqueda con todos los criterios del perfil seleccionado.

        Args:
            profile: Perfil de búsqueda con múltiples criterios

        Returns:
            int: Número total de correos encontrados (suma de todos los criterios)
        """
        criterios_count = len(profile.search_criteria)
        optimal_info = ""
        if profile.track_optimal:
            optimal_info = f" (óptimo: {profile.optimal_executions})"

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(
                f"Ejecutando búsqueda: '{profile.name}' con {criterios_count} criterio(s){optimal_info}"
            )

        # Ejecutar búsqueda real usando el servicio (ahora maneja múltiples criterios)
        total_found = self.search_service.search_emails(profile)

        # Actualizar resultados en el perfil
        self.profile_manager.update_search_results(profile.profile_id, total_found)

        # Log ampliado con información de éxito
        log_message = f"Búsqueda completada: {total_found} ejecuciones encontradas " \
                      f"(suma de {criterios_count} criterios)"

        if profile.track_optimal:
            success_percentage = profile.get_success_percentage()
            if success_percentage is not None:
                log_message += f" - Éxito: {success_percentage}%"
                if profile.is_success_optimal():
                    log_message += " ✅ ÓPTIMO"

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(log_message)

        # Actualizar el grid
        self._load_profiles()
        return total_found

    def _run_global_search(self):
        """Ejecuta la búsqueda para todos los perfiles con todos sus criterios."""
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles de búsqueda para ejecutar.")
            return

        # Calcular total de criterios y perfiles con seguimiento
        total_criterios = sum(len(p.search_criteria) for p in profiles)
        tracking_profiles = [p for p in profiles if p.track_optimal]

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(
                f"Iniciando búsqueda global: {len(profiles)} perfiles, {total_criterios} criterios, "
                f"{len(tracking_profiles)} con seguimiento óptimo"
            )

        total_found = 0
        profiles_searched = 0
        optimal_achieved = 0

        for profile in profiles:
            found = self._run_search(profile)
            total_found += found
            profiles_searched += 1

            # Contar perfiles que alcanzaron el óptimo
            if profile.is_success_optimal():
                optimal_achieved += 1

        self._load_profiles()

        # Mensaje de resultado ampliado
        result_message = f"Se han procesado {profiles_searched} perfiles.\n" \
                         f"Total de criterios buscados: {total_criterios}\n" \
                         f"Total de ejecuciones encontradas: {total_found}"

        if tracking_profiles:
            result_message += f"\n\nSeguimiento óptimo:\n" \
                              f"• Perfiles con seguimiento: {len(tracking_profiles)}\n" \
                              f"• Perfiles que alcanzaron el óptimo: {optimal_achieved}\n" \
                              f"• Tasa de éxito: {round((optimal_achieved / len(tracking_profiles)) * 100, 1) if tracking_profiles else 0}%"

        messagebox.showinfo("Búsqueda global completada", result_message)

        if self.bottom_right_panel:
            summary = self.profile_manager.get_profiles_summary()
            self.bottom_right_panel.add_log_entry(
                f"✅ Búsqueda global completada: {total_found} ejecuciones "
                f"({optimal_achieved}/{len(tracking_profiles)} perfiles óptimos)"
            )

    def _generate_report(self):
        """Genera y envía reporte Excel con información de perfiles, múltiples criterios y seguimiento óptimo."""
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles para generar reporte.")
            return

        # Obtener estadísticas mejoradas con seguimiento óptimo
        summary = self.profile_manager.get_profiles_summary()

        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(
                f"Iniciando generación de reporte: {summary['total_profiles']} perfiles, "
                f"{summary['total_criteria']} criterios, {summary['profiles_with_tracking']} con seguimiento óptimo"
            )

        try:
            # Generar archivo Excel
            report_path = self.report_service.generate_profiles_report(profiles)

            if self.bottom_right_panel:
                self.bottom_right_panel.add_log_entry(f"Reporte generado: {report_path}")

            # Enviar por correo
            success = self.email_service.send_report(report_path)

            if success:
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry(
                        "✅ Reporte con seguimiento óptimo enviado por correo exitosamente"
                    )
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

    def _generate_scheduled_report(self):
        """Genera y envía reporte programado sin interacción del usuario."""
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            self._add_log("No hay perfiles para generar reporte programado")
            return False

        summary = self.profile_manager.get_profiles_summary()
        self._add_log(
            f"Iniciando reporte programado: {summary['total_profiles']} perfiles, "
            f"{summary['total_criteria']} criterios, {summary['profiles_with_tracking']} con seguimiento"
        )

        try:
            # Generar archivo Excel
            report_path = self.report_service.generate_profiles_report(profiles)
            self._add_log(f"Reporte programado generado: {report_path}")

            # Enviar por correo
            success = self.email_service.send_report(report_path)

            if success:
                optimal_count = summary['optimal_profiles']
                self._add_log(f"✅ Reporte programado enviado ({optimal_count} perfiles óptimos)")
                return True
            else:
                self._add_log("❌ Error al enviar reporte programado por correo")
                return False

        except Exception as e:
            error_msg = f"Error al generar reporte programado: {e}"
            self._add_log(error_msg)
            return False

    def _add_log(self, message):
        """
        Agrega mensaje al log.

        Args:
            message (str): Mensaje a agregar
        """
        if self.bottom_right_panel:
            self.bottom_right_panel.add_log_entry(message)

    def get_data(self):
        """Retorna los datos actuales del panel con información de múltiples criterios y seguimiento óptimo."""
        summary = self.profile_manager.get_profiles_summary()
        return {
            "panel_type": "top_panel",
            "profiles_count": summary['total_profiles'],
            "total_criteria": summary['total_criteria'],
            "active_profiles": summary['active_profiles'],
            "total_emails_found": summary['total_emails_found'],
            # Nuevas métricas
            "profiles_with_tracking": summary['profiles_with_tracking'],
            "optimal_profiles": summary['optimal_profiles'],
            "avg_success_percentage": summary['avg_success_percentage']
        }