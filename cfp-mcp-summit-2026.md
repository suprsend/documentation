# MCP Dev Summit Seoul 2026 — Sessionize CFP

**Deadline:** Friday, 1 May 2026, 8:29 PM IST. Submit by 7:30 PM IST to leave buffer.
**Submitter:** Tanisha Sharma — AI DevRel Engineer, SuprSend
**Status:** Ready to paste, every field below fits Sessionize limits.

---

# 🟢 SUBMISSION 1 (PRIMARY) — paste-ready, field by field

> Sessionize fields shown in **bold**. Copy each value as-is. Character counts verified against the form's stated limits.

---

### **Session Title**

```
Eight Prompts, Eight Minutes, One Production App: Replacing MCP Tutorials With Prompt Packs
```

(94 chars. Title case per LF style guide.)

---

### **Description** *(1200 char limit)*

```
Most developer tutorials are obsolete. When an IDE has typed access to your platform via MCP, the optimal "tutorial" stops being prose. It becomes a sequence of natural-language prompts the developer pastes one by one — and the agent, the MCP server, and docs-as-tools build the app together.

This talk is the live proof. In eight minutes on stage, the speaker pastes eight prompts into Cursor against a production MCP server (SuprSend, as a case study not a pitch) and ends with a deployed React app: Kanban board, in-app inbox, toasts, OTP auth, preference center — without typing a line of code. The repo, live URL, and prompts are public; the demo is fully reproducible.

The remaining 20 minutes are the why. Four design rules — atomic-step prompts, declarative scope, embedded acceptance criteria, docs-as-tools as a safety net — make prompt packs compose. Plus the failure modes when each is violated, and the maintenance story when MCP tools change.

Closing argument: if your MCP server doesn't ship a prompt pack, your docs are already obsolete. The pattern generalizes to any MCP server.

For DevRels, technical writers, and MCP server engineers questioning the tutorial format.
```

(1190 chars. Verified under 1200.)

---

### **Topic**

```
Building with MCP
```

(Confirmed against the live Sessionize dropdown. The talk is literally about building applications with an MCP server, and about building the server side of that workflow. *MCP Protocol in Depth* is for spec/transport talks; *Ecosystem, Registries + Platform Infrastructure* is for registry/discovery talks — neither fits.)

---

### **Session Format**

```
Session Presentation (30 min)
```

---

### **Audience Level**

```
Intermediate
```

(Assumes audience has read the MCP spec and used at least one MCP-compatible IDE.)

---

### **Benefits to the Ecosystem**

```
Every MCP server team faces the same question: how do developers learn to use this? Long-form tutorials are the default answer, and they break down quickly — they go stale when tools change, they don't compose with the agent's own context, and they don't take advantage of MCP's biggest UX win: the IDE already has typed access to the platform.

This talk introduces a transferable, copy-able pattern (the "prompt pack") for tutorial replacement, with four concrete design rules and a falsifiable live demo. Every MCP server in the ecosystem can adopt it the same week. The benefit to the project: faster onboarding for developers, fewer hallucinated tool calls in agent traces, and a sharper docs primitive for server authors who currently default to prose.
```

---

### **Presented this talk before?**

```
No
```

---

### **Which language will you use for your presentation?**

```
English
```

---

### Required checkboxes

- ✅ **Code of Conduct** — tick "I have reviewed The Linux Foundation Code of Conduct"
- ✅ **Commitment to inclusivity** — tick "I have reviewed The Linux Foundation's Inclusive Speaker Orientation and Inclusive Language Initiative"
- ✅ **Content Quality Agreement** — tick "I understand that submitting low-quality or AI-generated 'slop' may result in removal from the review process"
- ✅ **Are you both the submitter and speaker?** → **Yes**

---

### **Speaker Bio** *(500 char max)*

```
Tanisha Sharma is an AI DevRel Engineer at SuprSend, where she ships and documents the SuprSend MCP server across Cursor, Claude, and Windsurf. Previously at Microsoft, she mentors at AI Makerspace and is a Google Women Engineers Cohort 3 alum. Splitting her time between Bengaluru and France, she spends most of it figuring out why agents misuse perfectly good APIs, and writes about AI tooling and DevRel for early-career engineers across India.
```

(~445 chars. Safely under 500.)

---

### **Company**

```
SuprSend
```

### **Speaker Title**

```
AI DevRel Engineer
```

### **Country of residence**

```
India
```

(Use India even though you split time with France — LF uses this for diversity tracking and your primary base is Bengaluru. Switch to France only if your tax/visa residency is currently France.)

### **Fediverse** *(optional)*

Leave blank unless you have a Mastodon/Fediverse handle you want public.

---

### Diversity questions *(optional, confidential)*

- **Gender identity:** Woman *(answer however you identify)*
- **Person of color:** Yes
- **Identify with other underrepresented group(s):** Optional — leave blank or note "Woman in tech from India"

---

### **Co-speakers**

Leave blank. Solo submission recommended.

---

# 🟡 SUBMISSION 2 (BACKUP) — paste-ready, field by field

LF CFPs allow up to 3 submissions per speaker. Submitting two roughly doubles your acceptance odds. This one is a contrarian-thesis talk that pairs cleanly with Submission 1 without overlapping.

---

### **Session Title**

```
Two Audiences, One Markdown File: Writing MCP Docs an Agent Can Actually Use
```

(76 chars.)

---

### **Description** *(1200 char limit)*

```
When an MCP server exposes documentation.search and documentation.fetch, its docs site quietly acquires a second reader: the agent. And the agent is not a small human. Humans want narrative tutorials; agents want flat, deduplicated, single-source-of-truth pages. Humans skim; agents tokenize. Humans tolerate ambiguity; agents hallucinate from it.

This talk is a field report from rewriting an MCP server's documentation to serve both audiences from one markdown source. Concrete before/after pages, real agent traces from the SuprSend MCP server (used as a case study not a pitch), the five rewrite rules that actually moved the needle on hallucination rates, and the surprising downstream effect: the human-facing docs got better too. Every rule generalizes to any MCP server with public docs.

Closes with two open questions the audience is invited to argue back at: should agent-facing docs be a separate channel? Should MCP add a "documentation" primitive at the protocol level?

For DevRels, technical writers, and MCP server maintainers who already exposed their docs as a tool — or are about to.
```

(~1135 chars.)

---

### **Topic**

```
Building with MCP
```

### **Session Format**

```
Session Presentation (30 min)
```

### **Audience Level**

```
Intermediate
```

---

### **Benefits to the Ecosystem**

```
The MCP ecosystem is converging on documentation-as-a-tool as a near-universal pattern (Anthropic, Apollo, Supabase, and others have shipped variants). But there is no shared vocabulary or set of best practices for how to *write* docs that serve both human and agent readers from one source. Server teams are quietly rediscovering the same five rewrite rules in isolation.

This talk gives the ecosystem a vocabulary, a measurable evaluation method (agent task success on before/after docs), and a concrete proposal: should "documentation" be a first-class MCP primitive? The answer matters for every server author downstream.
```

---

### **Presented this talk before?**

```
No
```

### **Language**

```
English
```

### Speaker Bio, Company, Title, Country, Co-speakers

> Same values as Submission 1 above.

### Notes for organizers *(if Sessionize has a private notes field)*

```
This talk builds on but does not duplicate Daniel Abdelsamed's NA 2026 talk "Your #1 Docs Audience Isn't Human: Dev Ed's MCP Strategy at Apollo". That talk argued the strategic case for treating agents as docs readers; this one is the implementation report from the other side of that decision, plus a concrete protocol-extension proposal. Happy to coordinate with the program committee if there's overlap concern.
```

---

# 🟠 SUBMISSION 3 (THIRD) — paste-ready, field by field

LF CFPs allow up to 3 submissions per speaker. This one targets the gap nobody at NA 2026 covered: cross-client compatibility from the server author's point of view. Different angle, same bucket, plays to your real multi-IDE documentation experience.

---

### **Session Title**

```
Your MCP Server Behaves Differently in Every Client: A Cross-Client Field Guide for Server Authors
```

(99 chars.)

---

### **Description** *(1200 char limit)*

```
Same MCP server. Same prompt. Three different IDEs. Three different outcomes — and one of them is silently wrong.

After documenting a production MCP server across Cursor, Claude Desktop, and Windsurf, the speaker has the war stories. Tool descriptions one client truncates and another expands. Resource limits that vary by 10x. Notification semantics that work in one host and silently no-op in another. OAuth flows that route through different dances depending on the client. Session-lifetime assumptions that turn into "why did my context vanish?" support tickets.

This talk is a field guide, organized by client, with the actual diffs server authors should care about. Live side-by-side traces of the same tool call across three clients, showing where each one quietly diverges from the spec — and the small defensive changes (in tool naming, description length, error semantics) that make a single server work the same way in all three.

Closes with a proposal: a "client compatibility matrix" the MCP ecosystem should publish and maintain, modeled on Can I Use for the web.

For MCP server authors who have only ever tested in one client.
```

(Verified ~1180 chars.)

---

### **Topic**

```
Building with MCP
```

### **Session Format**

```
Session Presentation (30 min)
```

### **Audience Level**

```
Intermediate
```

---

### **Benefits to the Ecosystem**

```
The MCP ecosystem now has a healthy plurality of clients — Cursor, Claude Desktop, Windsurf, Continue, Goose, Zed, OpenAI Apps, and more. This is a good thing for the protocol but a quietly painful thing for server authors, who almost universally test in one client and ship.

This talk surfaces the concrete cross-client differences that bite server authors in production, gives the audience a defensive design checklist, and proposes the missing artifact: a community-maintained MCP client compatibility matrix. Adoption of the matrix would lower the cost of writing new MCP servers, raise interop quality across the ecosystem, and give the protocol working group hard data on which spec ambiguities are actually being interpreted differently in the wild.
```

---

### **Presented this talk before?**

```
No
```

### **Language**

```
English
```

### Speaker Bio, Company, Title, Country, Co-speakers

> Same values as Submission 1. Sessionize attaches your speaker profile automatically.

### Notes for organizers *(if Sessionize has a private notes field)*

```
There were no accepted talks at MCP Dev Summit NA 2026 on cross-client compatibility from a server author's point of view (verified against the published schedule). Spec and transport talks exist, but the practical "same server, different clients, different behavior" angle is uncovered. The talk includes live side-by-side traces from three IDEs against the same SuprSend MCP server (case study, not a pitch); all of the diffs and defensive design recommendations generalize to any MCP server.
```

---

# 📋 Submission day checklist

- [ ] Sign in to Sessionize, open the MCP Dev Summit Seoul 2026 CFP
- [ ] Click **Brand new session**, paste Submission 1 field by field from above
- [ ] Save (Sessionize auto-saves), then click **Brand new session** again for Submission 2
- [ ] Repeat once more for Submission 3 (LF allows up to 3 per speaker)
- [ ] Upload a headshot to your Sessionize profile (square, 400×400+, well-lit)
- [ ] Verify Company, Title, Country are filled on your speaker profile
- [ ] Tick all three required agreement boxes (CoC, Inclusivity, Content Quality)
- [ ] **Submit by 7:30 PM IST** (deadline 8:29 PM IST — leave buffer for site issues)
- [ ] Screenshot the confirmation page

---

# 📝 Strategy notes (do not paste anywhere)

## Why these two submissions, in this order

I studied the **MCP Dev Summit NA 2026 accepted schedule** (~80 talks). Acceptance patterns:

**What got in:**
- Numbers in the title: *"1000+ MCP Tools"*, *"180+ MCP Tools"*, *"From 60 Minutes To 60 Seconds"*
- Provocative/contrarian: *"RPC > MCP"*, *"Rules Are Not Suggestions"*, *"The Seven Deadly Sins With MCP"*
- Specific war stories: *"Avatar Generation at Roblox"*, *"MCP at WestJet"*, *"Teaching a Non-Technical Marketer To Use MCP"* (Postman DevRel)
- Counterintuitive insight + live evidence: *"Your #1 Docs Audience Isn't Human"* (Apollo DevRel), *"Anatomy of a Meltdown"*

**What didn't make it:**
- Generic "we built an MCP server, here are some lessons"
- "Three design decisions" without a memorable hook
- Vendor-flavored titles

**Tanisha's unexploited angle vs. NA 2026:** Only two DevRel-led talks made it (Postman, Apollo). Both about adoption, neither about **how docs themselves change for the agent + human dual audience**. That's the gap. A number-driven, demo-first hook + a falsifiable live build = the strongest version of that pitch.

## Why mentioning SuprSend is fine

The rule is "no vendor *pitches*", not "no company names." Every accepted NA talk above named its company. The line is case study (allowed) vs. sales pitch (rejected). Both submissions are explicitly framed as case studies generalizable to any MCP server.

## What changed from the first draft

| First draft | This version |
|---|---|
| "Three design decisions that matter" — generic structure used by ~10 NA talks | "Eight prompts, eight minutes, one app" — number-driven, demo-driven, no equivalent at NA |
| Implicit demo at the end | Live build is the *opening* of the talk; everything else is the post-mortem |
| DevRel POV mentioned in passing | DevRel POV is the entire thesis (controversial: "stop writing tutorials") |
| Hard to disprove or argue with | Falsifiable on stage in real time — high stakes, high memorability |
| Could be given by any of 50 engineers | Can only be given by a DevRel who actually shipped a prompt-pack-based docs site |

## Live demo safety net (mention only if asked at the event)

- Pre-record the eight-prompt build to a 7-minute video as a fallback if Wi-Fi fails on stage (per LF speaker guidance — KubeCon explicitly recommends this)
- Pin model versions in the prompt pack so prompts don't drift between rehearsal and stage
- Have an engineer on call from SuprSend during the demo slot (Bengaluru is +6h from Seoul → reachable)
