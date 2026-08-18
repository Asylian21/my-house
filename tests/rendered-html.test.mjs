import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the Slovak digital-twin product shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<html[^>]+lang="sk"/i);
  assert.match(html, /<title>Dom 6012\/26 · Digitálne dvojča<\/title>/i);
  assert.match(html, /DOM 6012\/26/);
  assert.match(html, /Březí u Mikulova/);
  assert.match(html, /Živý výkres/);
  assert.match(html, /Parcela 6012\/26/);
  assert.match(html, /ČÚZK/);
  assert.match(html, /DÁTOVÁ STOPA/);
  assert.match(html, /Skutočné prípojky/);
  assert.match(html, /aria-label="Prieskumník digitálneho dvojčaťa"/);
  assert.match(html, /aria-label="Detail vybraného objektu"/);
  assert.match(html, /class="twin-shell is-presentation"/);
  assert.match(html, /class="scene-panel "[^>]+aria-hidden="true"[^>]+inert/);
  assert.match(html, /class="inspector "[^>]+aria-hidden="true"[^>]+inert/);
  assert.match(html, /aria-pressed="true"[^>]*>[\s\S]{0,500}?Realita/i);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
  assert.doesNotMatch(html, /Overené 04|12 % realizácie|react-loading-skeleton/);
});

test("keeps Babylon client-only and removes the disposable starter preview", async () => {
  const [viewport, page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/babylon-viewport.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(viewport, /void import\("@\/lib\/babylon-scene"\)/);
  assert.match(viewport, /ResizeObserver/);
  assert.match(viewport, /controllerRef\.current\?\.dispose\(\)/);
  assert.match(page, /<TwinStudio \/>/);
  assert.match(layout, /lang="sk"/);
  assert.match(layout, /Dom 6012\/26 · Digitálne dvojča/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(access(new URL("../public/_sites-preview", import.meta.url)));
});

test("ships and discloses every local illustrative rendering asset", async () => {
  const assets = [
    ["../public/assets/environment/overcast-garden.jpg", "ffd8ff"],
    ["../public/assets/textures/lawn-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/larch-cladding-v2.jpg", "ffd8ff"],
    ["../public/assets/textures/stucco-warm-v1.jpg", "ffd8ff"],
    ["../public/assets/textures/deck-larch-v1.jpg", "ffd8ff"],
    ["../public/assets/vegetation/ornamental-grass-card.png", "89504e470d0a1a0a"],
    ["../public/assets/vegetation/perennial-cluster-card.png", "89504e470d0a1a0a"],
  ];
  const [sceneSource, readme] = await Promise.all([
    readFile(new URL("../lib/babylon-scene.ts", import.meta.url), "utf8"),
    readFile(new URL("../README.md", import.meta.url), "utf8"),
  ]);

  for (const [relativePath, signature] of assets) {
    const bytes = await readFile(new URL(relativePath, import.meta.url));
    assert.ok(bytes.byteLength > 16 * 1024, `${relativePath} is unexpectedly small`);
    assert.equal(
      bytes.subarray(0, signature.length / 2).toString("hex"),
      signature,
      `${relativePath} has an unexpected file signature`,
    );
    const publicUrl = relativePath.replace("../public", "");
    assert.ok(sceneSource.includes(publicUrl), `${publicUrl} is not wired into Babylon`);
    assert.ok(readme.includes(relativePath.split("/").at(-1)), `${relativePath} is not disclosed`);
  }
  assert.match(readme, /OpenAI imagegen/);
  assert.match(readme, /ilustračný záhradný koncept/);
});
