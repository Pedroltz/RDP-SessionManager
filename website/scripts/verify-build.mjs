import assert from "node:assert/strict";
import { readFile, readdir, stat } from "node:fs/promises";
import { resolve } from "node:path";
import config from "../astro.config.mjs";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const base = `${config.base.replace(/\/$/, "")}/`;
const home = new URL(base, config.site);
const pages = [
  { path: "", lang: "pt-BR", alternate: "en/" },
  { path: "en/", lang: "en", alternate: "" }
];
const documents = new Map();

for (const page of pages) {
  const path = `${base}${page.path}`;
  const html = await readFile(resolve(dist, page.path, "index.html"), "utf8");
  assert.match(html, new RegExp(`<html lang="${page.lang}">`), `${path}: wrong language`);
  assert.ok(html.includes(`rel="canonical" href="${new URL(page.path, home)}"`), `${path}: wrong canonical URL`);
  assert.ok(html.includes(`href="${base}${page.alternate}"`), `${path}: language switch missing`);
  for (const lang of pages) {
    assert.ok(html.includes(`hreflang="${lang.lang}" href="${new URL(lang.path, home)}"`), `${path}: alternate language missing`);
  }
  for (const id of ["main", "features", "compatibility", "install", "install-command"]) {
    assert.ok(html.includes(`id="${id}"`), `${path}: missing ${id}`);
  }
  assert.match(html, /application\/ld\+json/, `${path}: structured data missing`);
  assert.match(html, /data-copy/, `${path}: copy control missing`);
  assert.match(html, /<h1\b/, `${path}: heading missing`);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(ids.length, new Set(ids).size, `${path}: duplicate IDs`);
  documents.set(path, { html, ids });
}

// Verify every local href/src, including anchors and references to hashed assets.
// This catches a successful build whose assets point at a different Pages base.
for (const [path, { html }] of documents) {
  for (const [, reference] of html.matchAll(/\s(?:href|src)="([^"]+)"/g)) {
    const url = new URL(reference, new URL(path, config.site));
    if (url.origin !== home.origin) continue;
    assert.ok(url.pathname.startsWith(base), `${path}: reference outside Pages base: ${reference}`);
    let target = resolve(dist, decodeURIComponent(url.pathname.slice(base.length)));
    if ((await stat(target)).isDirectory()) target = resolve(target, "index.html");
    assert.ok((await stat(target)).isFile(), `${path}: missing file ${reference}`);
    if (url.hash) {
      const document = documents.get(url.pathname);
      assert.ok(document?.ids.includes(decodeURIComponent(url.hash.slice(1))), `${path}: broken anchor ${reference}`);
    }
  }
}

const robots = await readFile(resolve(dist, "robots.txt"), "utf8");
assert.ok(robots.includes(`Sitemap: ${new URL("sitemap-index.xml", home)}`), "Wrong robots sitemap URL");
const sitemapIndex = await readFile(resolve(dist, "sitemap-index.xml"), "utf8");
assert.ok(sitemapIndex.includes(`<loc>${new URL("sitemap-0.xml", home)}</loc>`), "Wrong sitemap index URL");
const sitemap = await readFile(resolve(dist, "sitemap-0.xml"), "utf8");
for (const page of pages) {
  assert.ok(sitemap.includes(`<loc>${new URL(page.path, home)}</loc>`), "Missing sitemap page");
}
const cssFiles = (await readdir(resolve(dist, "_astro"))).filter((file) => file.endsWith(".css"));
assert.ok(cssFiles.length, "Stylesheet missing");
const css = (await Promise.all(cssFiles.map((file) => readFile(resolve(dist, "_astro", file), "utf8")))).join("\n");
assert.match(css, /prefers-reduced-motion/, "Reduced-motion fallback missing");
console.log("Static verification passed: PT-BR, EN, metadata, sitemap, local links and assets.");
