# API REST de gestion de produits

API d'exemple en Node.js et Express pour illustrer les opérations CRUD sur un catalogue de produits au format JSON.

## Fonctionnalités

- Lister les produits.
- Consulter un produit par identifiant.
- Ajouter, modifier et supprimer un produit.
- Filtrer par catégorie ou rechercher par nom/catégorie.
- Valider les champs et renvoyer des codes HTTP adaptés.
- Gérer les routes inconnues et les corps JSON invalides.

## Prérequis

- Node.js 18 ou plus récent
- npm

## Installation et démarrage

```bash
npm install
npm start
```

L'API démarre par défaut sur `http://localhost:3000`. Pour changer le port, définissez la variable d'environnement `PORT`.

## Routes

| Méthode | Route | Description |
|---|---|---|
| GET | `/` | Documentation rapide des routes |
| GET | `/api/products` | Liste des produits |
| GET | `/api/products?category=Informatique` | Filtrer par catégorie |
| GET | `/api/products?search=clavier` | Recherche par texte |
| GET | `/api/products/:id` | Détail d'un produit |
| POST | `/api/products` | Créer un produit |
| PUT | `/api/products/:id` | Remplacer les données d'un produit |
| DELETE | `/api/products/:id` | Supprimer un produit |

## Exemple de création

Envoyez une requête `POST /api/products` avec l'en-tête `Content-Type: application/json` et ce corps :

```json
{
  "name": "Écran",
  "category": "Informatique",
  "price": 85000,
  "stock": 5
}
```

## Limites et améliorations possibles

Les données sont conservées en mémoire et sont réinitialisées au redémarrage. Cette version est conçue pour l'apprentissage : elle n'inclut pas de base de données, d'authentification ni de limitation de débit. Avant un déploiement réel, ajouter une persistance, des contrôles d'accès, des journaux et une configuration de sécurité adaptée.

## Technologies

Node.js, Express, JavaScript, JSON.
