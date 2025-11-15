import unittest
from scripts.scraper_dgccrf import DgccrfScraper


class TestDgccrfParsing(unittest.TestCase):
    def test_parse_price_fcfa(self):
        self.assertEqual(DgccrfScraper._parse_price_fcfa("2 500 FCFA"), 2500.0)
        self.assertEqual(DgccrfScraper._parse_price_fcfa("2530 F CFA"), 2530.0)
        self.assertIsNone(DgccrfScraper._parse_price_fcfa("N/A"))

    def test_detect_unit(self):
        self.assertEqual(DgccrfScraper._detect_unit("1 kg de riz"), "kg")
        self.assertEqual(DgccrfScraper._detect_unit("Bouteille 1L"), "L")
        self.assertEqual(DgccrfScraper._detect_unit("Sachet 500 ml"), "ml")

    def test_parse_conditionnement(self):
        c = DgccrfScraper.parse_conditionnement("6 x 1L")
        self.assertEqual(c.get("nombre_unites"), 6)
        self.assertAlmostEqual(c.get("quantite_totale"), 6.0)
        
        # Test format "125g x 50"
        c2 = DgccrfScraper.parse_conditionnement("125g x 50")
        self.assertEqual(c2.get("nombre_unites"), 50)
        self.assertAlmostEqual(c2.get("quantite_unite"), 125.0)
        self.assertEqual(c2.get("unite"), "g")
        self.assertAlmostEqual(c2.get("quantite_totale"), 6250.0)
        
        # Test format avec "ou" et lbs
        c3 = DgccrfScraper.parse_conditionnement("10lbs ou 4,54Kg x 10")
        self.assertEqual(c3.get("nombre_unites"), 10)
        self.assertAlmostEqual(c3.get("quantite_unite"), 4.54, places=2)
        self.assertEqual(c3.get("unite"), "kg")
        
        # Test extraction origine
        origin_info = DgccrfScraper.extract_origin_and_clean_name("Cuisses de Poulet (USA)")
        self.assertEqual(origin_info['nom'], "Cuisses de Poulet")
        self.assertEqual(origin_info['origine'], "USA")


if __name__ == "__main__":
    unittest.main()
