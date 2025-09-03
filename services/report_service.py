# services/report_service.py
"""
Servicio para generar reportes Excel de perfiles de búsqueda.
Crea archivos Excel con información detallada de los perfiles.
"""

import os
from pathlib import Path
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    openpyxl = None


class ReportService:
    """Servicio para generar reportes en formato Excel."""

    def __init__(self):
        """Inicializa el servicio de reportes."""
        self.reports_dir = Path("reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_profiles_report(self, profiles):
        """
        Genera un reporte Excel con información de perfiles.

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

        border_style = Side(border_style="thin", color="000000")
        border = Border(top=border_style, bottom=border_style, left=border_style, right=border_style)

        # Configurar encabezados
        headers = [
            "ID del Perfil",
            "Nombre del Perfil",
            "Criterio de Búsqueda",
            "Correos Encontrados",
            "Última Búsqueda",
            "Estado"
        ]

        # Escribir encabezados
        for col_num, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # Escribir datos de perfiles
        for row_num, profile in enumerate(profiles, 2):
            # ID del Perfil
            cell = worksheet.cell(row=row_num, column=1)
            cell.value = profile.profile_id
            cell.border = border

            # Nombre del Perfil
            cell = worksheet.cell(row=row_num, column=2)
            cell.value = profile.name
            cell.border = border

            # Criterio de Búsqueda
            cell = worksheet.cell(row=row_num, column=3)
            cell.value = profile.search_criteria
            cell.border = border

            # Correos Encontrados
            cell = worksheet.cell(row=row_num, column=4)
            cell.value = profile.found_emails
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Última Búsqueda
            cell = worksheet.cell(row=row_num, column=5)
            if profile.last_search:
                cell.value = profile.last_search.strftime("%d/%m/%Y %H:%M:%S")
            else:
                cell.value = "Nunca"
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Estado
            cell = worksheet.cell(row=row_num, column=6)
            if profile.last_search:
                cell.value = "Activo"
                cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            else:
                cell.value = "Sin usar"
                cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

        # Ajustar ancho de columnas
        column_widths = {
            1: 30,  # ID del Perfil
            2: 25,  # Nombre del Perfil
            3: 35,  # Criterio de Búsqueda
            4: 18,  # Correos Encontrados
            5: 20,  # Última Búsqueda
            6: 15  # Estado
        }

        for col_num, width in column_widths.items():
            worksheet.column_dimensions[get_column_letter(col_num)].width = width

        # Agregar hoja de resumen
        summary_sheet = workbook.create_sheet("Resumen")
        self._add_summary_sheet(summary_sheet, profiles)

        # Guardar archivo
        workbook.save(file_path)

        return str(file_path)

    def _add_summary_sheet(self, worksheet, profiles):
        """
        Agrega hoja de resumen al reporte.

        Args:
            worksheet: Hoja de trabajo de Excel
            profiles (list): Lista de perfiles
        """
        # Título
        worksheet.cell(row=1, column=1).value = "RESUMEN DEL REPORTE"
        worksheet.cell(row=1, column=1).font = Font(bold=True, size=16)

        # Información general
        worksheet.cell(row=3, column=1).value = "Fecha de generación:"
        worksheet.cell(row=3, column=2).value = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        worksheet.cell(row=4, column=1).value = "Total de perfiles:"
        worksheet.cell(row=4, column=2).value = len(profiles)

        # Estadísticas
        active_profiles = len([p for p in profiles if p.last_search])
        inactive_profiles = len(profiles) - active_profiles
        total_emails_found = sum(p.found_emails for p in profiles)

        worksheet.cell(row=6, column=1).value = "ESTADÍSTICAS"
        worksheet.cell(row=6, column=1).font = Font(bold=True, size=14)

        worksheet.cell(row=7, column=1).value = "Perfiles activos:"
        worksheet.cell(row=7, column=2).value = active_profiles

        worksheet.cell(row=8, column=1).value = "Perfiles sin usar:"
        worksheet.cell(row=8, column=2).value = inactive_profiles

        worksheet.cell(row=9, column=1).value = "Total correos encontrados:"
        worksheet.cell(row=9, column=2).value = total_emails_found

        if active_profiles > 0:
            avg_emails = total_emails_found / active_profiles
            worksheet.cell(row=10, column=1).value = "Promedio correos por perfil activo:"
            worksheet.cell(row=10, column=2).value = round(avg_emails, 2)

        # Ajustar ancho de columnas
        worksheet.column_dimensions['A'].width = 30
        worksheet.column_dimensions['B'].width = 20

    def get_reports_directory(self):
        """
        Retorna el directorio donde se guardan los reportes.

        Returns:
            str: Ruta del directorio de reportes
        """
        return str(self.reports_dir)