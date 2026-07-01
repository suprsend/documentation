# Napkin

## Corrections
| Date | Source | What Went Wrong | What To Do Instead |
|------|--------|----------------|-------------------|
| 2026-07-01 | self | Used `subgraph` with `direction LR` to wrap mermaid rows; the doc's renderer ignored it and collapsed the diagram to vertical | This renderer does not honor per-subgraph `direction`. Keep `flowchart LR` and shorten labels to fit width instead of wrapping via subgraphs |

## User Preferences
- Docs are Mintlify (.mdx). Mermaid diagrams: prefers horizontal (`flowchart LR`), small text (~14px), black-and-white with transparent fills (borders only), stepped gray border shades to fake a gradient.
- Wants intro/description copy framed around what it solves for the end user, not just mechanics.
- Likes diagram nodes to be clickable, linking to the matching doc section anchors via mermaid `click ... href "#anchor"`.

## Patterns That Work
- Section anchors in Mintlify are slugified from heading text (e.g. `## Connector setup on SuprSend` -> `#connector-setup-on-suprsend`, `### 1. Add Prefix to track events` -> `#1-add-prefix-to-track-events`).
- Use `&amp;` for ampersands inside mermaid node labels to avoid parse issues.

## Patterns That Don't Work
- Per-subgraph `direction` for wrapping mermaid flows (see Corrections).

## Domain Notes
- Repo: SuprSend documentation (Mintlify). Working file this session: docs/segment.mdx (Segment connector integration).
- The zoom/pan controls the user saw are from the VS Code Mermaid preview extension, NOT from Mintlify output or the diagram — nothing in the .mdx controls them.
