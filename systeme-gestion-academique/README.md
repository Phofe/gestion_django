# Système de gestion académique

Application web Django/Python pour centraliser les opérations d'un établissement d'enseignement supérieur : étudiants, enseignants, cours, inscriptions, notes, paiements, emplois du temps, documents PDF et notifications internes.

## Fonctions du MVP

- Formulaires métier de création et modification pour étudiants, enseignants, cours, inscriptions, notes, paiements et séances.
- Rôles administrateur, enseignant et étudiant ; un enseignant peut saisir ou modifier uniquement les notes de ses propres cours.
- Filtrage des données affichées selon le profil connecté.
- Documents PDF : relevé de notes, attestation de scolarité et reçu de paiement.
- Administration Django et base PostgreSQL configurable par variables d'environnement ; SQLite reste disponible en développement local.

## Règles de gestion implémentées

- Matricule étudiant, matricule enseignant, code de cours et référence de paiement uniques.
- Compte lié au profil étudiant/enseignant avec le rôle correspondant.
- Année académique au format `AAAA-AAAA` et composée de deux années consécutives.
- Inscription interdite pour un étudiant inactif ou dans un cours d'une autre formation.
- Nombre de crédits compris entre 1 et 60.
- Notes comprises entre 0 et 20 et une seule note par type d'évaluation et inscription.
- Montant de paiement strictement positif ; la date de paiement est renseignée automatiquement lorsque le statut passe à « Payé ».
- Horaire : fin après début, pas de chevauchement pour une même salle, un même cours ou un même enseignant.
- Attestation réservée aux étudiants actifs ; reçu PDF disponible uniquement pour un paiement confirmé et autorisé.
- Contrôles de rôle sur les formulaires de gestion, contrôles CSRF Django et validation côté serveur.

Ces règles sont des valeurs de départ pour le MVP. Les règles institutionnelles (barème officiel, crédits par diplôme, périodes d'inscription, seuils de validation, compensation, redoublement, échéancier des frais) doivent être confirmées par l'établissement avant une utilisation réelle.

## Démarrage local

```bash
python -m venv .venv
# Windows : .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations academic
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ puis se connecter. L'administration est disponible sur /admin/.

## PostgreSQL

Renseigner `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT`. Sans `DB_NAME`, le projet utilise SQLite.

## Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Sécurité et limites

- Définir une clé secrète robuste, `DJANGO_DEBUG=False`, des hôtes autorisés et HTTPS en production.
- Mettre en place sauvegardes, journalisation, politique de conservation et permissions institutionnelles avant déploiement.
- Les PDF restent des documents de démonstration et ne constituent pas des attestations officielles.
- Utiliser des données fictives pour les tests et ne pas publier de données personnelles réelles.
