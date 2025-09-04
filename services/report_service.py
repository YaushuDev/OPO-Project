# services/report_service.py
"""
Servicio para generar reportes Excel optimizados de perfiles de búsqueda.
Crea archivos Excel limpios con información esencial de los perfiles.
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
    """Servicio para generar reportes optimizados en formato Excel."""

    def __init__(self):
        """Inicializa el servicio de reportes."""
        self.reports_dir = Path("reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_profiles_report(self, profiles):
        """
        Genera un reporte Excel optimizado con información esencial de perfiles.

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

        # Configurar encabezados optimizados (solo campos esenciales)
        headers = [
            "Nombre del Perfil",
            "Correos Encontrados",
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

        # Escribir datos de perfiles (solo información esencial)
        for row_num, profile in enumerate(profiles, 2):
            # Nombre del Perfil
            cell = worksheet.cell(row=row_num, column=1)
            cell.value = profile.name
            cell.border = border

            # Correos Encontrados
            cell = worksheet.cell(row=row_num, column=2)
            cell.value = profile.found_emails
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Última Búsqueda
            cell = worksheet.cell(row=row_num, column=3)
            if profile.last_search:
                cell.value = profile.last_search.strftime("%d/%m/%Y %H:%M:%S")
            else:
                cell.value = "Nunca"
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

        # Ajustar ancho de columnas optimizado
        column_widths = {
            1: 35,  # Nombre del Perfil
            2: 20,  # Correos Encontrados
            3: 25   # Última Búsqueda
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
        Agrega hoja de resumen optimizada al reporte.

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
        total_emails_found = sum(p.found_emails for p in profiles)
        total_criteria = sum(len(p.search_criteria) for p in profiles)

        worksheet.cell(row=6, column=1).value = "MÉTRICAS PRINCIPALES"
        worksheet.cell(row=6, column=1).font = Font(bold=True, size=14, color="366092")

        worksheet.cell(row=7, column=1).value = "Perfiles activos:"
        worksheet.cell(row=7, column=1).font = Font(bold=True)
        worksheet.cell(row=7, column=2).value = active_profiles

        worksheet.cell(row=8, column=1).value = "Perfiles sin usar:"
        worksheet.cell(row=8, column=1).font = Font(bold=True)
        worksheet.cell(row=8, column=2).value = inactive_profiles

        worksheet.cell(row=9, column=1).value = "Total correos encontrados:"
        worksheet.cell(row=9, column=1).font = Font(bold=True)
        worksheet.cell(row=9, column=2).value = total_emails_found

        worksheet.cell(row=10, column=1).value = "Total criterios configurados:"
        worksheet.cell(row=10, column=1).font = Font(bold=True)
        worksheet.cell(row=10, column=2).value = total_criteria

        # Métricas adicionales
        if active_profiles > 0:
            avg_emails = total_emails_found / active_profiles
            worksheet.cell(row=11, column=1).value = "Promedio correos por perfil activo:"
            worksheet.cell(row=11, column=1).font = Font(bold=True)
            worksheet.cell(row=11, column=2).value = round(avg_emails, 2)

        # Top 3 perfiles más productivos
        if profiles:
            worksheet.cell(row=13, column=1).value = "TOP 3 PERFILES MÁS PRODUCTIVOS"
            worksheet.cell(row=13, column=1).font = Font(bold=True, size=12, color="366092")

            # Ordenar perfiles por correos encontrados
            sorted_profiles = sorted(profiles, key=lambda p: p.found_emails, reverse=True)[:3]

            for i, profile in enumerate(sorted_profiles, 1):
                row = 13 + i
                worksheet.cell(row=row, column=1).value = f"{i}. {profile.name}"
                worksheet.cell(row=row, column=2).value = f"{profile.found_emails} correos"

        # Ajustar ancho de columnas
        worksheet.column_dimensions['A'].width = 35
        worksheet.column_dimensions['B'].width = 25

        # Agregar bordes a las celdas principales
        for row in range(1, 17):
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