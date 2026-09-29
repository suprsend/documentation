# Docs agent setup

Everything you need to switch the docs agents on for **github.com/suprsend/documentation**.
Do the steps in order. Each ends with a check so you know it worked. About 2–3 hours in
total, most of it waiting for approvals and clicking through consoles.

You need: org owner on the `suprsend` GitHub org (to add the bot account), admin on both Slack workspaces, Google
Workspace access to support@suprsend.com, a SuprSend dashboard login, Postman access to
the `suprsend` team, and the GitHub CLI (`gh auth login`) plus Python 3 and Node 20 on
your laptop.

Already filled in for you in `.docs-agent/config.yml`:
- docs repo `suprsend/documentation` (Mintlify, `openapi.yaml` drives `reference/`)
- 16 public code repos to watch (SDKs, CLI, schema, skills, agents SDK)
- Slack: #documentation, #all-team, #what-is-our-differentiator,
  #deployment-notifications, #customer-feedback, plus every community channel the
  community bot is invited to
- Postman collection `27786422-d77a13c1-8f59-406d-9669-078a10d52521`
- Shadow mode on (every brief waits for your approval)

---

## 1. Docs bot account and token (15 min)

The agents act as this account. Its token is what lets one agent's issue or PR start the
next agent (GitHub's built-in `GITHUB_TOKEN` can't do that).

**Use a separate bot account, not your own.** The learner tells the agents' work apart
from human edits by the account that made them. With your own token, your review edits
would look like the agent's and it would stop learning from them.

1. **Create the account.** Sign out (or use a private window), sign up at github.com as
   e.g. `suprsend-docs-bot` with a shared team mailbox like `docs-bot@suprsend.com`. Turn on
   2FA and keep the recovery codes in your password manager.
2. **Add it to the org.** As an org owner: github.com/orgs/suprsend/people → **Invite
   member** → `suprsend-docs-bot`. Accept the invite from the bot account. Then
   `suprsend/documentation` → **Settings → Collaborators and teams** → give it **Write**.
3. **Allow fine-grained tokens for the org** (once, org owner):
   github.com/organizations/suprsend/settings/personal-access-tokens → allow fine-grained
   tokens. If "Require approval" is on, you'll approve the token in step 5.
4. **Create the token, logged in as the bot:** github.com/settings/personal-access-tokens/new
   | Field | Value |
   |---|---|
   | Token name | `docs-agent` |
   | Resource owner | **suprsend** (not the bot's personal account) |
   | Expiration | the longest your org allows (e.g. 366 days). Put a renewal reminder in your calendar a week before |
   | Repository access | **Only select repositories** → `suprsend/documentation` |
   | Contents | Read and write |
   | Issues | Read and write |
   | Pull requests | Read and write |
   | Metadata | Read (added automatically) |

   Leave everything else at "No access". The token doesn't need the code repos: they're
   public, and fine-grained tokens can always read public repos. Copy the
   `github_pat_…` value; you only see it once.
   **"suprsend" missing from Resource owner?** The list only shows orgs the account is a
   member of *and* that allow fine-grained tokens. Check, in order:
   - Logged in as the bot? github.com/settings/organizations must list `suprsend`. If
     not, the org invite (step 2) hasn't been accepted yet: github.com/orgs/suprsend/invitation.
   - Org allows them? Org owner: github.com/organizations/suprsend/settings/personal-access-tokens
     → **Settings** tab → **Allow access via fine-grained personal access tokens** → Save.
     Then reload the new-token page.
   - Still missing: use a **classic token** instead (github.com/settings/tokens/new as the bot,
     scope `repo` only, longest expiry). It reaches whatever the bot can reach, which is just
     `documentation` (write) plus public repos. If the org uses SAML SSO, click **Configure
     SSO → Authorize** next to the token afterwards.
5. If approval is required: github.com/organizations/suprsend/settings/personal-access-token-requests
   → approve `docs-agent`.

✅ Check (on your laptop): `GH_TOKEN=github_pat_… gh api repos/suprsend/documentation --jq .permissions`
shows `"push": true`.

**When the token expires,** every agent run fails at checkout. Create a new token (step 4)
and rerun `install/set-secrets.sh` to store it; nothing else changes.

## 2. Set up the Slack bots (15 min)

1. api.slack.com/apps → **Create New App** → **From an app manifest** → pick the
   **SuprSend team** workspace → paste `install/slack-app-manifest.yml` → Create →
   **Install to Workspace**. Copy the **Bot User OAuth Token** (`xoxb-…`).
2. Invite it to the 5 channels: in each of #documentation, #all-team,
   #what-is-our-differentiator, #deployment-notifications, #customer-feedback type
   `/invite @docs-agent`.
3. Repeat step 1 in the **community** workspace, deleting the `chat:write` line first (it
   never posts there). Invite it to every channel you want watched, e.g. #help,
   #general, #feedback. No IDs to copy: it watches whichever channels it's in.

New agent PRs are posted in #documentation, one thread per PR, and you're @-mentioned
when one is ready for review. To change the channel or who gets pinged, edit
`config.yml → slack.announce` (`mention` takes Slack user IDs: profile → ⋯ → Copy member ID).

✅ Check: the bot shows as a member in each channel.

## 3. Staging workspace for testing (30 min)

The reviewer runs every code sample and dashboard click-path here, so it must be safe to
send from.

1. In the SuprSend dashboard, use a dedicated workspace for docs testing (or your
   staging workspace). Turn on **Test Mode** and only add verified channels.
2. Create the fixtures the agents use (names are in `config.yml → reviewer.staging`):
   - user `docs-agent-test-user` with a team email you own
   - workflow `docs-agent-smoke-test` (any simple email workflow), committed
   - tenant `docs-agent-tenant`
3. For realistic screenshots, add persona data matching the docs examples: a tenant
   named *Routewise*, a `quote-expiring-reminder` workflow, and a few users with
   `@routewise-demo.com` emails.
4. Copy from **Developers → API Keys**: workspace key, workspace secret, and generate an
   API key. From **Account Settings → Service Tokens**: create a service token.
5. Create a dashboard user just for the agents (e.g. `docs-agent@suprsend.com`) with
   access to this workspace only.

✅ Check: triggering `docs-agent-smoke-test` for `docs-agent-test-user` from the dashboard
delivers to your inbox.

## 4. Postman key (5 min)

Postman → avatar → **Settings → API keys** → Generate. Use an account that can edit the
SuprSend collection in the `suprsend` team.

## 5. Gmail access for support@ (20 min)

1. console.cloud.google.com → pick or create a project → **APIs & Services → Library** →
   enable **Gmail API**.
2. **OAuth consent screen** → Internal → app name "Docs agent".
3. **Credentials → Create credentials → OAuth client ID → Desktop app**. Copy the client
   ID and secret.
4. On your laptop: `python3 install/gmail_token.py <client_id> <client_secret>`. Sign in
   as support@suprsend.com. Copy the refresh token it prints.
5. In the support inbox, create a label **support-resolved**. Put it on threads once
   they're resolved. Those are the ones the planner reads.

✅ Check: the script printed `GMAIL_REFRESH_TOKEN = …`.

## 6. Dashboard login for the browser (5 min)

On your laptop: `bash install/dashboard-login.sh`. A browser opens. Log in as the agents'
dashboard user from step 3.5, open the test workspace, close the window. Copy the long
value it prints.

Sessions expire. When the browser checks start failing at login, run this again and update
the secret.

## 7. Store all secrets (10 min)

`bash install/set-secrets.sh` asks for each value (hidden input) and stores it:

| Where | Name | From |
|---|---|---|
| org secret | `DOCS_AGENT_TOKEN` | step 1.4. Shared with `documentation` and the 16 code repos |
| repo variable | `DOCS_AGENT_LOGIN` | set automatically from the token (the bot's login) |
| repo secret | `ANTHROPIC_API_KEY` | console.anthropic.com |
| repo secret | `SLACK_INTERNAL_BOT_TOKEN`, `SLACK_COMMUNITY_BOT_TOKEN` | step 2 |
| repo secret | `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | step 5 |
| env `docs-staging` | `SUPRSEND_STAGING_WORKSPACE_KEY`, `…_WORKSPACE_SECRET`, `…_API_KEY`, `…_SERVICE_TOKEN` | step 3.4 |
| env `docs-staging` | `DASHBOARD_STORAGE_STATE` | step 6 |
| env `docs-staging` | `POSTMAN_API_KEY` | step 4 |
| repo variable | `SLACK_DIGEST_CHANNEL` | e.g. `C09BPA6J5QF` (#documentation) |
| repo variable (optional) | `DOCS_AGENT_MODEL` | leave unset to use the default |

The script creates the `docs-staging` environment. Optional: in repo **Settings →
Environments → docs-staging**, add yourself as a required reviewer if you want to approve
every run that touches staging. Not recommended day to day: it pauses every review.

✅ Check: `gh secret list --repo suprsend/documentation --env docs-staging` lists 6 secrets.

## 8. Install the code (10 min)

1. `gh auth refresh -s workflow` (your own login needs this scope to push workflow
   files), then `bash install/install-into-docs-repo.sh`. It asks for your GitHub username
   and the bot's login, copies everything into a branch of `suprsend/documentation` and opens a PR.
   Skills in `.claude/skills` with the same names are replaced; other skills stay.
2. Review and merge that PR.
3. `bash install/add-notify-docs.sh` opens a small PR in each of the 16 code repos. Merge
   them. (A repo with a default branch other than `main`/`master`: edit the `branches:`
   line in its PR.)
4. Repo **Settings → Actions → General**: "Allow GitHub Actions to create and approve pull
   requests" can stay **off**. The bot token opens PRs, not `GITHUB_TOKEN`.

✅ Check: Actions tab of `suprsend/documentation` shows the docs-* workflows.

## 9. First run, then shadow mode (2 weeks)

1. Actions → **docs-plan** → Run workflow. When it finishes, check the run's
   `plan-run-…` artifact. `signals-*.json` shows what it collected, and **Issues** shows
   briefs labelled `docs-brief:needs-info`.
2. Post a test request in #documentation, e.g. "The idempotency page doesn't say how long
   keys are kept." Run docs-plan again. You should get a brief and a thread reply.
3. For a brief that looks right, add the label `docs-brief:ready`. The executor opens a
   PR, the reviewer tests it and comments, then you're asked to review.
4. Comment on that PR with `@docs-agent <change>` to try iterating.
5. Merge or close it. A `skill-update` PR from the learner follows.
6. Actions → **docs-postman** → Run workflow once to check the Postman setup: it should
   open a PR that only syncs the collection into `postman/collection.json`.
7. Browser checks: `.docs-agent/flows/` starts empty, because flows are recorded against the
   real UI, not guessed. The first brief that touches dashboard steps creates the first
   flow. After that, **docs-ui-drift** has something to run each Tuesday.

For two weeks, read every brief and fix wrong ones on the issue. After that, set
`planner.auto_ready_min_confidence: 0.75` in `.docs-agent/config.yml` so confident briefs
go straight to the executor.

## If something fails

| Symptom | Likely cause |
|---|---|
| Checkout fails with "Bad credentials" | `DOCS_AGENT_TOKEN` expired or was revoked: new token (step 1.4), rerun `set-secrets.sh` |
| `Resource not accessible by personal access token` | Token is missing a permission from step 1.4, or its resource owner isn't `suprsend` |
| Code repo `notify-docs` fails | `DOCS_AGENT_TOKEN` isn't shared with that repo: org **Settings → Secrets → DOCS_AGENT_TOKEN → Repository access** |
| Executor never starts after `:ready` | The label was added with `GITHUB_TOKEN` instead of the bot token. Add it by hand, or check the step uses `DOCS_AGENT_TOKEN` |
| Slack collector `not_in_channel` | Invite the bot to that channel |
| Slack collector `missing_scope` | Reinstall the app after editing scopes |
| Gmail `invalid_grant` | Refresh token revoked or expired; rerun `gmail_token.py` |
| Browser flows fail at step 0 | `DASHBOARD_STORAGE_STATE` expired; rerun `dashboard-login.sh`. If the script said "kept cookies only" and flows land on the login page, the dashboard keeps its session in localStorage: use `DASHBOARD_EMAIL` / `DASHBOARD_PASSWORD` secrets instead and check `browser.login_steps` in config.yml |
| Snippets fail with 401 | Staging keys wrong, or the sample uses a placeholder the runner doesn't know |
| Postman publish refuses | Someone edited the collection in Postman after the agent pulled; rerun docs-postman |
| Review fails "may not modify pipeline files" | A docs PR touched `.github/`, `.docs-agent/` or `.claude/` |
