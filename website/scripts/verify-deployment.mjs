import assert from "node:assert/strict";
import { setTimeout } from "node:timers/promises";

const input = process.argv[2];
assert.ok(input, "Usage: npm run verify:deployment -- https://host/Pages-base/");
const home = new URL(input.endsWith("/") ? input : `${input}/`);
assert.ok(["http:", "https:"].includes(home.protocol), "Expected an HTTP(S) URL");
const revision = process.env.EXPECTED_REVISION;

async function get(url, type) {
  const response = await fetch(url, { signal: AbortSignal.timeout(10_000), cache: "no-store" });
  assert.equal(response.status, 200, `${url}: HTTP ${response.status}`);
  assert.match(response.headers.get("content-type") ?? "", type, `${url}: unexpected content type`);
  return response.text();
}

async function verify() {
  for (const [path, lang] of [["", "pt-BR"], ["en/", "en"]]) {
    const url = new URL(path, home);
    const html = await get(url, /text\/html/);
    assert.ok(html.includes(`<html lang="${lang}">`), `${url}: wrong language`);
    if (revision) {
      assert.ok(html.includes(`name="deployment-revision" content="${revision}"`), `${url}: deployment has not propagated yet`);
    }
    const css = html.match(/<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"/);
    const script = html.match(/<script\b[^>]*src="([^"]+)"/);
    const image = html.match(/<img\b[^>]*src="([^"]+)"/);
    assert.ok(css && script && image, `${url}: missing CSS, script or application image`);
    for (const [reference, type] of [[css[1], /text\/css/], [script[1], /(?:javascript|ecmascript)/], [image[1], /image\/webp/]]) {
      const asset = new URL(reference, url);
      assert.equal(asset.origin, home.origin, `${asset}: asset points at another origin`);
      assert.ok(asset.pathname.startsWith(home.pathname), `${asset}: asset outside Pages base`);
      await get(asset, type);
    }
  }
}

for (let attempt = 1; attempt <= 6; attempt++) {
  try {
    await verify();
    console.log(`Deployment verified: PT-BR, EN, CSS, JavaScript and application image at ${home}`);
    break;
  } catch (error) {
    if (attempt === 6) throw error;
    console.warn(`Attempt ${attempt}/6: ${error.message}. Retrying in 5 seconds.`);
    await setTimeout(5_000);
  }
}
