# Assistant d'analyse de fichiers CSV

Petit outil en ligne de commande pour explorer un fichier CSV, repérer les valeurs manquantes et les lignes dupliquées, obtenir des statistiques simples et exporter une version nettoyée.

## Fonctionnalités

- Détection du séparateur parmi virgule, point-virgule, tabulation et barre verticale.
- Comptage des lignes et colonnes.
- Détection des valeurs manquantes et des valeurs uniques par colonne.
- Statistiques min, max et moyenne pour les colonnes numériques.
- Détection des doublons de lignes.
- Export optionnel d'un CSV sans lignes entièrement vides ni doublons exacts.
- Rapport lisible ou JSON.
- Tests unitaires sans dépendance externe.

## Prérequis

Python 3.10 ou plus récent. Aucune bibliothèque tierce n'est nécessaire.

## Utilisation

Depuis ce dossier :

```bash
python analyse_csv.py exemple.csv
```

Rapport JSON :

```bash
python analyse_csv.py exemple.csv --json
```

Exporter un fichier nettoyé :

```bash
python analyse_csv.py exemple.csv --nettoyer-vers exemple_nettoye.csv
```

Indiquer explicitement le séparateur :

```bash
python analyse_csv.py donnees.csv --delimiter ";"
```

Lancer les tests :

```bash
python -m unittest -v
```

## Structure

- `analyse_csv.py` : fonctions d'import, d'analyse, de nettoyage et interface CLI.
- `test_analyse_csv.py` : tests unitaires.
- `exemple.csv` : petit jeu de données fictives pour essayer le programme.

## Limites et confidentialité

Le programme traite les fichiers localement et n'envoie aucune donnée sur Internet. Il convient aux petits et moyens CSV ; les fichiers très volumineux peuvent nécessiter une approche en flux. Les cellules numériques utilisent une interprétation simple des virgules décimales. Le nettoyage supprime les doublons exacts et les lignes entièrement vides, mais ne corrige pas automatiquement les erreurs de saisie.

## Statut

Projet de portfolio pédagogique, exécutable localement.
