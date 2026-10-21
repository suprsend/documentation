# Candidate lessons

Patterns seen once. Promote to a rule on the second sighting (docs-learner, Mode A step 2).
Drop after 60 days if not seen again.

Format: `- **YYYY-MM-DD** (PR #n) — pattern → proposed rule → target file`

- **2026-10-21** (PR #284) — brief scoped to one CLI output column from a standup line; the owner's answer showed the flag was one surface of a wider feature (preference category API, dashboard, email headers) and the merged PR covered all of it → when a signal reports a new field/flag on one surface, grep the API, dashboard and SDK repos for the same name and scope the brief to the whole feature, not the surface that was mentioned → `docs-planner/SKILL.md` step 4
- **2026-10-21** (PR #284) — open question "which CLI version shipped this" was answerable from the public `suprsend/cli` repo, but a human had to answer it (≥ 1.1.0) → for public repos, find the first release containing the change (`gh release list -R suprsend/<repo>`, `git tag --contains <sha>`) and cite it as a fact instead of asking → `docs-planner/SKILL.md` step 5
- **2026-10-21** (PR #284) — owner attached a feature spec and warned that part of it (unsubscribing from a whole promotional root category) was never built → treat specs/PRDs attached to a brief as intent, not evidence; each behaviour they describe still needs code or staging proof before it becomes a fact → `docs-planner/SKILL.md` step 5 and `suprsend-docs-writer/SKILL.md` fact rules
