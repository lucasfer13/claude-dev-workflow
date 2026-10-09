# claude-dev-workflow

A Claude Code plugin marketplace with one plugin, **`dev-workflow`**: an evidence-gated development
workflow where the main conversation orchestrates specialist agents and **you take every decision**.

```
request → classify → architect asks (options, no decisions) → you decide → plan → GATE #1
→ branch → RED → GREEN → refactor → docs → review → GATE #2 → version → PR / MR → close
```

- **Stack-routed architects** (.NET, React, Android) survey the code and return every design choice as
  options with trade-offs; the plan is written only from your answers.
- **TDD implementers**: one agent owns test → red → implement → green per slice; 3-8 tests, only where
  they earn it.
- **Per-phase acceptance criteria** (`rules/reference/transitions.md`): a phase moves only with evidence
  seen in the session — a quoted failure, a suite total against the baseline, a sha, a grep. Each
  transition prints a `Done · Criteria · Review · Next` block; a ✘ gets two in-phase attempts, then stops.
- **Two human gates**: plan approval and final validation before the review request.
- **Checkpoints** in `~/.claude/dev-state/` so any session can resume a development (`/dev-resume`), plus
  an append-only trace rendered to a private page at the gates.
- **Guard hook** (PreToolUse) enforcing what text rules keep missing: no force-push / `reset --hard` /
  rebase of pushed history, no attribution trailers, no work-item ids or comment bloat (> ¼) in commits,
  review-request title and sections, ASCII-only tracker writes, forbidden models, no repo edits before
  the plan is approved.

## Install

```
/plugin marketplace add lucasfer13/claude-dev-workflow
/plugin install dev-workflow@lucasfer13
```

Then, in a new session, run **`/install-rules`**. A plugin cannot ship a `CLAUDE.md`, so this skill:

- writes the rules between `<!-- dev-workflow:start -->` and `<!-- dev-workflow:end -->` in
  `~/.claude/CLAUDE.md` (backup first; the rest of the file is untouched);
- copies the reference docs and scripts to `~/.claude/dev-workflow/`;
- creates `~/.claude/dev-workflow.json` from the example if you have none.

Re-run it after every plugin update. Requires Python 3 on `PATH` (for the guard and the trace renderer).

## Configure — `~/.claude/dev-workflow.json`

```json
{
  "work_item": { "prefix": "PROJ", "tool": null, "required": false, "mcp_server": null, "ascii_only": false },
  "review_request": { "tool": "gh", "mcp_server": null, "title_format": "{id} - {subject}",
                      "sections": ["Summary", "QA", "Tests"] },
  "versioning": "semver",
  "forbidden_models": []
}
```

| Key | Meaning |
|---|---|
| `work_item.prefix` | Ticket id prefix (`PROJ` → `PROJ-123`); `null` for none. Also what the guard strips from comments. |
| `work_item.tool` | `gh` for GitHub Issues (use prefix `#`; PRs get `Closes #12`), `mcp` for an MCP tracker, `null` for none. |
| `work_item.required` | Ask for a work item before starting a development. |
| `work_item.mcp_server` / `ascii_only` | MCP server of your issue tracker, and whether its writes must be ASCII. |
| `review_request.tool` | `gh` (GitHub PR), `glab` (GitLab MR) or `mcp` with `mcp_server`. |
| `review_request.title_format` / `sections` | Enforced by the guard on create/edit. |
| `review_request.max_section_words` / `banned_phrases` | Filler guard on the body: words per section (default 200) and opener phrases to deny; `[]` disables the phrases. |
| `versioning` | `semver`, or `revision` (4-part; only REVISION moves into the dev branch). |
| `forbidden_models` | Models the guard refuses for subagents. |

## What's inside

| Path | |
|---|---|
| `agents/` | architects (dotnet, react, android), implementers, test-engineer, debugger, code-reviewer, codebase-researcher, documentation-release-maintainer, issue-tracker-coordinator, review-request-publisher — invoked as `dev-workflow:<name>` |
| `skills/dev-task` | runs a development through the workflow (also triggered by "implement…", "fix…") |
| `skills/dev-resume` | resumes a development from its checkpoint, reconciled against git |
| `skills/install-rules` | installs / updates the rules |
| `hooks/` | the guard |
| `rules/` | `CLAUDE.md` rules (§0-§21), reference docs, trace renderer |

A project-level `CLAUDE.md` or project skills always win over these rules.

## Plugin 2 — `blueprint`

From an idea — or a new feature for an existing project — to a backlog the development workflow can
execute. `/blueprint` is the hub: it shows the state of every phase, asks which one to do, and resumes
or completes any of them.

```
/blueprint-scope   → product-analyst       → PRODUCT.md    vision, roles, scope, MVP, features with AC-ids, NFRs, glossary
/blueprint-tech    → project architect      → TECHNICAL.md  decisions, data model + ER, integrations, permissions,
                     | stack architects                     test strategy, threats, rollout, spikes
                     | solution-architect
/blueprint-design  → ux-designer + canvas   → DESIGN.md     flows, screens with every state, components, WCAG 2.2 AA
                                                            (or an explicit "no UI" skip)
/blueprint-backlog → delivery-manager       → BACKLOG.md    epics → stories → tasks with context pack,
                                                            Ready when, Done when; goal-based sprints
after every phase  → /blueprint-review: lint + a fresh blueprint-reviewer, cross-checked against every
                     earlier doc, fixes to each owner and decisions to you, until 0 BLOCKER / MAJOR
```

- **You decide everything.** Every agent returns options; answers go to `DECISIONS.md` and are never
  asked twice.
- **New product or evolution.** Evolutions live in `docs/blueprint/<project>/evolutions/<evo>/` as deltas
  against the base docs and are merged into them on your approval. The technical and design phases go
  to the project's own architect / designer when it has them.
- **Tasks written for a clean session.** Each agent-ready task carries only the facts it needs, where
  to touch the code, what its dependencies leave behind, what is out of scope, the checks that make it
  ready and the evidence that makes it done. `/dev-task T-03.2.1` briefs from the pack and records the
  outcome in `PROGRESS.md`.
- **Deterministic harness.** `blueprint_lint.py` checks ids, references, coverage (F → US, AC → task →
  test, MVP feature → screen, screen field → data model), sizes, dependency cycles, pack completeness,
  approvals by hash, and lists stale items after an upstream change. Hooks deny edits to an approved doc
  without a version bump and phases out of order, ask before merging an evolution, and lint every write.
- **Changes** go through `/blueprint-change`: impact by ids, cascade to stale items only, re-approval of
  only what changed.
- **Online.** A shared doc (through the host's first-party document connector, e.g. Claude Docs) the
  team edits and comments on — every edit and comment comes back as a proposal you accept or reject
  before any doc changes — plus a read-only dashboard page: phase status, traceability matrix, sprints,
  burn-up, open findings.
- Checkpoints in `~/.claude/dev-state/` like the development workflow; `/dev-resume` lists them.

```
/plugin install blueprint@lucasfer13
```

Replaces `product-planning` (uninstall it). Documents moved from `docs/product/<slug>/` to
`docs/blueprint/<project>/`.

## Development

```
python tests/test_guard.py     # guard cases against a throwaway repo
python tests/test_blueprint.py # blueprint lint and hooks against the fixture
scripts/leak-check.sh          # run before every push
```

## License

MIT
