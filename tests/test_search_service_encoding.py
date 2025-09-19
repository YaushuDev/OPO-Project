import shutil
import tempfile
import unittest
from datetime import datetime
from email.message import EmailMessage

from services.search_service import SearchService


class SearchServiceEncodingTests(unittest.TestCase):
    """Pruebas para validar el manejo de acentos y textos mal decodificados."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="search_service_test_")
        self.service = SearchService(data_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _build_message(self, subject):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = 'example@example.com'
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        msg.set_content('Cuerpo de prueba con Próximos y más tildes')
        return msg

    def test_subject_with_accent_matches_unaccented_criteria(self):
        """El servicio reconoce asuntos con tilde aunque el criterio no la tenga."""
        msg = self._build_message('Alertas de Pickup Services - Próximos a Vencer y Vencidos')
        content = self.service._extract_search_content(msg)
        patterns = self.service._prepare_search_patterns([
            'Alertas de Pickup Services - Proximos a Vencer y Vencidos'
        ])

        self.assertIn('proximos', content['subject_normalized'])
        self.assertTrue(self.service._matches_criteria(content, patterns[0]))

    def test_mojibake_subject_is_normalized(self):
        """Corrige cadenas mal decodificadas (ej. PrÃ³ximos -> Próximos)."""
        msg = self._build_message('Alertas de Pickup Services - PrÃ³ximos a Vencer y Vencidos')
        content = self.service._extract_search_content(msg)

        self.assertIn('Próximos', content['subject'])
        self.assertIn('proximos', content['subject_normalized'])

        patterns = self.service._prepare_search_patterns([
            'Alertas de Pickup Services - Proximos a Vencer y Vencidos'
        ])
        self.assertTrue(self.service._matches_criteria(content, patterns[0]))


if __name__ == '__main__':
    unittest.main()
