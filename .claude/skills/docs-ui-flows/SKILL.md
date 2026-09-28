---
name: docs-ui-flows
description: How the SuprSend docs agents use a real browser against the staging dashboard — writing flow files for documented dashboard procedures, capturing real screenshots for docs pages, and verifying that documented click-paths and screenshots still match the UI. Use when a docs brief lists dashboard flows, when a page describes dashboard steps or needs screenshots, or when reviewing browser results.
---

# Dashboard flows: real screenshots and real click-paths

A dashboard procedure in the docs ("Go to **Workflows**, open your workflow, add a
**Batch** node…") is only right if someone can follow it today. A flow file is that
procedure written as steps a browser can follow. Run it in **capture** mode to take the
page's screenshots. Run it in **verify** mode to prove the doc still matches the UI.

What you see in a flow run counts as a source. It is the best source for dashboard
labels, menu names and click paths. Write the doc's step text from what the flow
actually clicked, not from the PRD or memory.

Read `references/learnings.md` first.

## Flow file

One file per documented procedure: `.docs-agent/flows/<section>/<procedure>.yml`.

```yaml
page: docs/batch.mdx                 # page(s) this flow backs up (string or list)
goal: Add a Batch node to a workflow and open its settings
steps:
  - goto: /en/${workspace}/workflows/${workflow_slug}
  - expect: {role: heading, name: "${workflow_slug}"}
  - click: {role: button, name: "Edit"}
  - click: {text: "Batch", exact: true}
  - expect: {text: "Batch window"}
  - screenshot:
      out: images/batch/batch-node-settings.png
      element: {css: "aside"}        # crop to the panel (optional)
      highlight: {text: "Batch window"}   # orange outline on what the step is about
      mask: [{css: ".user-email"}]   # hide anything personal or random
      alt: Batch node settings with the batch window field highlighted
```

**Actions:** `goto` (path on the dashboard; other sites are blocked), `click`, `hover`,
`fill {target, value}`, `select {target, value}`, `press {key, target?}`,
`wait_for` (locator or `{url}`), `expect` (visible locator, `{hidden}` or `{url}` regex),
`screenshot`, `note`.

**Locators**, best first. Pick the one that uses the words the doc tells the reader to
look for, so a label change breaks the flow and tells us the doc is out of date:
1. `{role: button, name: "Save"}`: role plus visible name.
2. `{label: "Batch window"}` for form fields.
3. `{text: "Batch", exact: true}`.
4. `{testid: ...}` or `{css: ...}` only when nothing visible identifies the element.

Add `within: {...}` to scope a locator to a panel, and `nth: 1` when the same text
appears twice.

**Variables:** `${workspace}`, `${distinct_id}`, `${workflow_slug}`, `${tenant_id}` come
from `config.yml → browser.vars`. Never type real customer data or secrets into a flow.

## Capture: screenshots for a page

1. Write or update the flow. Start from the page's documented steps. One `expect` after
   each click proves the click did what the doc says.
2. Run it: `node .docs-agent/browser/run_flow.mjs --mode capture .docs-agent/flows/<id>.yml`
3. If a step fails, the UI differs from what you expected. Open the failure screenshot
   (`.docs-agent/run/browser/<id>/failed-step-N.png`) with Read. Fix the flow **and** the
   doc text to match the real UI. If you can't tell where the control went, stop and put
   the question in the PR's "Where I was unsure".
4. Look at every captured image with Read before using it. Check it shows the right
   moment, nothing personal or random is visible, and the highlight is on the right thing.
5. Put it in the page where the step is:
   ```mdx
   <Frame caption="The batch window decides how long SuprSend collects events.">
     <img src="/images/batch/batch-node-settings.png" alt="Batch node settings with the batch window field highlighted" />
   </Frame>
   ```
   Replace any `<!-- SCREENSHOT: ... -->` placeholder the step had.

## Screenshot rules

- **One screenshot per decision point**, not per click. The reader needs to see where
  they are and what to pick, not every loading state.
- **Crop to the part that matters** with `element`. Full-page shots only for "where am I"
  moments like the first screen of a new feature.
- **Highlight the one thing** the step talks about. Never more than one highlight.
- **Show the persona's world.** The staging workspace is seeded with persona data
  (Routewise tenants, `quote-expiring-reminder` workflows). Screenshots should show those
  names, matching the page's examples, not "test123".
- **Mask** emails, API keys, user avatars, timestamps, IDs that change every run.
- Keep the defaults: 1440×900, 2× scale, light mode. Don't change them per flow unless
  the doc is about a mobile or dark-mode view.
- Name files `images/<page-slug>/<what-it-shows>.png`. Alt text says what the reader sees
  and why it matters.

## Verify: does the doc still match the UI?

`node .docs-agent/browser/run_flow.mjs --mode verify --page <file.mdx>` runs the flows for
that page without overwriting anything. `.docs-agent/run/browser.json` says, per flow:
- `ok: false` + the failing step and a failure screenshot → the documented path is broken.
- a screenshot with `status: stale` (pixel diff above `browser.diff_threshold`) or
  `missing` → the image no longer matches the dashboard.

The reviewer runs this on every docs PR. The weekly `docs-ui-drift` job runs every flow
and turns failures into briefs.

## Never

- Never point a flow at production or at any site other than the dashboard.
- Never click destructive actions (delete, disable, revoke) except on the documented
  staging fixtures.
- Never commit a screenshot you haven't looked at.
- Never edit an image by hand to "fix" it. Fix the flow or the staging data and
  re-capture.
