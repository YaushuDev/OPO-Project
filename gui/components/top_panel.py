# top_panel.py
"""
Componente del panel superior del bot optimizado con threading.
Previene bloqueos de UI durante operaciones pesadas como búsquedas IMAP y generación de reportes.
Incluye indicadores de progreso y manejo asíncrono de operaciones con opciones
separadas para programación diaria, semanal y mensual.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import threading
import time
from pathlib import Path
from gui.models.profile_manager import ProfileManager
from gui.components.profile_modal import ProfileModal
from gui.components.scheduler_modal import SchedulerModal
from services.report_service import ReportService
from services.email_service import EmailService
from services.scheduler_service import UnifiedSchedulerService
from services.search_service import SearchService
from services.progress_service import ProgressService


class TopPanel:
    """Panel superior optimizado con threading para prevenir bloqueos de UI."""

    def __init__(self, parent_frame, bottom_right_panel=None):
        """
        Inicializa el panel superior optimizado.

        Args:
            parent_frame: Frame padre donde se montará este componente
            bottom_right_panel: Referencia opcional al panel de logs
        """
        self.parent_frame = parent_frame
        self.bottom_right_panel = bottom_right_panel
        self.profile_manager = ProfileManager()
        self.report_service = ReportService()
        self.email_service = EmailService()

        # Inicializar el servicio de progreso
        self.progress_service = ProgressService(
            parent_frame,
            log_callback=self._add_log
        )

        # Inicializar el servicio de búsqueda mejorada
        self.search_service = SearchService(log_callback=self._add_log)

        # Variables de control para operaciones asíncronas
        self.is_searching = False
        self.is_generating_report = False
        self.is_generating_weekly_report = False
        self.is_generating_monthly_report = False  # Nueva variable para reportes mensuales

        # Ruta al archivo de configuración
        self.config_file = Path("config") / "scheduler_config.json"

        # Inicializar el servicio de programación unificado
        self.scheduler_service = UnifiedSchedulerService(
            self.config_file,
            callbacks={
                "daily": self._generate_scheduled_report,
                "weekly": self._generate_scheduled_weekly_report,
                "monthly": self._generate_scheduled_monthly_report
            },
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

        # Botones de acción optimizados
        self.generate_report_btn = ttk.Button(
            self.button_frame,
            text="Generar Reporte",
            command=self._generate_report_async
        )
        self.generate_report_btn.grid(row=0, column=0, padx=(0, 5))

        # Botón para reporte semanal
        self.generate_weekly_report_btn = ttk.Button(
            self.button_frame,
            text="Generar Reporte Semanal",
            command=self._generate_weekly_report_async
        )
        self.generate_weekly_report_btn.grid(row=0, column=1, padx=(0, 5))

        # Botón para reporte mensual
        self.generate_monthly_report_btn = ttk.Button(
            self.button_frame,
            text="Generar Reporte Mensual",
            command=self._generate_monthly_report_async
        )
        self.generate_monthly_report_btn.grid(row=0, column=2, padx=(0, 5))

        # Botón de programación unificada
        self.schedule_reports_btn = ttk.Button(
            self.button_frame,
            text="Programar Reportes",
            command=self._open_scheduler_modal
        )
        self.schedule_reports_btn.grid(row=0, column=3, padx=(0, 5))

        self.search_all_btn = ttk.Button(
            self.button_frame,
            text="Buscar Todos",
            command=self._run_global_search_async
        )
        self.search_all_btn.grid(row=0, column=4, padx=(0, 5))

        self.new_btn = ttk.Button(
            self.button_frame,
            text="Nuevo Perfil",
            command=self._open_new_profile_modal
        )
        self.new_btn.grid(row=0, column=5)

        # Frame para el grid con scrollbar
        self.grid_frame = ttk.Frame(self.parent_frame)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.rowconfigure(0, weight=1)

        # Crear Treeview para la tabla de perfiles
        self.profiles_tree = ttk.Treeview(
            self.grid_frame,
            columns=("name", "bot_type", "criteria", "executions", "optimal", "success", "last_search", "actions"),
            show="headings",
            selectmode="browse"
        )

        # Definir columnas
        self.profiles_tree.heading("name", text="Nombre del Perfil")
        self.profiles_tree.heading("bot_type", text="Tipo de Bot")
        self.profiles_tree.heading("criteria", text="Criterios de Búsqueda")
        self.profiles_tree.heading("executions", text="Cantidad de ejecuciones")
        self.profiles_tree.heading("optimal", text="Ejecuciones Óptimas")
        self.profiles_tree.heading("success", text="Porcentaje de Éxito")
        self.profiles_tree.heading("last_search", text="Última Búsqueda")
        self.profiles_tree.heading("actions", text="Acciones")

        # Configurar ancho de columnas
        self.profiles_tree.column("name", width=110, minwidth=90)
        self.profiles_tree.column("bot_type", width=90, minwidth=80, anchor="center")
        self.profiles_tree.column("criteria", width=200, minwidth=180)
        self.profiles_tree.column("executions", width=100, minwidth=80, anchor="center")
        self.profiles_tree.column("optimal", width=100, minwidth=80, anchor="center")
        self.profiles_tree.column("success", width=100, minwidth=80, anchor="center")
        self.profiles_tree.column("last_search", width=120, minwidth=100, anchor="center")
        self.profiles_tree.column("actions", width=70, minwidth=60, anchor="center")

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

        # Configurar estilos para el Treeview
        style = ttk.Style()
        style.configure("Success.Treeview", background="#e8f5e8", foreground="darkgreen")

        # Enlazar eventos
        self.profiles_tree.bind("<Double-1>", self._on_tree_double_click)
        self.profiles_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Mensaje cuando no hay perfiles
        self.empty_label = ttk.Label(
            self.grid_frame,
            text="No hay perfiles de búsqueda. Crea uno nuevo con el botón 'Nuevo Perfil'.\n"
                 "Ahora puedes configurar hasta 3 criterios diferentes por perfil,\n"
                 "hacer seguimiento de ejecuciones óptimas con porcentajes de éxito\n"
                 "y elegir entre Bot Automático (🤖) o Bot Manual (👤).",
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
            try:
                # Formatear la fecha de última búsqueda
                last_search = "Nunca" if not profile.last_search else profile.last_search.strftime("%d/%m/%Y %H:%M")

                # Usar métodos del perfil para mostrar información
                criteria_display = profile.get_criteria_display()
                optimal_display = profile.get_optimal_display()
                success_display = profile.get_success_display()
                bot_type_display = profile.get_bot_type_display()

                # Añadir fila a la tabla
                item_id = self.profiles_tree.insert("", "end", text=profile.profile_id, values=(
                    profile.name,
                    bot_type_display,
                    criteria_display,
                    profile.found_emails,
                    optimal_display,
                    success_display,
                    last_search,
                    "🗑️ Eliminar"
                ))

                # Guardar el profile_id como tag
                self.profiles_tree.item(item_id, tags=(profile.profile_id,))

                # Aplicar color verde si tiene éxito óptimo
                if profile.is_success_optimal():
                    self.profiles_tree.set(item_id, "success", f"✅ {success_display}")

            except Exception as e:
                self._add_log(f"Error al cargar perfil {profile.name}: {e}")
                continue

        # Mostrar estadísticas en el log
        if profiles and self.bottom_right_panel:
            summary = self.profile_manager.get_profiles_summary()
            automatic_bots = len([p for p in profiles if p.is_bot_automatic()])
            manual_bots = len([p for p in profiles if p.is_bot_manual()])

            self.bottom_right_panel.add_log_entry(
                f"Perfiles cargados: {summary['total_profiles']} "
                f"({summary['total_criteria']} criterios, "
                f"{automatic_bots} automáticos, {manual_bots} manuales)"
            )

            if summary['profiles_with_tracking'] > 0:
                self.bottom_right_panel.add_log_entry(
                    f"Seguimiento óptimo: {summary['profiles_with_tracking']} perfiles "
                    f"({summary['optimal_profiles']} alcanzaron óptimo - {summary['avg_success_percentage']}% promedio)"
                )

    def _on_tree_click(self, event):
        """Maneja los clics en el árbol para la acción de eliminar."""
        region = self.profiles_tree.identify_region(event.x, event.y)

        if region == "cell":
            column = self.profiles_tree.identify_column(event.x)
            item = self.profiles_tree.identify_row(event.y)

            if not item:
                return

            # Si es la columna de acciones
            if column == "#8":
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
            self.bottom_right_panel.add_log_entry(
                "Creando nuevo perfil con múltiples criterios, seguimiento óptimo y tipo de bot")

        ProfileModal(self.parent_frame, self.profile_manager, callback=self._load_profiles)

    def _open_scheduler_modal(self):
        """Abre el modal unificado de programación de reportes."""
        if self._check_operation_in_progress():
            return

        try:
            if self.bottom_right_panel:
                self.bottom_right_panel.add_log_entry(
                    "Abriendo configuración unificada de programación de reportes")

            self.schedule_reports_btn.config(state="disabled")

            def on_close():
                self.schedule_reports_btn.config(state="normal")
                try:
                    self.scheduler_service.restart()
                    self._add_log("✅ Configuración de programación actualizada")
                except Exception as e:
                    self._add_log(f"⚠️ Error al reiniciar programación automática: {e}")

            SchedulerModal(
                self.parent_frame,
                self.bottom_right_panel,
                on_close=on_close
            )

        except Exception as e:
            self.schedule_reports_btn.config(state="normal")
            self._add_log(f"❌ Error al abrir configuración de programación: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la configuración: {e}")

    def _check_operation_in_progress(self):
        """
        Verifica si hay una operación en progreso.

        Returns:
            bool: True si hay una operación en progreso, False en caso contrario
        """
        if self.is_searching or self.is_generating_report or self.is_generating_weekly_report or self.is_generating_monthly_report:
            messagebox.showwarning(
                "Operación en Progreso",
                "Hay una operación en curso. Espera a que termine antes de configurar la programación."
            )
            return True
        return False

    def _edit_profile(self, profile):
        """Abre el modal para editar un perfil."""
        if self.bottom_right_panel:
            criterios_count = len(profile.search_criteria)
            bot_type_text = "Automático" if profile.is_bot_automatic() else "Manual"
            optimal_text = f" (óptimo: {profile.optimal_executions})" if profile.track_optimal else ""
            sender_text = ""
            if profile.has_sender_filters():
                sender_text = f", remitentes: {len(profile.sender_filters)}"
            self.bottom_right_panel.add_log_entry(
                f"Editando perfil: {profile.name} [{bot_type_text}] ({criterios_count} criterios{optimal_text}{sender_text})"
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
        bot_type_text = "Automático" if profile.is_bot_automatic() else "Manual"

        optimal_text = ""
        if profile.track_optimal:
            optimal_text = f"\nSeguimiento óptimo: {profile.optimal_executions} ejecuciones"

        sender_text = ""
        if profile.has_sender_filters():
            sender_text = f"\nRemitentes filtrados: {', '.join(profile.sender_filters)}"

        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar el perfil '{profile.name}'?\n"
            f"Tipo de bot: {bot_type_text}\n"
            f"Se perderán {criterios_count} {criterios_text} de búsqueda.{optimal_text}{sender_text}",
            icon=messagebox.WARNING
        )

        if confirm:
            if self.profile_manager.delete_profile(profile.profile_id):
                if self.bottom_right_panel:
                    self.bottom_right_panel.add_log_entry(
                        f"Perfil eliminado: {profile.name} [{bot_type_text}] ({criterios_count} criterios)"
                    )
                self._load_profiles()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el perfil")

    def _run_global_search_async(self):
        """Ejecuta búsqueda global de manera asíncrona para prevenir bloqueos."""
        if self.is_searching or self.is_generating_report or self.is_generating_weekly_report or self.is_generating_monthly_report:
            messagebox.showwarning(
                "Operación en Progreso",
                "Ya hay una operación en curso. Espera a que termine."
            )
            return

        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles de búsqueda para ejecutar.")
            return

        # Marcar como en progreso y deshabilitar botones
        self.is_searching = True
        self._set_buttons_state("disabled")

        # Iniciar operación de progreso
        self.progress_service.start_operation(
            "Búsqueda Global de Correos",
            len(profiles),
            can_cancel=True
        )

        # Ejecutar en hilo separado
        def search_thread():
            try:
                self._perform_global_search_threaded(profiles)
            finally:
                # Rehabilitar botones y marcar como terminado
                self.parent_frame.after(0, lambda: self._finish_search_operation())

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _perform_global_search_threaded(self, profiles):
        """Ejecuta la búsqueda global en un hilo separado."""
        try:
            # Calcular estadísticas iniciales
            total_criterios = sum(len(p.search_criteria) for p in profiles)
            tracking_profiles = [p for p in profiles if p.track_optimal]
            automatic_bots = len([p for p in profiles if p.is_bot_automatic()])
            manual_bots = len([p for p in profiles if p.is_bot_manual()])

            self.progress_service.log_progress(
                f"🚀 Búsqueda global iniciada: {len(profiles)} perfiles "
                f"({automatic_bots} automáticos, {manual_bots} manuales), "
                f"{total_criterios} criterios"
            )

            total_found = 0
            profiles_searched = 0
            optimal_achieved = 0

            for i, profile in enumerate(profiles):
                # Verificar cancelación
                if self.progress_service.is_cancelled():
                    self.progress_service.log_progress("🛑 Búsqueda cancelada por el usuario")
                    return

                # Actualizar progreso
                self.progress_service.update_progress(
                    i + 1, len(profiles),
                    f"Buscando: {profile.name}..."
                )

                try:
                    # Ejecutar búsqueda para este perfil
                    found = self._run_search_threaded(profile)
                    total_found += found
                    profiles_searched += 1

                    # Contar perfiles que alcanzaron el óptimo
                    if profile.is_success_optimal():
                        optimal_achieved += 1

                    # Pequeña pausa para no saturar el servidor
                    time.sleep(0.5)

                except Exception as e:
                    self.progress_service.log_progress(f"⚠️ Error en perfil {profile.name}: {e}")
                    continue

            # Programar actualización de UI en el hilo principal
            self.parent_frame.after(0, self._load_profiles)

            # Completar operación
            success_message = (
                f"Búsqueda global completada: {total_found} ejecuciones encontradas, "
                f"{optimal_achieved}/{len(tracking_profiles)} perfiles alcanzaron óptimo"
            )

            self.progress_service.complete_operation(success_message)

            # Mostrar resultado
            self.parent_frame.after(0, lambda: self._show_search_results(
                profiles_searched, total_criterios, total_found,
                automatic_bots, manual_bots, tracking_profiles, optimal_achieved
            ))

        except Exception as e:
            error_msg = f"Error durante búsqueda global: {e}"
            self.progress_service.error_operation(error_msg)

    def _run_search_threaded(self, profile):
        """Ejecuta búsqueda para un perfil específico en hilo separado."""
        try:
            # Ejecutar búsqueda real usando el servicio mejorado
            total_found = self.search_service.search_emails(profile)

            # Actualizar resultados en el perfil
            self.profile_manager.update_search_results(profile.profile_id, total_found)

            return total_found

        except Exception as e:
            self.progress_service.log_progress(f"❌ Error en búsqueda de {profile.name}: {e}")
            return 0

    def _show_search_results(self, profiles_searched, total_criterios, total_found,
                             automatic_bots, manual_bots, tracking_profiles, optimal_achieved):
        """Muestra los resultados de la búsqueda global."""
        result_message = f"✅ Se han procesado {profiles_searched} perfiles.\n" \
                         f"Total de criterios buscados: {total_criterios}\n" \
                         f"Total de ejecuciones encontradas: {total_found}\n" \
                         f"Tipos de bot: {automatic_bots} automáticos, {manual_bots} manuales\n" \
                         f"Método: Búsqueda mejorada con verificación de timestamp"

        if tracking_profiles:
            success_rate = round((optimal_achieved / len(tracking_profiles)) * 100, 1) if tracking_profiles else 0
            result_message += f"\n\nSeguimiento óptimo:\n" \
                              f"• Perfiles con seguimiento: {len(tracking_profiles)}\n" \
                              f"• Perfiles que alcanzaron el óptimo: {optimal_achieved}\n" \
                              f"• Tasa de éxito: {success_rate}%"

        messagebox.showinfo("Búsqueda Global Completada", result_message)

    def _finish_search_operation(self):
        """Finaliza la operación de búsqueda y restaura la UI."""
        self.is_searching = False
        self._set_buttons_state("normal")

    def _generate_report_async(self):
        """Genera reporte de manera asíncrona para prevenir bloqueos."""
        if self.is_searching or self.is_generating_report or self.is_generating_weekly_report or self.is_generating_monthly_report:
            messagebox.showwarning(
                "Operación en Progreso",
                "Ya hay una operación en curso. Espera a que termine."
            )
            return

        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            messagebox.showinfo("Información", "No hay perfiles para generar reporte.")
            return

        # Marcar como en progreso y deshabilitar botones
        self.is_generating_report = True
        self._set_buttons_state("disabled")

        # Iniciar operación de progreso
        self.progress_service.start_operation(
            "Generación de Reporte con Datos Actualizados",
            len(profiles) + 2,  # Perfiles + generación + envío
            can_cancel=False
        )

        # Ejecutar en hilo separado
        def report_thread():
            try:
                self._perform_report_generation_threaded(profiles)
            finally:
                # Rehabilitar botones y marcar como terminado
                self.parent_frame.after(0, lambda: self._finish_report_operation())

        thread = threading.Thread(target=report_thread, daemon=True)
        thread.start()

    def _generate_weekly_report_async(self):
        """Genera reporte semanal de manera asíncrona para prevenir bloqueos."""
        if self.is_searching or self.is_generating_report or self.is_generating_weekly_report or self.is_generating_monthly_report:
            messagebox.showwarning(
                "Operación en Progreso",
                "Ya hay una operación en curso. Espera a que termine."
            )
            return

        # Marcar como en progreso y deshabilitar botones
        self.is_generating_weekly_report = True
        self._set_buttons_state("disabled")

        # Iniciar operación de progreso
        self.progress_service.start_operation(
            "Generación de Reporte Semanal",
            3,  # Búsqueda + generación + envío
            can_cancel=False
        )

        # Ejecutar en hilo separado
        def weekly_report_thread():
            try:
                self._perform_weekly_report_generation_threaded()
            finally:
                # Rehabilitar botones y marcar como terminado
                self.parent_frame.after(0, lambda: self._finish_weekly_report_operation())

        thread = threading.Thread(target=weekly_report_thread, daemon=True)
        thread.start()

    def _generate_monthly_report_async(self):
        """Genera reporte mensual de manera asíncrona para prevenir bloqueos."""
        if self.is_searching or self.is_generating_report or self.is_generating_weekly_report or self.is_generating_monthly_report:
            messagebox.showwarning(
                "Operación en Progreso",
                "Ya hay una operación en curso. Espera a que termine."
            )
            return

        # Marcar como en progreso y deshabilitar botones
        self.is_generating_monthly_report = True
        self._set_buttons_state("disabled")

        # Iniciar operación de progreso
        self.progress_service.start_operation(
            "Generación de Reporte Mensual",
            3,  # Búsqueda + generación + envío
            can_cancel=False
        )

        # Ejecutar en hilo separado
        def monthly_report_thread():
            try:
                self._perform_monthly_report_generation_threaded()
            finally:
                # Rehabilitar botones y marcar como terminado
                self.parent_frame.after(0, lambda: self._finish_monthly_report_operation())

        thread = threading.Thread(target=monthly_report_thread, daemon=True)
        thread.start()

    def _perform_report_generation_threaded(self, profiles):
        """Ejecuta la generación de reporte en un hilo separado."""
        try:
            summary = self.profile_manager.get_profiles_summary()
            automatic_bots = len([p for p in profiles if p.is_bot_automatic()])
            manual_bots = len([p for p in profiles if p.is_bot_manual()])

            self.progress_service.log_progress("=" * 50)
            self.progress_service.log_progress("📊 GENERACIÓN DE REPORTE CON DATOS ACTUALIZADOS")
            self.progress_service.log_progress("=" * 50)

            # PASO 1: Actualizar datos
            self.progress_service.update_progress(1, len(profiles) + 2, "Actualizando datos de perfiles...")
            self.progress_service.log_progress(
                f"📋 Actualizando {summary['total_profiles']} perfiles "
                f"({automatic_bots} automáticos, {manual_bots} manuales)"
            )

            # Ejecutar búsqueda silenciosa para actualizar datos
            total_updated = self._run_global_search_silent_threaded(profiles)

            # PASO 2: Generar reporte
            self.progress_service.update_progress(len(profiles) + 1, len(profiles) + 2, "Generando reporte Excel...")

            updated_profiles = self.profile_manager.get_all_profiles()
            updated_summary = self.profile_manager.get_profiles_summary()

            self.progress_service.log_progress(
                f"📈 Datos actualizados: {updated_summary['total_emails_found']} ejecuciones totales"
            )

            report_path = self.report_service.generate_profiles_report(updated_profiles)
            self.progress_service.log_progress(f"✅ Reporte generado: {report_path}")

            # PASO 3: Enviar por correo
            self.progress_service.update_progress(len(profiles) + 2, len(profiles) + 2, "Enviando por correo...")

            success = self.email_service.send_report(report_path)

            if success:
                success_message = (
                    f"Reporte con datos actualizados enviado exitosamente. "
                    f"Incluye {updated_summary['profiles_with_tracking']} perfiles con seguimiento óptimo"
                )
                self.progress_service.complete_operation(success_message)

                # Mostrar resultado
                self.parent_frame.after(0,
                                        lambda: self._show_report_results(updated_summary, automatic_bots, manual_bots))

            else:
                error_msg = "Reporte generado pero no se pudo enviar por correo"
                self.progress_service.error_operation(error_msg)

        except Exception as e:
            error_msg = f"Error durante generación de reporte: {e}"
            self.progress_service.error_operation(error_msg)

    def _perform_weekly_report_generation_threaded(self):
        """Ejecuta la generación de reporte semanal en un hilo separado."""
        try:
            self.progress_service.log_progress("=" * 50)
            self.progress_service.log_progress("📊 GENERACIÓN DE REPORTE SEMANAL")
            self.progress_service.log_progress("=" * 50)

            # PASO 1: Buscar reportes existentes
            self.progress_service.update_progress(1, 3, "Buscando reportes diarios de la semana...")

            # PASO 2: Generar reporte semanal
            self.progress_service.update_progress(2, 3, "Generando reporte semanal...")

            try:
                report_path = self.report_service.generate_weekly_profiles_report()
                self.progress_service.log_progress(f"✅ Reporte semanal generado: {report_path}")

                # PASO 3: Enviar por correo
                self.progress_service.update_progress(3, 3, "Enviando reporte semanal por correo...")

                # Aquí está el cambio: especificar report_type="weekly"
                success = self.email_service.send_report(report_path, report_type="weekly")

                if success:
                    success_message = f"Reporte semanal enviado exitosamente: {report_path}"
                    self.progress_service.complete_operation(success_message)

                    # Mostrar resultado
                    self.parent_frame.after(0, lambda: self._show_weekly_report_results(report_path))
                else:
                    error_msg = "Reporte semanal generado pero no se pudo enviar por correo"
                    self.progress_service.error_operation(error_msg)

            except Exception as e:
                error_msg = f"Error generando reporte semanal: {str(e)}"
                self.progress_service.error_operation(error_msg)
                self.parent_frame.after(0, lambda: messagebox.showerror("Error", error_msg))

        except Exception as e:
            error_msg = f"Error durante generación de reporte semanal: {e}"
            self.progress_service.error_operation(error_msg)

    def _perform_monthly_report_generation_threaded(self):
        """Ejecuta la generación de reporte mensual en un hilo separado."""
        try:
            self.progress_service.log_progress("=" * 50)
            self.progress_service.log_progress("📊 GENERACIÓN DE REPORTE MENSUAL")
            self.progress_service.log_progress("=" * 50)

            # PASO 1: Buscar reportes existentes
            self.progress_service.update_progress(1, 3, "Buscando reportes diarios del mes...")

            # PASO 2: Generar reporte mensual
            self.progress_service.update_progress(2, 3, "Generando reporte mensual...")

            try:
                report_path = self.report_service.generate_monthly_profiles_report()
                self.progress_service.log_progress(f"✅ Reporte mensual generado: {report_path}")

                # PASO 3: Enviar por correo
                self.progress_service.update_progress(3, 3, "Enviando reporte mensual por correo...")

                # Especificar report_type="monthly"
                success = self.email_service.send_report(report_path, report_type="monthly")

                if success:
                    success_message = f"Reporte mensual enviado exitosamente: {report_path}"
                    self.progress_service.complete_operation(success_message)

                    # Mostrar resultado
                    self.parent_frame.after(0, lambda: self._show_monthly_report_results(report_path))
                else:
                    error_msg = "Reporte mensual generado pero no se pudo enviar por correo"
                    self.progress_service.error_operation(error_msg)

            except Exception as e:
                error_msg = f"Error generando reporte mensual: {str(e)}"
                self.progress_service.error_operation(error_msg)
                self.parent_frame.after(0, lambda: messagebox.showerror("Error", error_msg))

        except Exception as e:
            error_msg = f"Error durante generación de reporte mensual: {e}"
            self.progress_service.error_operation(error_msg)

    def _run_global_search_silent_threaded(self, profiles):
        """Ejecuta búsqueda global silenciosa en hilo separado."""
        total_found = 0
        optimal_achieved = 0

        for i, profile in enumerate(profiles):
            self.progress_service.update_progress(i + 1, len(profiles), f"Actualizando: {profile.name}...")

            found = self._run_search_threaded(profile)
            total_found += found

            if profile.is_success_optimal():
                optimal_achieved += 1

            # Pequeña pausa
            time.sleep(0.3)

        # Programar actualización de UI
        self.parent_frame.after(0, self._load_profiles)

        self.progress_service.log_progress(
            f"🔄 Actualización completa: {total_found} ejecuciones encontradas, "
            f"{optimal_achieved} perfiles alcanzaron óptimo"
        )

        return total_found

    def _show_report_results(self, updated_summary, automatic_bots, manual_bots):
        """Muestra los resultados de la generación de reporte."""
        messagebox.showinfo(
            "✅ Reporte Actualizado Enviado",
            f"Reporte generado y enviado correctamente.\n\n"
            f"Datos incluidos:\n"
            f"• Total ejecuciones: {updated_summary['total_emails_found']}\n"
            f"• Perfiles óptimos: {updated_summary['optimal_profiles']}\n"
            f"• Bots automáticos: {automatic_bots}\n"
            f"• Bots manuales: {manual_bots}\n"
            f"• Búsqueda mejorada: Con verificación de timestamp"
        )

    def _show_weekly_report_results(self, report_path):
        """Muestra los resultados de la generación de reporte semanal."""
        messagebox.showinfo(
            "✅ Reporte Semanal Enviado",
            f"Reporte semanal generado y enviado correctamente.\n\n"
            f"El reporte semanal contiene los datos acumulados\n"
            f"de todos los reportes diarios de la semana actual.\n\n"
            f"Ruta del archivo: {report_path}"
        )

    def _show_monthly_report_results(self, report_path):
        """Muestra los resultados de la generación de reporte mensual."""
        messagebox.showinfo(
            "✅ Reporte Mensual Enviado",
            f"Reporte mensual generado y enviado correctamente.\n\n"
            f"El reporte mensual contiene los datos acumulados\n"
            f"de todos los reportes diarios del mes actual, con\n"
            f"análisis de tendencias y comparativas mensuales.\n\n"
            f"Ruta del archivo: {report_path}"
        )

    def _finish_report_operation(self):
        """Finaliza la operación de reporte y restaura la UI."""
        self.is_generating_report = False
        self._set_buttons_state("normal")

    def _finish_weekly_report_operation(self):
        """Finaliza la operación de reporte semanal y restaura la UI."""
        self.is_generating_weekly_report = False
        self._set_buttons_state("normal")

    def _finish_monthly_report_operation(self):
        """Finaliza la operación de reporte mensual y restaura la UI."""
        self.is_generating_monthly_report = False
        self._set_buttons_state("normal")

    def _set_buttons_state(self, state):
        """Cambia el estado de todos los botones principales."""
        buttons = [
            self.generate_report_btn,
            self.generate_weekly_report_btn,
            self.generate_monthly_report_btn,
            self.schedule_reports_btn,
            self.search_all_btn,
            self.new_btn
        ]
        for btn in buttons:
            btn.config(state=state)

    def _generate_scheduled_report(self):
        """
        Genera y envía reporte diario programado sin interacción del usuario.

        Returns:
            bool: True si se generó correctamente, False en caso contrario
        """
        profiles = self.profile_manager.get_all_profiles()

        if not profiles:
            self._add_log("No hay perfiles para generar reporte diario programado")
            return False

        summary = self.profile_manager.get_profiles_summary()
        automatic_bots = len([p for p in profiles if p.is_bot_automatic()])
        manual_bots = len([p for p in profiles if p.is_bot_manual()])

        self._add_log("=" * 40)
        self._add_log("📅 REPORTE DIARIO PROGRAMADO INICIADO")

        try:
            # Actualizar datos antes de generar reporte programado
            self._add_log("🔄 Actualizando datos para reporte diario programado...")

            # Ejecutar búsqueda silenciosa en el hilo principal (para reportes programados)
            total_updated = 0
            for profile in profiles:
                try:
                    found = self.search_service.search_emails(profile)
                    self.profile_manager.update_search_results(profile.profile_id, found)
                    total_updated += found
                except Exception as e:
                    self._add_log(f"⚠️ Error en perfil {profile.name}: {e}")

            # Generar archivo Excel con datos actualizados
            updated_profiles = self.profile_manager.get_all_profiles()
            updated_summary = self.profile_manager.get_profiles_summary()

            report_path = self.report_service.generate_profiles_report(updated_profiles)
            self._add_log(f"📊 Reporte diario programado generado: {report_path}")

            # Enviar por correo
            success = self.email_service.send_report(report_path)

            if success:
                optimal_count = updated_summary['optimal_profiles']
                self._add_log(
                    f"✅ Reporte diario programado enviado con datos actualizados "
                    f"({optimal_count} perfiles óptimos, {total_updated} ejecuciones totales)"
                )
                self._add_log("=" * 40)
                return True
            else:
                self._add_log("❌ Error al enviar reporte diario programado por correo")
                return False

        except Exception as e:
            error_msg = f"💥 Error al generar reporte diario programado: {e}"
            self._add_log(error_msg)
            return False

    def _generate_scheduled_weekly_report(self):
        """
        Genera y envía reporte semanal programado sin interacción del usuario.

        Returns:
            bool: True si se generó correctamente, False en caso contrario
        """
        self._add_log("=" * 40)
        self._add_log("📅 REPORTE SEMANAL PROGRAMADO INICIADO")

        try:
            # Generar reporte semanal
            self._add_log("📊 Generando reporte semanal programado...")

            try:
                report_path = self.report_service.generate_weekly_profiles_report()
                self._add_log(f"✅ Reporte semanal programado generado: {report_path}")

                # Enviar por correo - Aquí está el cambio
                success = self.email_service.send_report(report_path, report_type="weekly")

                if success:
                    self._add_log(f"✉️ Reporte semanal programado enviado: {report_path}")
                    self._add_log("=" * 40)
                    return True
                else:
                    self._add_log("❌ Error al enviar reporte semanal programado por correo")
                    return False

            except Exception as e:
                error_msg = f"Error generando reporte semanal programado: {str(e)}"
                self._add_log(error_msg)
                return False

        except Exception as e:
            error_msg = f"💥 Error durante generación de reporte semanal programado: {e}"
            self._add_log(error_msg)
            return False

    def _generate_scheduled_monthly_report(self):
        """
        Genera y envía reporte mensual programado sin interacción del usuario.

        Returns:
            bool: True si se generó correctamente, False en caso contrario
        """
        self._add_log("=" * 40)
        self._add_log("📅 REPORTE MENSUAL PROGRAMADO INICIADO")

        try:
            # Generar reporte mensual
            self._add_log("📊 Generando reporte mensual programado...")

            try:
                report_path = self.report_service.generate_monthly_profiles_report()
                self._add_log(f"✅ Reporte mensual programado generado: {report_path}")

                # Enviar por correo - Especificar report_type="monthly"
                success = self.email_service.send_report(report_path, report_type="monthly")

                if success:
                    self._add_log(f"✉️ Reporte mensual programado enviado: {report_path}")
                    self._add_log("=" * 40)
                    return True
                else:
                    self._add_log("❌ Error al enviar reporte mensual programado por correo")
                    return False

            except Exception as e:
                error_msg = f"Error generando reporte mensual programado: {str(e)}"
                self._add_log(error_msg)
                return False

        except Exception as e:
            error_msg = f"💥 Error durante generación de reporte mensual programado: {e}"
            self._add_log(error_msg)
            return False

    def _add_log(self, message):
        """Agrega mensaje al log de manera thread-safe."""
        if self.bottom_right_panel:
            # Si estamos en un hilo diferente, programar la actualización en el hilo principal
            if threading.current_thread() != threading.main_thread():
                self.parent_frame.after(0, lambda: self.bottom_right_panel.add_log_entry(message))
            else:
                self.bottom_right_panel.add_log_entry(message)

    def get_data(self):
        """Retorna los datos actuales del panel."""
        summary = self.profile_manager.get_profiles_summary()
        profiles = self.profile_manager.get_all_profiles()
        automatic_bots = len([p for p in profiles if p.is_bot_automatic()])
        manual_bots = len([p for p in profiles if p.is_bot_manual()])

        return {
            "panel_type": "top_panel",
            "profiles_count": summary['total_profiles'],
            "total_criteria": summary['total_criteria'],
            "active_profiles": summary['active_profiles'],
            "total_emails_found": summary['total_emails_found'],
            "profiles_with_tracking": summary['profiles_with_tracking'],
            "optimal_profiles": summary['optimal_profiles'],
            "avg_success_percentage": summary['avg_success_percentage'],
            "automatic_bots": automatic_bots,
            "manual_bots": manual_bots,
            "enhanced_search": True,
            "weekly_reports": True,
            "monthly_reports": True,
            "daily_scheduler": True,
            "weekly_scheduler": True,
            "monthly_scheduler": True,
            "unified_scheduler": True,
            "optimized_ui": True
        }