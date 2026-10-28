const test = require("node:test");
const assert = require("node:assert/strict");
const { once } = require("node:events");
const { app } = require("../src/server");

test("API produits : parcours CRUD et erreurs", async () => {
  const server = app.listen(0);
  await once(server, "listening");
  const address = server.address();
  const base = `http://127.0.0.1:${address.port}`;

  async function json(path, options) {
    const response = await fetch(base + path, options);
    const body = await response.json();
    return { response, body };
  }

  try {
    const initial = await json("/api/products");
    assert.equal(initial.response.status, 200);
    assert.equal(initial.body.count, 3);

    const created = await json("/api/products", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "Écran", category: "Informatique", price: 85000, stock: 5 })
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.data.name, "Écran");
    const id = created.body.data.id;

    const detail = await json(`/api/products/${id}`);
    assert.equal(detail.response.status, 200);
    assert.equal(detail.body.data.stock, 5);

    const updated = await json(`/api/products/${id}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "Écran HD", category: "Informatique", price: 90000, stock: 4 })
    });
    assert.equal(updated.response.status, 200);
    assert.equal(updated.body.data.name, "Écran HD");

    const searched = await json("/api/products?search=Écran");
    assert.equal(searched.response.status, 200);
    assert.equal(searched.body.count, 1);

    const invalid = await json("/api/products", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "", category: "Informatique", price: -1, stock: 1.5 })
    });
    assert.equal(invalid.response.status, 400);
    assert.ok(Array.isArray(invalid.body.details));

    const deleted = await json(`/api/products/${id}`, { method: "DELETE" });
    assert.equal(deleted.response.status, 200);
    assert.equal(deleted.body.data.id, id);

    const missing = await json(`/api/products/${id}`);
    assert.equal(missing.response.status, 404);

    const malformed = await fetch(base + "/api/products", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{"
    });
    assert.equal(malformed.status, 400);
    assert.equal((await malformed.json()).error, "JSON invalide.");

    const unknown = await json("/route-inconnue");
    assert.equal(unknown.response.status, 404);
  } finally {
    await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
});
