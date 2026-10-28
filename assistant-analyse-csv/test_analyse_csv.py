import unittest

from analyse_csv import analyser, nettoyer, nombre


class AnalyseCsvTests(unittest.TestCase):
    def test_nombre_decimal_virgule(self):
        self.assertEqual(nombre("12,5"), 12.5)

    def test_analyser_statistiques(self):
        colonnes = ["nom", "prix"]
        lignes = [
            {"nom": "Stylo", "prix": "100"},
            {"nom": "Cahier", "prix": "200"},
            {"nom": "Stylo", "prix": "100"},
        ]
        rapport = analyser(colonnes, lignes)
        self.assertEqual(rapport["nombre_lignes"], 3)
        self.assertEqual(rapport["lignes_dupliquees"], 1)
        self.assertEqual(rapport["colonnes"]["prix"]["moyenne"], 133.333)

    def test_nettoyer_doublons_et_lignes_vides(self):
        lignes = [
            {"nom": "Stylo", "prix": "100"},
            {"nom": "Stylo", "prix": "100"},
            {"nom": "", "prix": ""},
        ]
        self.assertEqual(nettoyer(lignes), [{"nom": "Stylo", "prix": "100"}])


if __name__ == "__main__":
    unittest.main()
