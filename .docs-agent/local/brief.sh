#!/usr/bin/env bash
# Write a brief yourself (or with Claude Code on your laptop) while it waits for approval.
# Run from the root of your suprsend/documentation clone. Needs the GitHub CLI (gh).
#
#   bash .docs-agent/local/brief.sh start 42   claim brief #42, make a branch, save the brief locally
#   bash .docs-agent/local/brief.sh check      Vale + link check on the pages you changed
#   bash .docs-agent/local/brief.sh pr 42      push and open the PR ("Closes #42", label docs-local)
#
# The PR then gets the same automated review as agent PRs (samples run on staging,
# browser checks, rendered pages) and the learner learns from how you wrote it.
set -euo pipefail
cmd=${1:-}; n=${2:-}
base=main

case "$cmd" in
  start)
    [ -n "$n" ] || { echo "usage: $0 start <brief-number>"; exit 1; }
    git fetch -q origin "$base"
    git checkout -q -b "docs-local/brief-$n" "origin/$base"
    # Tell the executor a human has it, so approving later doesn't start a duplicate.
    gh issue edit "$n" --add-label "docs-brief:local" >/dev/null
    gh issue comment "$n" --body "Writing this one by hand on \`docs-local/brief-$n\`." >/dev/null
    mkdir -p .docs-agent/run
    gh issue view "$n" --json title,body,comments \
      --jq '"# " + .title + "\n\n" + .body + "\n\n## Comments\n" + ([.comments[] | "- " + .author.login + ": " + .body] | join("\n"))' \
      > ".docs-agent/run/brief-$n.md"
    cat <<MSG

Brief #$n saved to .docs-agent/run/brief-$n.md, branch docs-local/brief-$n ready.

Write it by hand, or with Claude Code in this folder (the repo's skills load automatically):
  claude "Write the docs for brief #$n in .docs-agent/run/brief-$n.md. Follow the docs-executor
          skill's writing rules (and docs-reference-writer / docs-guide-writer per page), but
          don't push or open a PR."

Preview:  npx mintlify dev      Check:  bash .docs-agent/local/brief.sh check
Open PR:  bash .docs-agent/local/brief.sh pr $n
MSG
    ;;

  check)
    pages=$(git diff --name-only --diff-filter=AM "origin/$base"...HEAD -- '*.mdx'; git diff --name-only --diff-filter=AM -- '*.mdx')
    pages=$(echo "$pages" | sort -u | grep -v '^\.' || true)
    command -v vale >/dev/null || pip install --quiet vale
    [ -d styles/Google ] || vale sync >/dev/null
    [ -n "$pages" ] && { echo "== Vale"; vale $pages || true; }
    echo "== Broken links"; npx --yes mintlify broken-links || true
    if ! git diff --quiet "origin/$base" -- openapi.yaml; then
      echo "== OpenAPI"; npx --yes mintlify openapi-check openapi.yaml || true
    fi
    echo; echo "Code samples and browser checks run on the PR against staging."
    ;;

  pr)
    [ -n "$n" ] || { echo "usage: $0 pr <brief-number>"; exit 1; }
    title=$(gh issue view "$n" --json title --jq .title)
    git push -q -u origin HEAD
    gh pr create --base "$base" --title "$title" --label docs-local --body "Closes #$n

Written by hand from brief #$n. The docs reviewer will test it against staging and comment.

## What changed
$(git diff --stat "origin/$base"...HEAD | sed 's/^/    /')"
    ;;

  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
