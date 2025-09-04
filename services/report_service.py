# report_service.py
"""
Servicio para generar reportes Excel optimizados de perfiles de búsqueda.
Crea archivos Excel con título general, información esencial de los perfiles,
seguimiento de ejecuciones óptimas con formato condicional por rangos y tipo de bot.
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
    """Servicio para generar reportes optimizados en formato Excel con seguimiento de ejecuciones óptimas y tipo de bot."""

    def __init__(self):
        """Inicializa el servicio de reportes."""
        self.reports_dir = Path("reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_profiles_report(self, profiles):
        """
        Genera un reporte Excel optimizado con título general e información esencial de perfiles,
        incluyendo seguimiento de ejecuciones óptimas con colores condicionales por rangos y tipo de bot.

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

        # Configurar estilos con colores aRGB corregidos
        # Estilo para título principal
        title_font = Font(bold=True, size=16, color="FFFFFF")
        title_fill = PatternFill(start_color="FF2E5090", end_color="FF2E5090", fill_type="solid")
        title_alignment = Alignment(horizontal="center", vertical="center")

        # Estilo para subtítulo
        subtitle_font = Font(bold=True, size=12, color="000000")
        subtitle_alignment = Alignment(horizontal="center", vertical="center")

        # Estilo para encabezados de tabla
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="FF366092", end_color="FF366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # NUEVOS ESTILOS PARA PORCENTAJE DE ÉXITO POR RANGOS
        # 100%: Verde
        success_100_fill = PatternFill(start_color="FF90EE90", end_color="FF90EE90", fill_type="solid")
        success_100_font = Font(bold=True, color="006400")

        # 90-50%: Morado
        success_90_50_fill = PatternFill(start_color="FFE6E6FA", end_color="FFE6E6FA", fill_type="solid")
        success_90_50_font = Font(bold=True, color="800080")

        # 50-30%: Amarillo
        success_50_30_fill = PatternFill(start_color="FFFFFF99", end_color="FFFFFF99", fill_type="solid")
        success_50_30_font = Font(bold=True, color="B8860B")

        # <30%: Rojo
        success_low_fill = PatternFill(start_color="FFFFCCCC", end_color="FFFFCCCC", fill_type="solid")
        success_low_font = Font(bold=True, color="CC0000")

        # NUEVO ESTILO PARA TIPOS DE BOT: ROSA UNIFORME
        bot_fill = PatternFill(start_color="FFFFC0CB", end_color="FFFFC0CB", fill_type="solid")  # Rosa claro
        bot_font = Font(bold=True, color="C71585")  # Rosa oscuro/magenta

        border_style = Side(border_style="thin", color="000000")
        border = Border(top=border_style, bottom=border_style, left=border_style, right=border_style)

        # === AGREGAR TÍTULO GENERAL (FILAS 1 Y 2) ===

        # Fila 1: Título principal
        worksheet.merge_cells('A1:G1')
        title_cell = worksheet['A1']
        title_cell.value = "Reporte de Ejecuciones - Registro Diario"
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = title_alignment
        title_cell.border = border

        # Aplicar borde a todas las celdas del título fusionado
        for col in range(1, 8):  # A1 hasta G1
            cell = worksheet.cell(row=1, column=col)
            cell.border = border

        # Fila 2: Información de generación
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        total_bots = len(profiles)

        worksheet.merge_cells('A2:G2')
        subtitle_cell = worksheet['A2']
        subtitle_cell.value = f"Generado el {current_date} - Total de Bots: {total_bots}"
        subtitle_cell.font = subtitle_font
        subtitle_cell.alignment = subtitle_alignment

        # Aplicar borde a todas las celdas del subtítulo fusionado
        for col in range(1, 8):  # A2 hasta G2
            cell = worksheet.cell(row=2, column=col)
            cell.border = border

        # Fila vacía de separación
        worksheet.row_dimensions[3].height = 10

        # === CONFIGURAR ENCABEZADOS DE TABLA (FILA 4) ===
        headers = [
            "Nombre del Perfil",
            "Cantidad de ejecuciones",
            "Ejecuciones Óptimas",
            "Porcentaje de Éxito",
            "Bot Automático",
            "Bot Manual",
            "Última Búsqueda"
        ]

        # Escribir encabezados en fila 4
        for col_num, header in enumerate(headers, 1):
            cell = worksheet.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # === ESCRIBIR DATOS DE PERFILES (DESDE FILA 5) ===
        for row_num, profile in enumerate(profiles, 5):
            # Nombre del Perfil
            cell = worksheet.cell(row=row_num, column=1)
            cell.value = profile.name
            cell.border = border

            # Cantidad de ejecuciones
            cell = worksheet.cell(row=row_num, column=2)
            cell.value = profile.found_emails
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Ejecuciones Óptimas
            cell = worksheet.cell(row=row_num, column=3)
            cell.value = profile.get_optimal_display()
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # PORCENTAJE DE ÉXITO CON COLORES POR RANGOS
            cell = worksheet.cell(row=row_num, column=4)
            success_display = profile.get_success_display()
            success_percentage = profile.get_success_percentage()

            cell.value = success_display
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Aplicar formato condicional por rangos
            if success_percentage is not None:
                if success_percentage >= 100.0:
                    # 100%: Verde con ✅
                    cell.fill = success_100_fill
                    cell.font = success_100_font
                    cell.value = f"✅ {success_display}"
                elif success_percentage >= 90.0:
                    # 90-99%: Morado con 📊
                    cell.fill = success_90_50_fill
                    cell.font = success_90_50_font
                    cell.value = f"📊 {success_display}"
                elif success_percentage >= 50.0:
                    # 50-89%: Morado con 📊
                    cell.fill = success_90_50_fill
                    cell.font = success_90_50_font
                    cell.value = f"📊 {success_display}"
                elif success_percentage >= 30.0:
                    # 30-49%: Amarillo con ⚠️
                    cell.fill = success_50_30_fill
                    cell.font = success_50_30_font
                    cell.value = f"⚠️ {success_display}"
                else:
                    # <30%: Rojo con ❌
                    cell.fill = success_low_fill
                    cell.font = success_low_font
                    cell.value = f"❌ {success_display}"

            # COLUMNA BOT AUTOMÁTICO: ROSA CON X
            cell = worksheet.cell(row=row_num, column=5)
            if profile.is_bot_automatic():
                cell.value = "X"
                cell.fill = bot_fill
                cell.font = bot_font
            else:
                cell.value = ""
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # COLUMNA BOT MANUAL: ROSA CON X
            cell = worksheet.cell(row=row_num, column=6)
            if profile.is_bot_manual():
                cell.value = "X"
                cell.fill = bot_fill
                cell.font = bot_font
            else:
                cell.value = ""
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

            # Última Búsqueda
            cell = worksheet.cell(row=row_num, column=7)
            if profile.last_search:
                cell.value = profile.last_search.strftime("%d/%m/%Y %H:%M:%S")
            else:
                cell.value = "Nunca"
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

        # === AJUSTAR ANCHO DE COLUMNAS ===
        column_widths = {
            1: 30,  # Nombre del Perfil
            2: 20,  # Cantidad de ejecuciones
            3: 18,  # Ejecuciones Óptimas
            4: 18,  # Porcentaje de Éxito
            5: 15,  # Bot Automático
            6: 12,  # Bot Manual
            7: 22  # Última Búsqueda
        }

        for col_num, width in column_widths.items():
            worksheet.column_dimensions[get_column_letter(col_num)].width = width

        # Ajustar altura de las filas del título
        worksheet.row_dimensions[1].height = 25
        worksheet.row_dimensions[2].height = 20

        # Agregar hoja de resumen ampliada
        summary_sheet = workbook.create_sheet("Resumen")
        self._add_summary_sheet(summary_sheet, profiles)

        # Guardar archivo
        workbook.save(file_path)

        return str(file_path)

    def _add_summary_sheet(self, worksheet, profiles):
        """
        Agrega hoja de resumen optimizada al reporte incluyendo métricas de seguimiento óptimo y tipos de bot.

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

        worksheet.cell(row=4, column=1).value = "Total de bots:"
        worksheet.cell(row=4, column=1).font = Font(bold=True)
        worksheet.cell(row=4, column=2).value = len(profiles)

        # Estadísticas principales
        active_profiles = len([p for p in profiles if p.last_search])
        inactive_profiles = len(profiles) - active_profiles
        total_executions = sum(p.found_emails for p in profiles)
        total_criteria = sum(len(p.search_criteria) for p in profiles)

        worksheet.cell(row=6, column=1).value = "MÉTRICAS PRINCIPALES"
        worksheet.cell(row=6, column=1).font = Font(bold=True, size=14, color="366092")

        worksheet.cell(row=7, column=1).value = "Bots activos:"
        worksheet.cell(row=7, column=1).font = Font(bold=True)
        worksheet.cell(row=7, column=2).value = active_profiles

        worksheet.cell(row=8, column=1).value = "Bots sin usar:"
        worksheet.cell(row=8, column=1).font = Font(bold=True)
        worksheet.cell(row=8, column=2).value = inactive_profiles

        worksheet.cell(row=9, column=1).value = "Total ejecuciones encontradas:"
        worksheet.cell(row=9, column=1).font = Font(bold=True)
        worksheet.cell(row=9, column=2).value = total_executions

        worksheet.cell(row=10, column=1).value = "Total criterios configurados:"
        worksheet.cell(row=10, column=1).font = Font(bold=True)
        worksheet.cell(row=10, column=2).value = total_criteria

        # Métrica adicional existente
        if active_profiles > 0:
            avg_executions = total_executions / active_profiles
            worksheet.cell(row=11, column=1).value = "Promedio ejecuciones por bot activo:"
            worksheet.cell(row=11, column=1).font = Font(bold=True)
            worksheet.cell(row=11, column=2).value = round(avg_executions, 2)

        # SECCIÓN: TIPOS DE BOT CON COLORES ROSA
        automatic_bots = [p for p in profiles if p.is_bot_automatic()]
        manual_bots = [p for p in profiles if p.is_bot_manual()]

        worksheet.cell(row=13, column=1).value = "TIPOS DE BOT"
        worksheet.cell(row=13, column=1).font = Font(bold=True, size=14, color="C71585")  # Rosa oscuro

        worksheet.cell(row=14, column=1).value = "Bots Automáticos:"
        worksheet.cell(row=14, column=1).font = Font(bold=True)
        worksheet.cell(row=14, column=2).value = len(automatic_bots)
        worksheet.cell(row=14, column=2).fill = PatternFill(start_color="FFFFC0CB", end_color="FFFFC0CB", fill_type="solid")

        worksheet.cell(row=15, column=1).value = "Bots Manuales:"
        worksheet.cell(row=15, column=1).font = Font(bold=True)
        worksheet.cell(row=15, column=2).value = len(manual_bots)
        worksheet.cell(row=15, column=2).fill = PatternFill(start_color="FFFFC0CB", end_color="FFFFC0CB", fill_type="solid")

        # Porcentaje de distribución
        if profiles:
            auto_percentage = (len(automatic_bots) / len(profiles)) * 100
            worksheet.cell(row=16, column=1).value = "% Bots Automáticos:"
            worksheet.cell(row=16, column=1).font = Font(bold=True)
            worksheet.cell(row=16, column=2).value = f"{round(auto_percentage, 1)}%"

        # MÉTRICAS DE SEGUIMIENTO ÓPTIMO CON RANGOS DE COLORES
        profiles_with_tracking = [p for p in profiles if p.track_optimal]

        if profiles_with_tracking:
            worksheet.cell(row=18, column=1).value = "SEGUIMIENTO DE EJECUCIONES ÓPTIMAS"
            worksheet.cell(row=18, column=1).font = Font(bold=True, size=14, color="006400")

            worksheet.cell(row=19, column=1).value = "Bots con seguimiento óptimo:"
            worksheet.cell(row=19, column=1).font = Font(bold=True)
            worksheet.cell(row=19, column=2).value = len(profiles_with_tracking)

            # Contadores por rangos de éxito
            success_100 = len(
                [p for p in profiles_with_tracking if p.get_success_percentage() and p.get_success_percentage() >= 100])
            success_90_50 = len([p for p in profiles_with_tracking if
                                 p.get_success_percentage() and 90 <= p.get_success_percentage() < 100])
            success_50_30 = len([p for p in profiles_with_tracking if
                                 p.get_success_percentage() and 30 <= p.get_success_percentage() < 50])
            success_low = len(
                [p for p in profiles_with_tracking if p.get_success_percentage() and p.get_success_percentage() < 30])

            worksheet.cell(row=20, column=1).value = "✅ Éxito óptimo (100%):"
            worksheet.cell(row=20, column=1).font = Font(bold=True, color="006400")
            worksheet.cell(row=20, column=2).value = success_100
            worksheet.cell(row=20, column=2).fill = PatternFill(start_color="FF90EE90", end_color="FF90EE90",
                                                                fill_type="solid")

            worksheet.cell(row=21, column=1).value = "📊 Éxito alto (90-99%):"
            worksheet.cell(row=21, column=1).font = Font(bold=True, color="800080")
            worksheet.cell(row=21, column=2).value = success_90_50
            worksheet.cell(row=21, column=2).fill = PatternFill(start_color="FFE6E6FA", end_color="FFE6E6FA",
                                                                fill_type="solid")

            worksheet.cell(row=22, column=1).value = "⚠️ Éxito medio (30-49%):"
            worksheet.cell(row=22, column=1).font = Font(bold=True, color="B8860B")
            worksheet.cell(row=22, column=2).value = success_50_30
            worksheet.cell(row=22, column=2).fill = PatternFill(start_color="FFFFFF99", end_color="FFFFFF99",
                                                                fill_type="solid")

            worksheet.cell(row=23, column=1).value = "❌ Éxito bajo (<30%):"
            worksheet.cell(row=23, column=1).font = Font(bold=True, color="CC0000")
            worksheet.cell(row=23, column=2).value = success_low
            worksheet.cell(row=23, column=2).fill = PatternFill(start_color="FFFFCCCC", end_color="FFFFCCCC",
                                                                fill_type="solid")

            # Promedio de porcentaje de éxito
            success_percentages = []
            for profile in profiles_with_tracking:
                percentage = profile.get_success_percentage()
                if percentage is not None:
                    success_percentages.append(percentage)

            if success_percentages:
                avg_success = sum(success_percentages) / len(success_percentages)
                worksheet.cell(row=24, column=1).value = "Promedio de porcentaje de éxito:"
                worksheet.cell(row=24, column=1).font = Font(bold=True)
                worksheet.cell(row=24, column=2).value = f"{round(avg_success, 1)}%"

        # Top 3 bots más productivos (actualizado con tipo de bot)
        if profiles:
            start_row = 26 if profiles_with_tracking else 18
            worksheet.cell(row=start_row, column=1).value = "TOP 3 BOTS MÁS PRODUCTIVOS"
            worksheet.cell(row=start_row, column=1).font = Font(bold=True, size=12, color="366092")

            # Ordenar perfiles por ejecuciones encontradas
            sorted_profiles = sorted(profiles, key=lambda p: p.found_emails, reverse=True)[:3]

            for i, profile in enumerate(sorted_profiles, 1):
                row = start_row + i
                bot_type_icon = "🤖" if profile.is_bot_automatic() else "👤"
                profile_text = f"{i}. {profile.name} {bot_type_icon}"
                executions_text = f"{profile.found_emails} ejecuciones"

                # Agregar información de éxito si está disponible
                if profile.track_optimal:
                    success_percentage = profile.get_success_percentage()
                    if success_percentage is not None:
                        executions_text += f" ({success_percentage}% éxito)"
                        if success_percentage >= 100:
                            executions_text += " ✅"
                        elif success_percentage >= 90:
                            executions_text += " 📊"
                        elif success_percentage >= 30:
                            executions_text += " ⚠️"
                        else:
                            executions_text += " ❌"

                worksheet.cell(row=row, column=1).value = profile_text
                worksheet.cell(row=row, column=2).value = executions_text

        # Ajustar ancho de columnas
        worksheet.column_dimensions['A'].width = 40
        worksheet.column_dimensions['B'].width = 30

        # Agregar bordes a las celdas principales
        max_row = 30 if profiles_with_tracking else 22
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