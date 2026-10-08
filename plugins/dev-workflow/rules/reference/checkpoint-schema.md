# Development checkpoint — schema, write rules, template

Canonical reference for `~/.claude/dev-state/<repo-key>/<development-id>.md`.
Used by `/dev-task`, `/dev-resume` and by any orchestrated development started in plain language.

The **ORCHESTRATOR owns the checkpoint**. There is no checkpoint agent. Subagents return a
`CHECKPOINT_DELTA` block with facts from their own phase; the orchestrator integrates it.

---

## 1. repo-key

Filesystem-safe, stable, reasonably unique. Prefer the git remote.

```bash
# inside the repo
git rev-parse --show-toplevel
git remote get-url origin
```

Derivation, in order:

1. **Remote exists** — strip the scheme, any `user:password@` or token, the host, the port and the
   trailing `.git`; keep the path segments; lowercase; replace every run of non
   `[a-z0-9._-]` characters with `-`; join the segments with `__`.

   ```
   https://oauth2:ghp-xxxx@github.com/acme/shop/orders-api.git
   git@github.com:acme/shop/orders-api.git
   → acme__shop__orders-api
   ```

   **Always sanitise**: the credential part of a remote URL must never reach the key, the path or
   the file content.

2. **No remote** — the repository root's directory name, plus a short stable discriminator derived
   from its absolute path, to avoid collisions between two same-named checkouts:

   ```
   ~/src/orders-api  →  orders-api__local-4f1c9a
   ```

   Any stable short hash of the normalised absolute path works; keep using the same one for that
   path once chosen.

3. **Not a git repository at all** — same as (2), based on the working directory.

Record the derived key in the checkpoint (`repo_key`) so it is never recomputed differently later.

---

## 2. development-id

- Work item exists → `PROJ-123`
- No work item yet → `local-YYYYMMDD-HHmm-<short-slug>`, e.g. `local-20260826-1045-ticket-filter`

**Migration when the work item appears** (`PROJ-124` created or associated):

1. Write the full, updated content to `PROJ-124.md` — same state, `development_id` and
   `work_item_id` updated, `previous_development_id` recorded, `checkpoint_revision` incremented.
2. Verify the new file reads back correctly.
3. Only then delete the `local-*.md` file.

Never leave two active checkpoints describing the same development.

---

## 3. Frontmatter schema (`schema_version: 1`)

```yaml
---
schema_version: 1

development_id: PROJ-123              # <PREFIX>-<n> | local-YYYYMMDD-HHmm-<slug>
previous_development_id: null         # set when migrated from a local id
repo_key: acme__shop__orders-api
repo_root: ~/src/orders-api
title: Return expired regulations in the regulations listing

status: active                        # active | waiting_user | blocked | completed | cancelled
phase: implementation                 # see the phase list below
task_class: STANDARD                  # READ_ONLY | TRIVIAL | STANDARD | COMPLEX | BUG
                                      # | DOCUMENTATION_ONLY | RELEASE_PREPARATION | CODE_REVIEW
verdict: null                         # READ_ONLY evaluations only: defect | not_code
verdict_reason: null                  # one line, why
verdict_at: null                      # ISO-8601 timestamp of the verdict

work_item_status: existing            # none | existing | created | pending_creation
                                      # | blocked_missing_parent | declined_by_user
work_item_id: PROJ-123
work_item_parent: PROJ-100

development_branch: develop           # detected, never assumed
working_branch: feat(Orders)/PROJ-123
branch_status: created                # not_needed | pending | created
commit_status: partial                # none | partial | committed
push_status: none                     # none | pushed
mr_status: none                       # none | approved_pending | created | blocked

plan_version: 3
plan_approved: true
plan_fingerprint: "sha256:9f2c…"      # of the approved plan text stored below
plan_artifact: null                   # path when the plan lives in a file (e.g. IMPLEMENTATION_PLAN.md)

research_status: complete             # not_started | in_progress | complete
research_loops_used: 1                # MAX_RESEARCH_LOOPS = 3

tdd_red: true
tdd_green: false
tdd_exception: null                   # reason string when TDD was legitimately skipped

documentation_status: pending         # pending | in_progress | completed | not_applicable
review_status: pending                # pending | in_progress | findings_open | completed
review_fix_loops_used: 0              # MAX_REVIEW_FIX_LOOPS = 2

version_before: 1.7.1.32
version_after: null
development_revision_status: pending   # pending | completed | pipeline_managed | not_applicable

mr_approved: false
mr_created: false
mr_iid: null
mr_url: null

trace_artifact_url: null             # private artifact rendered from <id>.trace.md (§9)

checkpoint_revision: 8
last_updated: "2026-08-26T10:45:12+02:00"
git_head_at_checkpoint: "a1b2c3d4e5f6…"
dirty_worktree_at_checkpoint: true
---
```

Fields may be absent or `null` while unknown — nothing has to exist from the first write. Do not
invent a value to fill a field, and do not rename a field or a state; the vocabulary is stable so a
future Dev Hub can read it.

### Evaluation (`task_class: READ_ONLY`)

One checkpoint file per work item and repo. `/dev-task <id> --evaluate` writes a `READ_ONLY` checkpoint
with `verdict`, `verdict_reason` and `verdict_at`; only that evaluation session writes a `READ_ONLY`
checkpoint. Re-evaluating rewrites `verdict*`. Starting the development reclassifies the same file
(`status: active`, new `task_class`) and keeps `verdict*`; evaluating a work item that already has a
development checkpoint opens that one.

### phase values

```
work_item · research · planning · waiting_for_plan_approval · branch_preparation · tdd_red
implementation · tdd_green · documentation · review · fixing · validation
waiting_for_mr_approval · revision_preparation · publishing_mr · blocked · completed · cancelled
```

### status values

`phase` says **where** we are; `status` says **whether it can continue**.

```
active · waiting_user · blocked · completed · cancelled
```

`completed` and `cancelled` are never listed as active by `/dev-resume`.

### plan fingerprint

`plan_fingerprint` is a stable hash of the approved plan text (`sha256:` prefix). It is a
change-detection aid, **not** a security mechanism. On a material plan change:
`plan_version += 1`, `plan_approved: false`, new fingerprint.

Compute it over the exact `## Approved Plan` body, e.g.:

```bash
printf '%s' "$PLAN_TEXT" | sha256sum
```

When the plan lives in a file (a project's own `IMPLEMENTATION_PLAN.md`), set `plan_artifact` to its path
and fingerprint that file's content instead of duplicating the whole plan in the checkpoint — keep a
condensed step list in `## Approved Plan` so a resume works even if the artifact was deleted.

---

## 4. Body template

Keep only the sections that carry information. Compact — state and minimal evidence, never a log.

```markdown
# Development State

## Work Item
PROJ-123 — <subject>. Parent: PROJ-100. The tracker remains the source of truth for the full issue.

## Requirement Summary
Goal and the acceptance details that matter. Not a copy of a huge tracker description.

## User Decisions
- Expired regulations must also be returned.
- Do not modify `/tickets/search`.
- Keep the existing OData endpoint unchanged.

## Research Findings
- ASP.NET Core 8; existing features use MediatR + FluentValidation.
- Integration tests use WebApplicationFactory.
- Development branch is `develop`.
- Version source of truth is `Directory.Build.props`.

## Approved Plan
Plan version: 3 · Approved: yes
1. …
2. …
3. …

## Progress
Completed:
- …
In progress:
- …
Pending:
- …

## TDD
### RED
Status: confirmed
Test: `RegulationsQueryTests.Returns_expired_when_flag_set`
Observed failure: <trimmed to the relevant assertion>
Why this is the expected RED: the flag is not read anywhere yet.
### GREEN
Status: pending

## Files / Areas Changed
- `src/…/CentralTicketsProvider.cs`
- `tests/…/CentralTicketsProviderTests.cs`

## Current Problem
Symptom · Evidence · Already tried · Do not repeat

## Validation
Commands actually run and their real results.

## Documentation
Comments cleanup · OpenAPI · CHANGELOG · version metadata.

## Versioning
version_before → version_after; who owns REVISION (manual or pipeline).

## Review
Blocking findings only, and which are fixed.

## MR
iid · URL · source → target · title.

## Risks / Preconditions
…

## Transitions
- 2026-09-14 10:02 REQUEST → CLASSIFIED · 3/3 ✔ · STANDARD; develop b452b25 has no PROJ-123 commit
- 2026-09-14 10:40 QUESTIONS → PLAN · 4/4 ✔ · Q1-Q3 answered; plan v2 142 lines
- 2026-09-14 12:15 RED → GREEN · 6/6 ✔ · suite 348/0 (baseline 342 +6); pushed 9f1c2ab

## Next Action
Finish the mapping in `CentralTicketsProvider` and run
`dotnet test --filter CentralTicketsProviderTests`.
Expected next state: TDD GREEN.

## Resume Notes
- Do NOT rerun architecture planning. Plan v3 is already approved.
- RED has already been demonstrated.
- Do NOT increment REVISION yet.
- Documentation and final review are still pending.
```

### Section rules

- **Requirement Summary** — enough to recover intent. The tracker stays the source of truth.
- **User Decisions** — anything whose loss would change the development. No irrelevant chat.
- **Research Findings** — only the facts needed to resume. Durable project knowledge belongs in agent
  memory, not here.
- **Approved Plan** — the plan that was actually approved, with enough detail to continue **without
  re-running architecture**. Not a one-liner. Not approved yet → `Approved: no`.
- **Progress** — current state, not a diary. Finished items move into `Completed`.
- **TDD** — minimal evidence, never a full test log.
- **Files / Areas Changed** — paths only. Git holds the content.
- **Current Problem** — updated **immediately** when blocked; `Already tried` and `Do not repeat`
  exist so a fresh session does not re-run a failed strategy.
- **Transitions** — append-only, one line per phase transition (global `CLAUDE.md` §21): time,
  FROM → TO, criteria passed, key evidence. The audit trail of why each phase was left; never rewritten.
  The full block goes to the trace file (§9).
- **Next Action** — **the most important section**. Exactly one concrete, executable action, plus the
  expected next state. Never "Continue implementation."
- **Resume Notes** — what must not be redone.

---

## 5. Never store

Chain-of-thought · whole conversations · full build output · large stack traces · full diffs · file
contents · every tool call · repo commit history.

**Never**: secrets, passwords, tokens, cookies, authorization headers, private keys,
credential-bearing connection strings, unnecessary PII. Sanitise errors and logs before pasting.

A normal checkpoint should stay quick for another Claude to read end to end.

---

## 6. Write rules

Every valid write increments `checkpoint_revision` and refreshes `last_updated`,
`git_head_at_checkpoint` and `dirty_worktree_at_checkpoint`.

**Atomicity** — prepare the full new content, write it to a temporary file in the same directory,
then replace the previous file with a single move. Never truncate or delete the last valid checkpoint
first.

```bash
d=~/.claude/dev-state/<repo-key>; mkdir -p "$d"
# write $d/.PROJ-123.md.tmp with the complete new content, then:
mv -f "$d/.PROJ-123.md.tmp" "$d/PROJ-123.md"
```

A single whole-file `Write` of complete content is also acceptable — it replaces in one step. What is
forbidden is a partial or multi-step rewrite that can leave the file half-written.

### Update triggers — write on state transitions, not on tool calls

Mandatory:

- a request becomes an active development (**initial checkpoint**, even with no work item yet)
- work item loaded, associated, created, or found to be blocked for a missing parent
- initial research complete, and any research-loop finding that materially changes architecture
  understanding, scope, integration or constraints
- the user answers a functional question → `User Decisions`, before resuming an architect
- every material plan version (`plan_version += 1`), and **immediately** on approval
  (`plan_approved: true`) before any implementation starts
- **before delegating** any expensive or mutating phase, with `Next Action: Run <phase> for …`
- branch created → development branch, working branch, HEAD, worktree state
- TDD RED confirmed — do not wait for implementation
- after each significant implementation block (a use case, persistence, a screen, an integration);
  rule of thumb: if losing the context now would cost more than a few minutes of re-reasoning, write
- **when blocked or when something fails unexpectedly** — before trying a new approach
- TDD GREEN confirmed
- documentation phase done
- review done (blockers and loop count only)
- before asking for review-request approval, the checkpoint must already read: implementation
  complete, tests complete, documentation complete, review complete, `waiting_for_mr_approval`
- after the REVISION bump (`version_before`, `version_after`,
  `development_revision_status: completed`, or `pipeline_managed` when the pipeline owns it — never
  invent the number)
- after the review request is created: iid, URL, source, target, title, then `status: completed`,
  `phase: completed`

Not after every Grep, Read or shell command. That is noise.

### Fast path

Do not bureaucratise `TRIVIAL`. Create a checkpoint only when the change will outlast a single
trivial operation, there is a branch or a work item, interruption is a realistic risk, or it will
end in a review request. Then keep it very compact — frontmatter plus `Next Action` is enough.
No checkpoint for a ten-second typo fix.

---

## 7. `CHECKPOINT_DELTA` from subagents

Mutating agents (implementers, `test-engineer`, `documentation-release-maintainer`) and read-only
agents alike report facts from **their own phase only**. They never rewrite global workflow state and
never invent approvals.

```
CHECKPOINT_DELTA:

Phase:
Completed:
Pending:
Current problem:
Next action:
```

The orchestrator integrates it into the single checkpoint file.

---

## 8. Lifecycle

- **Completed** — after the MR is created: `status: completed`, `phase: completed`. The file is kept,
  not deleted, so it stays consultable.
- **Cancelled** — only when the user explicitly abandons it: `status: cancelled`, plus the reason if
  given. Never delete it automatically.
- **Stale** — never auto-close by age. A development may sit untouched for weeks and still be active.

Everything stays in one flat directory per repo key: `status` distinguishes active from finished, so
no `active/` and `completed/` subdirectories are needed and detection stays trivial.

---

## 9. Trace file and trace artifact

`<development-id>.trace.md` next to the checkpoint: the full §21 block of every transition, append-only,
never rewritten (a correction is a new block). Migrates with the checkpoint (§2). Same "never store"
rules as §5. Criteria per phase: `transitions.md`.

```markdown
---
development_id: PROJ-123
title: <subject>
repo_key: acme__shop__orders-api
working_branch: feat(Orders)/PROJ-123
development_branch: develop
---
## 2026-09-15 11:40 · RED → GREEN
Agent: dotnet-implementer
Done: A1-A5: DeregisterAsync, validator with no future date
Criteria:
- ✔ build 0 errors · 84 warnings = baseline (after clean)
- ✔ suite 1177 passed / 0 failed · total = 1172 + 6 − 1 (deletion authorised)
- – refactor: not applicable (no new duplication)
Attempts: 1 — new warning CS8618 → initialized
Review:
- `git diff --stat develop...a52da3a`
Next: documentation on the diff
```

Heading `## <YYYY-MM-DD HH:mm> · FROM → TO`, `TO` from the phase names in `transitions.md` (the page's
phase rail reads them). Criteria marks: `✔ ✘ ⚠ –`; an unmarked criterion renders as ⚠. A block may be
written in the user's language — the render script accepts either the English keywords above or their
Spanish equivalents (`Agente · Hecho · Criterios · Intentos · Para revisar · Siguiente`).

**Publish** only at gate #1, gate #2, closure, and any stop on a ✘ — the file is appended at every transition:

```bash
python ~/.claude/dev-workflow/scripts/render.py <dev-state>/<repo-key>/<id>.trace.md <scratchpad>/trace-<id>/index.html
```

Then Artifact publish of that `index.html`: first time with `icon: "timeline"` and a one-line
description, storing the returned URL in `trace_artifact_url`; afterwards with `url:
<trace_artifact_url>`. A session that did not publish it reads it once (`action: "read"`) first. The page
is private; never share it without the user asking. A failed publish is noted and retried at the next
publish point — it never blocks the phase.

