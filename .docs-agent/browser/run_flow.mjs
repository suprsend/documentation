#!/usr/bin/env node
/**
 * Run documented dashboard flows in a real browser (Playwright + Chromium).
 *
 *   node run_flow.mjs --mode capture <flow.yml...>    take screenshots, write them to the
 *                                                     paths in the flow (docs images)
 *   node run_flow.mjs --mode verify  --page <file.mdx...>   run the flows for those pages,
 *                                                     compare screenshots with the committed
 *                                                     ones, don't overwrite anything
 *   node run_flow.mjs --mode verify  --all           every flow (weekly UI drift check)
 *
 * Flows are YAML data, not code: a fixed set of actions (see .docs-agent/flows/README.md).
 * Navigation outside browser.allowed_origins is blocked.
 * Results: .docs-agent/run/browser.json ; screenshots from verify runs and failure
 * shots: .docs-agent/run/browser/
 * Exit code 1 if any flow step failed (stale screenshots alone don't fail).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import YAML from "yaml";
import { chromium } from "playwright";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const AGENT = path.join(ROOT, ".docs-agent");
const RUN = path.join(AGENT, "run", "browser");
const CFG = YAML.parse(fs.readFileSync(path.join(AGENT, "config.yml"), "utf8")).browser;
const BASE = process.env.DASHBOARD_URL || CFG.dashboard_url;
const ALLOWED = new Set([...(CFG.allowed_origins || []), new URL(BASE).origin]);
const ENV_ALLOW = new Set(["DASHBOARD_EMAIL", "DASHBOARD_PASSWORD"]);

// ---------- args ----------
const args = process.argv.slice(2);
const mode = args.includes("--mode") ? args[args.indexOf("--mode") + 1] : "verify";
const all = args.includes("--all");
const pages = [], files = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--mode") { i++; continue; }
  if (args[i] === "--page") { while (args[i + 1] && !args[i + 1].startsWith("--")) pages.push(args[++i]); continue; }
  if (!args[i].startsWith("--")) files.push(args[i]);
}

// ---------- flows ----------
function listFlows(dir = path.join(AGENT, "flows")) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) =>
    d.isDirectory() ? listFlows(path.join(dir, d.name))
      : /\.ya?ml$/.test(d.name) ? [path.join(dir, d.name)] : []);
}
function load(file) {
  const f = YAML.parse(fs.readFileSync(file, "utf8"));
  f.file = path.relative(ROOT, file);
  f.id = f.file.replace(/^\.docs-agent\/flows\//, "").replace(/\.ya?ml$/, "");
  return f;
}
let flows = (files.length ? files.map((f) => path.resolve(f)) : listFlows()).map(load);
if (!all && !files.length) {
  const want = new Set(pages.map((p) => p.replace(/^\.\//, "")));
  flows = flows.filter((f) => [].concat(f.page || []).some((p) => want.has(p)));
}

// ---------- helpers ----------
function sub(value) {
  if (typeof value !== "string") return value;
  return value.replace(/\$\{(env:)?([A-Za-z_][\w]*)\}/g, (m, isEnv, name) => {
    if (isEnv) {
      if (!ENV_ALLOW.has(name)) throw new Error(`env var ${name} not allowed in flows`);
      return process.env[name] ?? "";
    }
    if (!(name in (CFG.vars || {}))) throw new Error(`unknown variable \${${name}}`);
    return String(CFG.vars[name]);
  });
}
function url(u) {
  const full = new URL(sub(u), BASE);
  if (!ALLOWED.has(full.origin)) throw new Error(`navigation to ${full.origin} is not allowed`);
  return full.href;
}
/** Locator spec → Playwright locator. A plain string means visible text. */
function loc(page, spec) {
  if (typeof spec === "string") spec = { text: spec };
  let l;
  const exact = spec.exact ?? false;
  if (spec.role) l = page.getByRole(spec.role, spec.name ? { name: sub(spec.name), exact } : {});
  else if (spec.label) l = page.getByLabel(sub(spec.label), { exact });
  else if (spec.placeholder) l = page.getByPlaceholder(sub(spec.placeholder), { exact });
  else if (spec.testid) l = page.getByTestId(spec.testid);
  else if (spec.text) l = page.getByText(sub(spec.text), { exact });
  else if (spec.css) l = page.locator(spec.css);
  else throw new Error(`bad locator ${JSON.stringify(spec)}`);
  if (spec.within) l = loc(page, spec.within).locator(l);
  return spec.nth !== undefined ? l.nth(spec.nth) : l.first();
}
function diffRatio(aPath, bPath) {
  const a = PNG.sync.read(fs.readFileSync(aPath)), b = PNG.sync.read(fs.readFileSync(bPath));
  if (a.width !== b.width || a.height !== b.height) return 1;
  const n = pixelmatch(a.data, b.data, null, a.width, a.height, { threshold: 0.1 });
  return n / (a.width * a.height);
}
const STABLE_CSS = `*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}
${(CFG.hide_selectors || []).join(",") || "x-none"}{visibility:hidden!important}`;

async function screenshot(page, flow, s, out) {
  const target = s.element ? loc(page, s.element) : null;
  const hl = s.highlight ? loc(page, s.highlight) : null;
  const masks = [...(CFG.mask_selectors || []).map((css) => page.locator(css)),
                 ...(s.mask || []).map((m) => loc(page, m))];
  if (hl) await hl.evaluate((el) => { el.dataset.docsHl = el.style.outline;
    el.style.outline = "3px solid #FF5A1F"; el.style.outlineOffset = "3px"; el.style.borderRadius = "6px"; });
  const opts = { path: out, mask: masks, maskColor: "#E5E7EB", animations: "disabled", fullPage: !!s.full_page };
  if (target) {
    await target.scrollIntoViewIfNeeded();
    const box = await target.boundingBox();
    const pad = s.padding ?? 16, vp = page.viewportSize();
    opts.clip = { x: Math.max(0, box.x - pad), y: Math.max(0, box.y - pad),
                  width: Math.min(vp.width, box.width + 2 * pad), height: Math.min(vp.height, box.height + 2 * pad) };
  }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.screenshot(opts);
  if (hl) await hl.evaluate((el) => { el.style.outline = el.dataset.docsHl || ""; });
}

async function runStep(page, flow, step, res) {
  const [action, arg] = Object.entries(step)[0];
  switch (action) {
    case "note": return;
    case "goto": await page.goto(url(arg), { waitUntil: "domcontentloaded" }); await page.waitForLoadState("networkidle").catch(() => {}); return;
    case "click": await loc(page, arg).click(); return;
    case "hover": await loc(page, arg).hover(); return;
    case "fill": await loc(page, arg.target).fill(sub(arg.value)); return;
    case "select": await loc(page, arg.target).selectOption(sub(arg.value)); return;
    case "press": await (arg.target ? loc(page, arg.target).press(arg.key) : page.keyboard.press(arg.key)); return;
    case "wait_for":
      if (arg.url) await page.waitForURL(sub(arg.url));
      else await loc(page, arg).waitFor({ state: "visible" });
      return;
    case "expect": {
      if (arg.url) { if (!new RegExp(sub(arg.url)).test(page.url())) throw new Error(`url ${page.url()} !~ ${arg.url}`); return; }
      if (arg.hidden) { await loc(page, arg.hidden).waitFor({ state: "hidden" }); return; }
      await loc(page, arg.visible ?? arg).waitFor({ state: "visible" }); return;
    }
    case "screenshot": {
      const committed = path.join(ROOT, arg.out);
      if (mode === "capture") {
        await screenshot(page, flow, arg, committed);
        res.screenshots.push({ out: arg.out, status: "captured" });
      } else {
        const fresh = path.join(RUN, flow.id, path.basename(arg.out));
        await screenshot(page, flow, arg, fresh);
        const exists = fs.existsSync(committed);
        const ratio = exists ? diffRatio(committed, fresh) : 1;
        res.screenshots.push({ out: arg.out, fresh: path.relative(ROOT, fresh),
          status: !exists ? "missing" : ratio > CFG.diff_threshold ? "stale" : "ok", diff: +ratio.toFixed(4) });
      }
      return;
    }
    default: throw new Error(`unknown action "${action}"`);
  }
}

async function login(browser) {
  if (process.env.DASHBOARD_STORAGE_STATE)
    return JSON.parse(Buffer.from(process.env.DASHBOARD_STORAGE_STATE, "base64").toString());
  if (!process.env.DASHBOARD_EMAIL) return undefined;          // public pages only
  const ctx = await browser.newContext({ viewport: CFG.viewport });
  const page = await ctx.newPage();
  page.setDefaultTimeout(CFG.step_timeout_ms);
  for (const s of CFG.login_steps) await runStep(page, { id: "_login" }, s, { screenshots: [] });
  const state = await ctx.storageState(); await ctx.close();
  return state;
}

// ---------- main ----------
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const storageState = await login(browser);
const results = [];
for (const flow of flows) {
  const res = { flow: flow.id, file: flow.file, page: flow.page, goal: flow.goal, mode, ok: true,
                steps: [], screenshots: [], console_errors: [] };
  const ctx = await browser.newContext({
    viewport: flow.viewport || CFG.viewport, deviceScaleFactor: CFG.device_scale_factor || 1,
    colorScheme: flow.color_scheme || "light", locale: "en-US", timezoneId: "UTC", storageState });
  await ctx.route("**/*", (route) => {
    const req = route.request();
    let top = false;
    try { top = req.isNavigationRequest() && req.frame() === req.frame().page().mainFrame(); } catch {}
    if (top && !req.url().startsWith("about:") && !ALLOWED.has(new URL(req.url()).origin))
      return route.abort("blockedbyclient");
    return route.continue();
  });
  await ctx.addInitScript((css) => {
    const add = () => { const s = document.createElement("style"); s.textContent = css; document.documentElement.appendChild(s); };
    document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", add) : add();
  }, STABLE_CSS);
  const page = await ctx.newPage();
  page.setDefaultTimeout(flow.timeout_ms || CFG.step_timeout_ms);
  page.on("console", (m) => m.type() === "error" && res.console_errors.push(m.text().slice(0, 300)));
  for (const [i, step] of (flow.steps || []).entries()) {
    const t0 = Date.now();
    try {
      await runStep(page, flow, step, res);
      res.steps.push({ i, step, ok: true, ms: Date.now() - t0 });
    } catch (e) {
      res.ok = false;
      const shot = path.join(RUN, flow.id, `failed-step-${i}.png`);
      fs.mkdirSync(path.dirname(shot), { recursive: true });
      await page.screenshot({ path: shot }).catch(() => {});
      res.steps.push({ i, step, ok: false, ms: Date.now() - t0,
                       error: String(e.message || e).split("\n")[0].slice(0, 400),
                       failure_screenshot: path.relative(ROOT, shot), url: page.url() });
      break;
    }
  }
  await ctx.close();
  results.push(res);
  const stale = res.screenshots.filter((s) => s.status !== "ok" && s.status !== "captured").length;
  console.log(`${res.ok ? "PASS" : "FAIL"} ${flow.id}  steps ${res.steps.filter((s) => s.ok).length}/${(flow.steps || []).length}` +
              (stale ? `  screenshots needing refresh: ${stale}` : ""));
}
await browser.close();
fs.mkdirSync(RUN, { recursive: true });
fs.writeFileSync(path.join(AGENT, "run", "browser.json"), JSON.stringify(results, null, 2));
console.log(`${results.length} flow(s) → .docs-agent/run/browser.json`);
process.exit(results.every((r) => r.ok) ? 0 : 1);
