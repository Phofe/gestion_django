const express = require("express");

const app = express();
const PORT = process.env.PORT || 3000;

app.disable("x-powered-by");
app.use(express.json({ limit: "20kb" }));

let nextId = 4;
let products = [
  { id: 1, name: "Clavier", category: "Informatique", price: 12000, stock: 12 },
  { id: 2, name: "Cahier", category: "Papeterie", price: 750, stock: 50 },
  { id: 3, name: "Souris", category: "Informatique", price: 6500, stock: 18 }
];

function validateProduct(body) {
  const errors = [];
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return ["Le corps de la requête doit être un objet JSON."];
  }
  if (typeof body.name !== "string" || !body.name.trim()) errors.push("Le champ name est obligatoire.");
  else if (body.name.trim().length > 100) errors.push("Le champ name ne doit pas dépasser 100 caractères.");
  if (typeof body.category !== "string" || !body.category.trim()) errors.push("Le champ category est obligatoire.");
  else if (body.category.trim().length > 60) errors.push("Le champ category ne doit pas dépasser 60 caractères.");
  if (typeof body.price !== "number" || !Number.isFinite(body.price) || body.price < 0) errors.push("Le champ price doit être un nombre positif ou nul.");
  if (!Number.isInteger(body.stock) || body.stock < 0) errors.push("Le champ stock doit être un entier positif ou nul.");
  return errors;
}

function normalizeProduct(body) {
  return { name: body.name.trim(), category: body.category.trim(), price: body.price, stock: body.stock };
}

app.get("/", (_req, res) => res.json({
  name: "API REST de gestion de produits",
  version: "1.0.0",
  endpoints: {
    list: "GET /api/products",
    detail: "GET /api/products/:id",
    create: "POST /api/products",
    update: "PUT /api/products/:id",
    delete: "DELETE /api/products/:id"
  }
}));

app.get("/api/products", (req, res) => {
  let result = [...products];
  if (req.query.category) {
    const category = String(req.query.category).toLowerCase();
    result = result.filter(p => p.category.toLowerCase() === category);
  }
  if (req.query.search) {
    const search = String(req.query.search).toLowerCase();
    result = result.filter(p => p.name.toLowerCase().includes(search) || p.category.toLowerCase().includes(search));
  }
  res.json({ data: result, count: result.length });
});

app.get("/api/products/:id", (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) return res.status(400).json({ error: "Identifiant invalide." });
  const product = products.find(p => p.id === id);
  if (!product) return res.status(404).json({ error: "Produit introuvable." });
  return res.json({ data: product });
});

app.post("/api/products", (req, res) => {
  const errors = validateProduct(req.body);
  if (errors.length) return res.status(400).json({ error: "Données invalides.", details: errors });
  const product = { id: nextId++, ...normalizeProduct(req.body) };
  products.push(product);
  return res.status(201).json({ data: product });
});

app.put("/api/products/:id", (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) return res.status(400).json({ error: "Identifiant invalide." });
  const index = products.findIndex(p => p.id === id);
  if (index === -1) return res.status(404).json({ error: "Produit introuvable." });
  const errors = validateProduct(req.body);
  if (errors.length) return res.status(400).json({ error: "Données invalides.", details: errors });
  products[index] = { id, ...normalizeProduct(req.body) };
  return res.json({ data: products[index] });
});

app.delete("/api/products/:id", (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) return res.status(400).json({ error: "Identifiant invalide." });
  const index = products.findIndex(p => p.id === id);
  if (index === -1) return res.status(404).json({ error: "Produit introuvable." });
  const [deleted] = products.splice(index, 1);
  return res.json({ message: "Produit supprimé.", data: deleted });
});

app.use((_req, res) => res.status(404).json({ error: "Route introuvable." }));
app.use((err, _req, res, _next) => {
  if (err instanceof SyntaxError && "body" in err) return res.status(400).json({ error: "JSON invalide." });
  return res.status(500).json({ error: "Erreur interne du serveur." });
});

if (require.main === module) {
  app.listen(PORT, () => console.log("API disponible sur http://localhost:" + PORT));
}
module.exports = { app };
