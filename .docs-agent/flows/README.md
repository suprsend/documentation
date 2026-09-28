# Dashboard flows

One YAML file per documented dashboard procedure, e.g. `workflows/add-batch-node.yml`.
The executor writes them (see `.claude/skills/docs-ui-flows/SKILL.md` for the format);
the reviewer and the weekly `docs-ui-drift` job run them against the staging dashboard.

This folder starts empty on purpose: flows are recorded against the real UI as pages get
updated, never guessed.
