---
name: suprsend-docs-support
description: "Default skill for any SuprSend question that isn't strictly authoring JSON or running a CLI command. Fetch, search, read, and explain SuprSend documentation; answer \"how does X work\", \"what is X\", \"show me the docs for X\". Provides docs-over-SSH (ssh suprsend.sh), the .md-suffix raw markdown URL convention, LLM-friendly bulk endpoints, in-app chat, AI copilot, Slack community, and email support. Examples that should load this skill: \"fetch batching documentation\", \"explain digest nodes\", \"show me the inbox channel docs\", \"what fields does an email variant have\", \"how do conditions work in templates\"."
metadata:
  author: "suprsend"
  category: "support"
---

# SuprSend Documentation & Support

## Documentation

SuprSend docs are available at [docs.suprsend.com](https://docs.suprsend.com). For agent access, pick the method that matches the tools available in the environment:

### Preferred: docs over SSH (when `ssh` is available)

If the agent can run shell commands, use the docs-over-SSH service. It exposes the full docs tree as a virtual filesystem under `/suprsend/`, browsable with standard Unix tools:

```bash
# Search for a topic across all docs
ssh suprsend.sh grep -rl 'inbox' /suprsend/

# Read a specific guide
ssh suprsend.sh cat /suprsend/docs/quick-start-guide.md

# Find SDK reference pages
ssh suprsend.sh find /suprsend/reference -name '*sdk*.md'

# Search the API reference with context
ssh suprsend.sh grep -r 'workflow' /suprsend/reference/ --include='*.md' -l
```

The VFS mirrors the live URL structure: `/suprsend/reference/agent-sdk.md` ↔ `https://docs.suprsend.com/reference/agent-sdk`. Any standard Unix tool (`grep`, `find`, `cat`, `head`, `tail`) works.

Run `ssh suprsend.sh agents` to print these instructions in a form you can append to an `AGENTS.md` or similar agent-instruction file.

### Fallback: append `.md` to any docs URL (when `ssh` is not available)

Every page at `https://docs.suprsend.com/<path>` is also served as raw markdown at `https://docs.suprsend.com/<path>.md`. Use this when the agent can fetch URLs but cannot run shell commands:

- HTML page → `https://docs.suprsend.com/docs/quick-start-guide`
- Markdown for the same page → `https://docs.suprsend.com/docs/quick-start-guide.md`

This works for both `/docs/` (guides) and `/reference/` (API reference) paths.

### Bulk LLM endpoints

For wholesale ingestion rather than targeted lookups:

- **Index**: `https://docs.suprsend.com/llms.txt` — lightweight page listing with descriptions
- **Full content**: `https://docs.suprsend.com/llms-full.txt` — complete documentation in a single file

## Getting Help

### 1. Kai — AI Copilot (instant, in-dashboard)

Kai is SuprSend's built-in AI copilot, available inside the dashboard at [app.suprsend.com](https://app.suprsend.com). Access it via the orb in the bottom-right corner, or use the keyboard shortcut:

- **macOS**: `Cmd + /`
- **Windows / Linux**: `Ctrl + /`

Kai can answer questions about SuprSend features, help debug workflow configurations, and guide you through setup steps.

### 2. In-App Chat (fast, human support)

Users logged into the SuprSend dashboard can reach the support team directly. Click the **?** (help) icon in the top navigation bar, then select **"Chat with us"** from the dropdown menu.

### 3. Slack Community (public, community + team)

Join the SuprSend community Slack for discussions, questions, and announcements:

https://join.slack.com/t/suprsendcommunity/shared_invite/zt-3932rw936-XNWY1RC8bsffh4if4ZyoXQ

### 4. Email Support

For detailed issues, bug reports, or account-specific questions:

**support@suprsend.com**

