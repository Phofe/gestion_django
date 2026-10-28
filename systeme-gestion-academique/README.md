# Système de gestion académique

Application web Django/Python pour centraliser les opérations d'un établissement d'enseignement supérieur : étudiants, enseignants, cours, emplois du temps, notes, paiements, documents PDF, tableau de bord et notifications internes.

## Fonctionnalités prévues dans ce MVP
- Authentification Django et profils à rôles : administrateur, enseignant, étudiant.
- Modèles de données pour étudiants, enseignants, cours, inscriptions, notes, paiements et séances.
- Tableau de bord avec indicateurs et notifications internes.
- Génération PDF d'un relevé de notes, d'une attestation de scolarité ou d'un reçu de paiement.
- Interface de gestion Django Admin pour administrer les données.
- Configuration PostgreSQL via variables d'environnement ; SQLite est utilisé par défaut en développement local.

## Démarrage
```bash
python -m venv .venv
# Windows : .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations academic
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Ouvrir http://127.0.0.1:8000/ puis se connecter. Le superutilisateur accède à l'administration via /admin/.

## PostgreSQL
Définir `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT` dans l'environnement. Si `DB_NAME` est défini, Django utilise PostgreSQL ; sinon, il utilise SQLite pour simplifier les tests locaux.

## Sécurité et limites
- Définir une valeur secrète et non publique pour `DJANGO_SECRET_KEY` en production et `DJANGO_DEBUG=False`.
- Configurer HTTPS, les hôtes autorisés, sauvegardes, politique de conservation et permissions métier avant un déploiement réel.
- Les PDF sont des documents de démonstration ; une validation administrative et une identité visuelle officielle doivent être ajoutées avant leur usage institutionnel.
- Ce dépôt constitue une base MVP à compléter et tester avec des données fictives. Il ne doit pas être présenté comme un service universitaire déjà déployé.
