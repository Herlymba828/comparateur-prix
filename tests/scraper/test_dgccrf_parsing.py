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


if __name__ == "__main__":
    unittest.main()
