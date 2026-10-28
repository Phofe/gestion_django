#!/usr/bin/env python3
"""Analyseur CSV simple utilisant uniquement la bibliothèque standard Python."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any


def lire_csv(chemin: str | Path, delimiter: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
    """Lit un CSV UTF-8 et renvoie les noms de colonnes et les lignes."""
    path = Path(chemin)
    with path.open("r", encoding="utf-8-sig", newline="") as fichier:
        extrait = fichier.read(4096)
        fichier.seek(0)
        if delimiter is None:
            try:
                delimiter = csv.Sniffer().sniff(extrait, delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
        lecteur = csv.DictReader(fichier, delimiter=delimiter)
        if not lecteur.fieldnames:
            raise ValueError("Le fichier CSV ne contient pas d'en-tête.")
        colonnes = [nom.strip() for nom in lecteur.fieldnames]
        lignes: list[dict[str, str]] = []
        for ligne in lecteur:
            lignes.append({
                colonne: (ligne.get(original) or "").strip()
                for colonne, original in zip(colonnes, lecteur.fieldnames)
            })
    return colonnes, lignes


def nombre(valeur: str) -> float | None:
    """Convertit une valeur en nombre si possible (prend en charge la virgule décimale)."""
    valeur = valeur.strip().replace("\u00a0", "").replace(" ", "")
    if not valeur:
        return None
    if "," in valeur and "." not in valeur:
        valeur = valeur.replace(",", ".")
    try:
        return float(valeur)
    except ValueError:
        return None


def analyser(colonnes: list[str], lignes: list[dict[str, str]]) -> dict[str, Any]:
    """Calcule les statistiques de base, les valeurs manquantes et les doublons."""
    ensembles = {tuple(ligne.get(c, "") for c in colonnes) for ligne in lignes}
    resultats: dict[str, Any] = {
        "nombre_lignes": len(lignes),
        "nombre_colonnes": len(colonnes),
        "colonnes": {},
        "lignes_dupliquees": len(lignes) - len(ensembles),
    }
    for colonne in colonnes:
        valeurs = [ligne.get(colonne, "") for ligne in lignes]
        remplies = [v for v in valeurs if v != ""]
        numeriques = [n for v in remplies if (n := nombre(v)) is not None]
        info: dict[str, Any] = {
            "valeurs_manquantes": len(valeurs) - len(remplies),
            "valeurs_uniques": len(set(remplies)),
            "type_probable": "numérique" if remplies and len(numeriques) == len(remplies) else "texte",
        }
        if numeriques and len(numeriques) == len(remplies):
            info.update({
                "minimum": min(numeriques),
                "maximum": max(numeriques),
                "moyenne": round(statistics.mean(numeriques), 3),
            })
        resultats["colonnes"][colonne] = info
    return resultats


def nettoyer(lignes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Retire les lignes entièrement vides et les doublons exacts, en conservant l'ordre."""
    vues: set[tuple[tuple[str, str], ...]] = set()
    propres: list[dict[str, str]] = []
    for ligne in lignes:
        if not any(valeur.strip() for valeur in ligne.values()):
            continue
        cle = tuple(sorted(ligne.items()))
        if cle not in vues:
            vues.add(cle)
            propres.append(ligne)
    return propres


def exporter_csv(chemin: str | Path, colonnes: list[str], lignes: list[dict[str, str]]) -> None:
    """Exporte des lignes dans un nouveau fichier CSV UTF-8."""
    with Path(chemin).open("w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=colonnes, extrasaction="ignore")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse et nettoie un fichier CSV.")
    parser.add_argument("fichier", help="Chemin du fichier CSV à analyser")
    parser.add_argument("--delimiter", help="Séparateur explicite (ex. ; ou ,)")
    parser.add_argument("--nettoyer-vers", help="Chemin d'un nouveau CSV nettoyé à créer")
    parser.add_argument("--json", action="store_true", help="Afficher le rapport au format JSON")
    args = parser.parse_args()

    try:
        colonnes, lignes = lire_csv(args.fichier, args.delimiter)
    except (OSError, UnicodeError, csv.Error, ValueError) as erreur:
        parser.error(str(erreur))

    rapport = analyser(colonnes, lignes)
    print(json.dumps(rapport, ensure_ascii=False, indent=2) if args.json else rapport_texte(rapport))
    if args.nettoyer_vers:
        propres = nettoyer(lignes)
        exporter_csv(args.nettoyer_vers, colonnes, propres)
        print(f"\nCSV nettoyé créé : {args.nettoyer_vers} ({len(propres)} lignes conservées)")
    return 0


def rapport_texte(rapport: dict[str, Any]) -> str:
    lignes = [
        "RAPPORT D'ANALYSE CSV",
        "=" * 22,
        f"Lignes : {rapport['nombre_lignes']}",
        f"Colonnes : {rapport['nombre_colonnes']}",
        f"Lignes dupliquées : {rapport['lignes_dupliquees']}",
        "",
        "DÉTAIL PAR COLONNE",
    ]
    for nom, info in rapport["colonnes"].items():
        lignes.append(f"\n• {nom} ({info['type_probable']})")
        lignes.append(f"  Valeurs manquantes : {info['valeurs_manquantes']}")
        lignes.append(f"  Valeurs uniques : {info['valeurs_uniques']}")
        if "moyenne" in info:
            lignes.append(f"  Min / Max / Moyenne : {info['minimum']} / {info['maximum']} / {info['moyenne']}")
    return "\n".join(lignes)


if __name__ == "__main__":
    raise SystemExit(main())
