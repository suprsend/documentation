#!/usr/bin/env node
/**
 * Open changed docs pages in a real browser (local `mintlify dev` preview) and check that
 * they render the way a reader will see them.
 *
 *   node render_check.mjs [--base http://localhost:3000] page1.mdx page2.mdx ...
 *
 * Per page, desktop (1440px) and mobile (390px):
 *   - page loads (HTTP < 400) and has no browser console errors
 *   - no unrendered MDX: raw "<Steps>", "<ParamField" etc. visible as text
 *   - every <img> loaded (naturalWidth > 0)
 *   - no horizontal scroll on mobile
 *   - every in-page link to #anchor has a target
 * Full-page screenshots → .docs-agent/run/render/ ; results → .docs-agent/run/render.json
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUT = path.join(ROOT, ".docs-agent", "run", "render");
const args = process.argv.slice(2);
const base = args.includes("--base") ? args[args.indexOf("--base") + 1] : "http://localhost:3000";
const files = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--base");
const COMPONENTS = /<\/?(Steps|Step|Tabs|Tab|CodeGroup|Accordion|AccordionGroup|ParamField|ResponseField|Expandable|Frame|Card|CardGroup|Note|Tip|Warning|Info|Check|Update)\b/;

const toUrl = (f) => "/" + f.replace(/\.mdx?$/, "").replace(/(^|\/)index$/, "");
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const results = [];
fs.mkdirSync(OUT, { recursive: true });

for (const file of files) {
  for (const [label, viewport] of [["desktop", { width: 1440, height: 900 }], ["mobile", { width: 390, height: 844 }]]) {
    const ctx = await browser.newContext({ viewport, colorScheme: "light" });
    const page = await ctx.newPage();
    const errors = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text().slice(0, 300)));
    page.on("pageerror", (e) => errors.push(String(e).slice(0, 300)));
    const r = { file, url: toUrl(file), viewport: label, problems: [] };
    try {
      const resp = await page.goto(base + r.url, { waitUntil: "networkidle", timeout: 45000 });
      if (!resp || resp.status() >= 400) r.problems.push(`HTTP ${resp ? resp.status() : "no response"}`);
      const check = await page.evaluate((re) => {
        const main = document.querySelector("main, article, #content") || document.body;
        const clone = main.cloneNode(true);             // ignore components shown inside code blocks
        clone.querySelectorAll("pre, code").forEach((n) => n.remove());
        document.body.appendChild(clone); clone.style.cssText = "position:absolute;left:-99999px";
        const text = clone.innerText; clone.remove();
        const raw = text.match(new RegExp(re))?.[0] || null;
        const brokenImgs = [...main.querySelectorAll("img")].filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.getAttribute("src"));
        const anchors = [...main.querySelectorAll('a[href^="#"]')].map((a) => a.getAttribute("href").slice(1))
          .filter((id) => id && !document.getElementById(decodeURIComponent(id)));
        return { raw, brokenImgs, anchors, overflow: document.documentElement.scrollWidth > window.innerWidth + 1 };
      }, COMPONENTS.source);
      if (check.raw) r.problems.push(`unrendered component text: ${check.raw}`);
      if (check.brokenImgs.length) r.problems.push(`images not loading: ${check.brokenImgs.join(", ")}`);
      if (check.anchors.length) r.problems.push(`anchor links without a target: #${check.anchors.join(", #")}`);
      if (label === "mobile" && check.overflow) r.problems.push("horizontal scroll on mobile (wide table or code block?)");
      r.screenshot = path.relative(ROOT, path.join(OUT, `${r.url.replace(/\W+/g, "_")}-${label}.png`));
      await page.screenshot({ path: path.join(ROOT, r.screenshot), fullPage: true });
    } catch (e) {
      r.problems.push(`failed to load: ${String(e.message || e).split("\n")[0]}`);
    }
    if (errors.length) r.problems.push(...errors.map((e) => `console error: ${e}`));
    r.ok = r.problems.length === 0;
    results.push(r);
    console.log(`${r.ok ? "PASS" : "FAIL"} ${r.url} (${label})${r.ok ? "" : " — " + r.problems[0]}`);
    await ctx.close();
  }
}
await browser.close();
fs.writeFileSync(path.join(ROOT, ".docs-agent", "run", "render.json"), JSON.stringify(results, null, 2));
process.exit(results.every((r) => r.ok) ? 0 : 1);
