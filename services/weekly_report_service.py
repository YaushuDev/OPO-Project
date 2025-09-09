"""weekly_report_service.py
Servicio para generar un reporte semanal a partir de correos enviados.
Recorre el directorio 'enviados/' buscando correos con un asunto
específico y extrae los adjuntos en formato Excel para combinarlos
en un solo reporte utilizando ReportService.
"""

from pathlib import Path
from datetime import datetime
import email

try:
    import openpyxl
except ImportError:  # pragma: no cover - dependencia opcional
    openpyxl = None

from services.report_service import ReportService


class WeeklyReportService:
    """Servicio que construye reportes semanales a partir de correos enviados."""

    def __init__(self, sent_dir: str = "enviados", subject_keyword: str = "Reporte Semanal"):
        self.sent_dir = Path(sent_dir)
        self.subject_keyword = subject_keyword
        self.report_service = ReportService()

    def _find_weekly_attachments(self):
        """Busca correos con el asunto semanal y extrae adjuntos Excel."""
        attachments = []
        if not self.sent_dir.exists():
            return attachments

        for eml_file in self.sent_dir.glob("*.eml"):
            try:
                with open(eml_file, "r", encoding="utf-8", errors="ignore") as fp:
                    msg = email.message_from_file(fp)
                subject = msg.get("Subject", "")
                if self.subject_keyword.lower() not in subject.lower():
                    continue
                for part in msg.walk():
                    if part.get_content_disposition() == "attachment":
                        filename = part.get_filename()
                        if filename and filename.lower().endswith((".xls", ".xlsx")):
                            attachment_path = self.sent_dir / filename
                            if not attachment_path.exists():
                                with open(attachment_path, "wb") as out:
                                    out.write(part.get_payload(decode=True))
                            attachments.append(attachment_path)
            except Exception:
                continue
        return attachments

    def generate_weekly_report(self):
        """Genera un único reporte Excel a partir de adjuntos semanales.

        Returns:
            str | None: Ruta del reporte generado o None si no se encontraron adjuntos.
        """
        if openpyxl is None:
            raise Exception("openpyxl no está instalado. Ejecute: pip install openpyxl")

        excel_files = self._find_weekly_attachments()
        if not excel_files:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"reporte_semanal_{timestamp}.xlsx"
        return self.report_service.merge_excels(excel_files, output_name)
