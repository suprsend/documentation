# Metrics

`prs/<pr-number>.json`: one file per closed docs-agent PR (category, merged, human edit
ratio, review rounds, hours to close). Written by `scripts/collect_feedback.py` and
committed to `main` by the docs-learn workflow.

`scripts/autonomy_report.py` turns them into the per-category graduation table the
learner posts in its weekly digest.
