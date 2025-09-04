# services/report_service.py
"""
Servicio para generar reportes Excel optimizados de perfiles de búsqueda.
Crea archivos Excel limpios con información esencial de los perfiles,
incluyendo seguimiento de ejecuciones óptimas con formato condicional verde.
"""

import os
from pathlib import Path
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import CellIsRule
except ImportError:
    openpyxl = None


class ReportService:
    """Servicio para generar reportes optimizados en formato Excel con seguimiento de ejecuciones óptimas."""

    def __init__(self):
        """Inicializa el servicio de reportes."""
        self.reports_dir = Path("reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_profiles_report(self, profiles):
        """
        Genera un reporte Excel optimizado con información esencial de perfiles,
        incluyendo seguimiento de ejecuciones óptimas con colores condicionales.

        Args:
            profiles (list): Lista de perfiles de búsqueda

        Returns:
            str: Ruta del archivo Excel generado

        Raises:
            Exception: Si openpyxl no está instalado o hay error en la generación
        """
        if openpyxl is None:
            raise Exception("openpyxl no está instalado. Ejecute: pip install openpyxl")

        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_perfiles_{timestamp}.xlsx"
        file_path = self.reports_dir / filename

        # Crear libro de trabajo
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Perfiles de Búsqueda"

        # Configurar estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Estilo para éxito óptimo (verde)
        success_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
        success_font = Font(bold=True, color="006400")

        border_style = Side(border_style="thin", color="000000")
        border = Border(top=border_style, bottom=border_style, left=border_style, right=border_style)

        # Configurar encabezados ampliados (incluyendo nuevas columnas)
        headers = [
            "Nombre del Perfil",
            "Cantidad de ejecuciones",  # CAMBIADO: antes "Correos Encontrados"
            "Ejecuciones Óptimas",  # NUEVA COLUMNA
            "Porcentaje de Éxito",  # NUEVA COLUMNA
            "Última Búsqueda"
        ]

        # Escribir encabezados
        for col_num, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # Escribir datos de perfiles (incluyendo nueva información)
        for row_num, profile in enumerate(profiles, 2):
            # Nombre del Perfil
            cell = worksheet.cell(row=row_num, column=1)
            cell.value = profile.name
            cell.border = border

            # Cantidad de ejecuciones (antes "Correos Encontrados")
            cell = worksheet.cell(row=row_num, column=2)
            cell.value = profile.found_emails
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Ejecuciones Óptimas (NUEVA COLUMNA)
            cell = worksheet.cell(row=row_num, column=3)
            cell.value = profile.get_optimal_display()
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Porcentaje de Éxito (NUEVA COLUMNA)
            cell = worksheet.cell(row=row_num, column=4)
            success_display = profile.get_success_display()
            cell.value = success_display
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Aplicar formato condicional verde si es óptimo (≥100%)
            if profile.is_success_optimal():
                cell.fill = success_fill
                cell.font = success_font
                cell.value = f"✅ {success_display}"

            # Última Búsqueda
            cell = worksheet.cell(row=row_num, column=5)
            if profile.last_search:
                cell.value = profile.last_search.strftime("%d/%m/%Y %H:%M:%S")
            else:
                cell.value = "Nunca"
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

        # Ajustar ancho de columnas optimizado (redistribuido para nuevas columnas)
        column_widths = {
            1: 30,  # Nombre del Perfil
            2: 20,  # Cantidad de ejecuciones
            3: 20,  # Ejecuciones Óptimas (NUEVA)
            4: 18,  # Porcentaje de Éxito (NUEVA)
            5: 22  # Última Búsqueda
        }

        for col_num, width in column_widths.items():
            worksheet.column_dimensions[get_column_letter(col_num)].width = width

        # Agregar hoja de resumen ampliada
        summary_sheet = workbook.create_sheet("Resumen")
        self._add_summary_sheet(summary_sheet, profiles)

        # Guardar archivo
        workbook.save(file_path)

        return str(file_path)

    def _add_summary_sheet(self, worksheet, profiles):
        """
        Agrega hoja de resumen optimizada al reporte incluyendo métricas de seguimiento óptimo.

        Args:
            worksheet: Hoja de trabajo de Excel
            profiles (list): Lista de perfiles
        """
        # Título principal
        worksheet.cell(row=1, column=1).value = "RESUMEN EJECUTIVO"
        worksheet.cell(row=1, column=1).font = Font(bold=True, size=16, color="366092")
        worksheet.merge_cells('A1:B1')

        # Información general
        worksheet.cell(row=3, column=1).value = "Fecha de generación:"
        worksheet.cell(row=3, column=1).font = Font(bold=True)
        worksheet.cell(row=3, column=2).value = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        worksheet.cell(row=4, column=1).value = "Total de perfiles:"
        worksheet.cell(row=4, column=1).font = Font(bold=True)
        worksheet.cell(row=4, column=2).value = len(profiles)

        # Estadísticas principales
        active_profiles = len([p for p in profiles if p.last_search])
        inactive_profiles = len(profiles) - active_profiles
        total_executions = sum(p.found_emails for p in profiles)  # Cambio de terminología
        total_criteria = sum(len(p.search_criteria) for p in profiles)

        worksheet.cell(row=6, column=1).value = "MÉTRICAS PRINCIPALES"
        worksheet.cell(row=6, column=1).font = Font(bold=True, size=14, color="366092")

        worksheet.cell(row=7, column=1).value = "Perfiles activos:"
        worksheet.cell(row=7, column=1).font = Font(bold=True)
        worksheet.cell(row=7, column=2).value = active_profiles

        worksheet.cell(row=8, column=1).value = "Perfiles sin usar:"
        worksheet.cell(row=8, column=1).font = Font(bold=True)
        worksheet.cell(row=8, column=2).value = inactive_profiles

        worksheet.cell(row=9, column=1).value = "Total ejecuciones encontradas:"  # CAMBIADO
        worksheet.cell(row=9, column=1).font = Font(bold=True)
        worksheet.cell(row=9, column=2).value = total_executions

        worksheet.cell(row=10, column=1).value = "Total criterios configurados:"
        worksheet.cell(row=10, column=1).font = Font(bold=True)
        worksheet.cell(row=10, column=2).value = total_criteria

        # Métrica adicional existente
        if active_profiles > 0:
            avg_executions = total_executions / active_profiles
            worksheet.cell(row=11, column=1).value = "Promedio ejecuciones por perfil activo:"  # CAMBIADO
            worksheet.cell(row=11, column=1).font = Font(bold=True)
            worksheet.cell(row=11, column=2).value = round(avg_executions, 2)

        # NUEVAS MÉTRICAS DE SEGUIMIENTO ÓPTIMO
        profiles_with_tracking = [p for p in profiles if p.track_optimal]
        optimal_profiles = [p for p in profiles_with_tracking if p.is_success_optimal()]

        if profiles_with_tracking:
            worksheet.cell(row=13, column=1).value = "SEGUIMIENTO DE EJECUCIONES ÓPTIMAS"
            worksheet.cell(row=13, column=1).font = Font(bold=True, size=14, color="006400")

            worksheet.cell(row=14, column=1).value = "Perfiles con seguimiento óptimo:"
            worksheet.cell(row=14, column=1).font = Font(bold=True)
            worksheet.cell(row=14, column=2).value = len(profiles_with_tracking)

            worksheet.cell(row=15, column=1).value = "Perfiles que alcanzaron el óptimo:"
            worksheet.cell(row=15, column=1).font = Font(bold=True)
            worksheet.cell(row=15, column=2).value = len(optimal_profiles)

            # Tasa de éxito general
            success_rate = (len(optimal_profiles) / len(profiles_with_tracking)) * 100
            worksheet.cell(row=16, column=1).value = "Tasa de éxito general:"
            worksheet.cell(row=16, column=1).font = Font(bold=True)
            worksheet.cell(row=16, column=2).value = f"{round(success_rate, 1)}%"

            # Aplicar color verde si la tasa es alta
            if success_rate >= 80:
                worksheet.cell(row=16, column=2).fill = PatternFill(start_color="90EE90", end_color="90EE90",
                                                                    fill_type="solid")
                worksheet.cell(row=16, column=2).font = Font(bold=True, color="006400")

            # Promedio de porcentaje de éxito
            success_percentages = []
            for profile in profiles_with_tracking:
                percentage = profile.get_success_percentage()
                if percentage is not None:
                    success_percentages.append(percentage)

            if success_percentages:
                avg_success = sum(success_percentages) / len(success_percentages)
                worksheet.cell(row=17, column=1).value = "Promedio de porcentaje de éxito:"
                worksheet.cell(row=17, column=1).font = Font(bold=True)
                worksheet.cell(row=17, column=2).value = f"{round(avg_success, 1)}%"

        # Top 3 perfiles más productivos (actualizado)
        if profiles:
            start_row = 19 if profiles_with_tracking else 13
            worksheet.cell(row=start_row, column=1).value = "TOP 3 PERFILES MÁS PRODUCTIVOS"
            worksheet.cell(row=start_row, column=1).font = Font(bold=True, size=12, color="366092")

            # Ordenar perfiles por ejecuciones encontradas
            sorted_profiles = sorted(profiles, key=lambda p: p.found_emails, reverse=True)[:3]

            for i, profile in enumerate(sorted_profiles, 1):
                row = start_row + i
                profile_text = f"{i}. {profile.name}"
                executions_text = f"{profile.found_emails} ejecuciones"  # CAMBIADO

                # Agregar información de éxito si está disponible
                if profile.track_optimal:
                    success_percentage = profile.get_success_percentage()
                    if success_percentage is not None:
                        executions_text += f" ({success_percentage}% éxito)"
                        if profile.is_success_optimal():
                            executions_text += " ✅"

                worksheet.cell(row=row, column=1).value = profile_text
                worksheet.cell(row=row, column=2).value = executions_text

        # Ajustar ancho de columnas
        worksheet.column_dimensions['A'].width = 40
        worksheet.column_dimensions['B'].width = 30

        # Agregar bordes a las celdas principales
        max_row = 20 if profiles_with_tracking else 17
        for row in range(1, max_row):
            for col in range(1, 3):
                cell = worksheet.cell(row=row, column=col)
                if cell.value:
                    cell.border = Border(
                        left=Side(border_style="thin"),
                        right=Side(border_style="thin"),
                        top=Side(border_style="thin"),
                        bottom=Side(border_style="thin")
                    )

    def get_reports_directory(self):
        """
        Retorna el directorio donde se guardan los reportes.

        Returns:
            str: Ruta del directorio de reportes
        """
        return str(self.reports_dir)