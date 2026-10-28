import csv
import tempfile
import unittest
from pathlib import Path

from analyse_csv import analyser, exporter_csv, lire_csv, nettoyer, nombre


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



    def test_lit_csv_avec_point_virgule_et_bom(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "entree.csv"
            chemin.write_text("\\ufeffnom;prix\\nStylo;12,5\\nCahier;20\\n", encoding="utf-8")
            colonnes, lignes = lire_csv(chemin)
            self.assertEqual(colonnes, ["nom", "prix"])
            self.assertEqual(lignes[0], {"nom": "Stylo", "prix": "12,5"})
            self.assertEqual(analyser(colonnes, lignes)["nombre_lignes"], 2)

    def test_entete_absent_est_signale(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "vide.csv"
            chemin.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                lire_csv(chemin)

    def test_export_csv_nettoye_relisible(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "nettoye.csv"
            colonnes = ["nom", "prix"]
            lignes = [{"nom": "Stylo", "prix": "100"}]
            exporter_csv(chemin, colonnes, lignes)
            colonnes_lues, lignes_lues = lire_csv(chemin)
            self.assertEqual(colonnes_lues, colonnes)
            self.assertEqual(lignes_lues, lignes)


if __name__ == "__main__":
    unittest.main()
