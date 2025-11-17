"""Tests unitaires pour le scraper DGCCRF."""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ajout du répertoire parent au PATH pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scraper_dgccrf import DgccrfScraper, setup_logging

class TestDgccrfScraper(unittest.TestCase):
    """Classe de tests pour DgccrfScraper."""
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests."""
        cls.scraper = DgccrfScraper()
        
    def test_normalize_category(self):
        """Test de la méthode _normalize_category."""
        self.assertEqual(self.scraper._normalize_category("ÉLECTROMÉNAGER"), 
                        "electromenager")
        self.assertEqual(self.scraper._normalize_category("  Espaces  avec  espaces  "), 
                        "espaces_avec_espaces")
        self.assertEqual(self.scraper._normalize_category(""), "")

    @patch('scripts.scraper_dgccrf.requests.Session')
    def test_request_with_retry_success(self, mock_session):
        """Test de la méthode _request_with_retry avec succès."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Test</html>"
        mock_session.return_value.get.return_value = mock_response
        
        # Appel de la méthode avec un mock pour time.sleep
        with patch('time.sleep'):
            response = self.scraper._request_with_retry("http://test.com")
            self.assertEqual(response.text, "<html>Test</html>")

    def test_parse_price_fcfa(self):
        """Test de la méthode _parse_price_fcfa."""
        self.assertEqual(self.scraper._parse_price_fcfa("1 234,56 FCFA"), 1234.56)
        self.assertIsNone(self.scraper._parse_price_fcfa("Invalid"))
        self.assertEqual(self.scraper._parse_price_fcfa("1.234,56 FCFA"), 1234.56)
        self.assertEqual(self.scraper._parse_price_fcfa("1 234 FCFA"), 1234.0)

    def test_clean_text(self):
        """Test de la méthode _clean_text."""
        self.assertEqual(self.scraper._clean_text("  Test  "), "Test")
        self.assertEqual(self.scraper._clean_text("Test\navec\nsauts"), 
                        "Test avec sauts")
        self.assertEqual(self.scraper._clean_text("  "), "")
        self.assertEqual(self.scraper._clean_text("  Test  avec  espaces  "), 
                        "Test avec espaces")

    @patch('scripts.scraper_dgccrf.robotparser.RobotFileParser')
    @patch('scripts.scraper_dgccrf.requests.Session')
    def test_is_allowed_by_robots(self, mock_session, mock_robot_parser):
        """Test de la méthode _is_allowed_by_robots."""
        # Configuration des mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private/"
        mock_session.return_value.get.return_value = mock_response
        
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True
        mock_robot_parser.return_value = mock_parser
        
        # Test avec RESPECT_ROBOTS = False
        with patch('scripts.scraper_dgccrf.RESPECT_ROBOTS', False):
            self.assertTrue(self.scraper._is_allowed_by_robots("http://test.com"))
        
        # Test avec RESPECT_ROBOTS = True
        with patch('scripts.scraper_dgccrf.RESPECT_ROBOTS', True):
            self.assertTrue(self.scraper._is_allowed_by_robots("http://test.com"))
            mock_parser.can_fetch.assert_called_once()

    def test_find_category_before_table(self):
        """Test de la méthode find_category_before_table."""
        from bs4 import BeautifulSoup
        
        # Création d'un fragment HTML de test
        html = """
        <div>
            <h3><strong><span>CATÉGORIE DE TEST</span></strong></h3>
            <table>
                <tr><td>Test</td><td>123</td></tr>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        # Test avec une table valide
        category = self.scraper.find_category_before_table(table)
        self.assertEqual(category, "CATÉGORIE DE TEST")
        
        # Test avec une table sans catégorie
        empty_table = BeautifulSoup("<table></table>", 'html.parser').find('table')
        self.assertEqual(self.scraper.find_category_before_table(empty_table), "")


if __name__ == '__main__':
    unittest.main()
