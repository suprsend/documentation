# Candidate lessons

Patterns seen once. Promote to a rule on the second sighting (docs-learner, Mode A step 2).
Drop after 60 days if not seen again.

Format: `- **YYYY-MM-DD** (PR #n) — pattern → proposed rule → target file`

- **2026-10-21** (PR #284) — open question "which CLI version shipped this" was answerable from the public `suprsend/cli` repo, but a human had to answer it (≥ 1.1.0) → for public repos, find the first release containing the change (`gh release list -R suprsend/<repo>`, `git tag --contains <sha>`) and cite it as a fact instead of asking → `docs-planner/SKILL.md` step 6
