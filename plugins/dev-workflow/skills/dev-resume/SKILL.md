---
name: dev-resume
description: >-
  Resume an interrupted development from its persistent checkpoint in ~/.claude/dev-state, reconciled
  against the real state of Git. Use when the user invokes /dev-resume, and equally whenever they say
  "continúa con la PROJ-123", "retoma la PROJ-123", "seguimos con la 123", "continúa con el
  desarrollo", "¿dónde lo dejamos?", "qué desarrollos tengo abiertos", "continue with PROJ-123",
  "where did we leave off?" or anything equivalent. It recovers the approved plan, user decisions,
  TDD state, progress, blockers and the concrete next action, so nothing is re-planned or
  re-researched from scratch — and it stops instead of guessing when the checkpoint and the
  repository disagree.
---

# /dev-resume

`$ARGUMENTS` is optional: a work item (`PROJ-123`), a bare number (`123`), a local id, or nothing.

Never start investigating from scratch when a checkpoint exists.

Schema, write rules, `repo-key` derivation and the body template:
`~/.claude/dev-workflow/reference/checkpoint-schema.md` (for writing, the short
`~/.claude/dev-workflow/reference/checkpoint-template.md`). The always-on rules live in the
`dev-workflow` section of `~/.claude/CLAUDE.md`.

---

## Step 1 — locate the checkpoint

Derive the `repo-key` for the current repository (recipe in the reference) and list
`~/.claude/dev-state/<repo-key>/`.

```bash
git rev-parse --show-toplevel
git remote get-url origin      # sanitise any credentials out of the URL
ls ~/.claude/dev-state/<repo-key>/
```

- **Argument given** → use that development. A bare number means `<PREFIX>-<n>` with config
  `work_item.prefix` (`123` → `PROJ-123`). Not found → say so, then list what does exist for this
  repo rather than inventing state.
- **No argument, exactly one non-terminal development** (`status` is `active`, `waiting_user` or
  `blocked`) → resume it.
- **No argument, several** → show a short list — id, phase, status, last_updated, next action in one
  line each — and ask which. Never merge two developments' state.
- **No checkpoint at all** → say so plainly and offer to start the development normally (which
  creates one). Do not fabricate a recovered state.

- **Blueprint checkpoints** (`kind: blueprint`, `blueprint-<project>…`) are listed with the others,
  labelled `blueprint`; resuming one hands over to `/blueprint`, which reads it (§1.3) — no git
  reconciliation beyond the docs' own versions.

`<id>.trace.md` files are the trace of a development, not developments — skip them when listing.
`completed` and `cancelled` developments are never offered as active; mention them only if the user
asks for history.

If the directory for this repo does not exist but another repo-key looks like the same project (a
second checkout, a renamed remote), show what you found and ask — do not silently adopt it.

## Step 2 — read it

Read the whole file. Extract: work item, `status`, `phase`, plan and `plan_version` /
`plan_approved` / `plan_fingerprint`, user decisions, research findings, branches, TDD flags,
progress, current problem, documentation and review state, version state, MR state, next action,
resume notes. From `<id>.trace.md` read only the last block. With a `trace_artifact_url`, `Artifact
read` it once so the next publish point (gate or ✘ stop) can republish it.

## Step 3 — reconcile with Git (read-only)

The checkpoint may lag if the previous session ended abruptly. **Git and the working tree are the
source of truth for the code.** The checkpoint is the source of truth for workflow, decisions,
approvals, intended plan, known progress and next action.

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git rev-parse HEAD
git log --oneline -5
```

and, when it matters, the relevant diff against the development branch
(`git diff --stat <development_branch>...HEAD`).

Compare: checkpoint branch vs actual branch · checkpoint HEAD vs actual HEAD · checkpoint changed
files vs actual status and diff.

**Never** `checkout`, `reset`, `stash`, `clean` or otherwise mutate the repository to force a match.

### Harmless drift
An extra commit that clearly belongs to the saved work, a file that moved on, a worktree now clean
because the work was committed: update the checkpoint (new `checkpoint_revision`, refreshed HEAD and
worktree flags) and carry on.

### Material drift
A different branch, a HEAD that is not a descendant of the saved one, missing expected changes,
unexplained foreign modifications, a rebase or a force-push: **STOP** and report.

```
CHECKPOINT_DRIFT_DETECTED

Checkpoint expected:
Repository currently:
Possible cause:
Options:
```

Destroy nothing. Reset nothing. Let the user decide.

## Step 4 — do not redo settled work

- `plan_approved: true`, the fingerprint matches the stored plan, no `PLAN_DEVIATION_REQUIRED`, and
  the repository state is compatible → **the approval still stands.** Do not ask
  "¿Apruebas este plan?" again merely because the session changed. Continue from the pending phase.
  The same holds for `mr_approved: true`.
- `research_status: complete` → do not re-run the full researcher. Research again only if the next
  action requires it, new evidence appeared, an architect asks for it, or the repo changed materially.
- `plan_approved: true` → do not re-launch an architect. Architecture re-enters only on
  `PLAN_DEVIATION_REQUIRED` or when the user changes a requirement.
- `tdd_red: true, tdd_green: false` → do not redesign the tests. Verify the relevant test still
  exists, then drive to GREEN. If reality is already GREEN because of work done after the last write,
  update the checkpoint and move to the next phase.
- `work_item_status: blocked_missing_parent` → the development keeps all its research and planning.
  The next action is to ask the user for a tracker parent issue or for manual root-issue creation.
  The configured integration may only create subtasks of an existing parent — there is no
  root-issue tool. Never invent a parent, a project or an issue id.

## Step 5 — show a very short summary, then continue

```
Resuming PROJ-123

✓ Checkpoint #8 recovered
✓ Plan v3 already approved
✓ Branch: feat(Orders)/PROJ-123
✓ TDD RED already confirmed
○ GREEN pending
○ Documentation pending
○ Review pending

Next action:
Finish the endpoint mapping and rerun the targeted integration test.
```

Add a `⚠` line for anything reconciliation changed. Do not make the user re-read the plan unless they
ask. Then continue the workflow from that phase — with the same approval gates for everything still
ahead.

## Step 6 — write before you work

Before delegating the resumed phase, write the checkpoint (reconciled state, new
`checkpoint_revision`, `Next Action` naming the phase about to run). That way an abrupt end to this
session is recoverable too.

---

## Safe recovery principle

Always decide from

```
CHECKPOINT  +  GIT REALITY  +  CURRENT PROJECT RULES
```

Never `CHECKPOINT SAYS X → blindly execute X`.

If the project has its own dedicated agents and workflow skills, that workflow still owns **how**
the work is done; the checkpoint only records the state it produces. Where a plan lives in a repo
artifact such as `IMPLEMENTATION_PLAN.md`, `plan_artifact`
points at it — read it back instead of re-planning.
