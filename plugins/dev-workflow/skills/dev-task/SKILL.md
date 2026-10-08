---
name: dev-task
description: >-
  Run a software development task through the global orchestrated agent workflow: work-item context
  from an optional issue tracker, task classification, codebase research, stack-routed architecture,
  an approval gate on the plan, TDD RED to GREEN, documentation and version maintenance, code
  review, and a second approval gate before the review request (PR/MR). Use when the user invokes
  /dev-task, and equally whenever they say "haz la PROJ-123", "implementa…", "añade…", "arregla…",
  "corrige este bug…", "modifica…", "cambia…", "refactoriza…", "crea un endpoint…", "necesito…", or
  the English equivalents "implement…", "add…", "fix…", "create an endpoint…" or "I need…". Works
  for .NET, React, Android and other stacks — the stack is detected, never assumed.
---

# /dev-task

`$ARGUMENTS` is the task. It may be a work item (`PROJ-123`), a sentence
(`Añadir cancelación de reservas`), or a bug report (`Arreglar el crash al volver de background`).

Invoking this skill does **not** mean "do everything without stopping". It runs the workflow defined
in the `dev-workflow` section of the global `~/.claude/CLAUDE.md`, including
both approval gates. That section is the authority; this file is the entry point and the checklist.

You are the ORCHESTRATOR. You are the only one who talks to the user.

Every development started here is **checkpointed**: persistent state in
`~/.claude/dev-state/<repo-key>/<development-id>.md`, owned by you, written at state transitions —
see §19 of the global rules; write it from `~/.claude/dev-workflow/reference/checkpoint-template.md`
(full schema and `repo-key` recipe in `checkpoint-schema.md`, only when in doubt). To pick a development back up later, use `/dev-resume` (or
just say "continúa con la PROJ-123"). The approval gates are unchanged.

## Sequence

0. **Checkpoint.** As soon as the request is identified as an active development, create the
   checkpoint — even before a work item exists (`local-YYYYMMDD-HHmm-<slug>`, migrated to
   `<PREFIX>-<n>` when the work item appears). From then on, write it at every state transition
   listed in §19: work item, research, user decisions, each plan version and its approval, **before
   delegating any mutating phase**, branch creation, TDD RED, each significant implementation block,
   any block or unexpected failure, TDD GREEN, documentation, review, before review-request approval,
   after the version bump, after the review request. On `TRIVIAL`, checkpoint only if it earns it,
   and keep it minimal.

1. **Work item.** `$ARGUMENTS` names a work item → read it first yourself, if `work_item.mcp_server`
   is configured, and write the `WORK_ITEM` block (§4); `issue-tracker-coordinator` only for
   searches, parent inference or creation. That block is the input to everything downstream. No work
   item and config `work_item.required` is true → ask once whether to create the task; never create
   it unasked; never invent a work item id or a branch name built from one.
   (The tracker integration may only support creating subtasks of an existing parent — see §4 of the
   global rules.)

2. **Classify**: `READ_ONLY | TRIVIAL | STANDARD | COMPLEX | BUG | DOCUMENTATION_ONLY |
   RELEASE_PREPARATION | CODE_REVIEW`. Quick inspection if needed. In doubt → STANDARD.

   **`--evaluate`** (`/dev-task <id> --evaluate`): an evaluation, not a development. Classify `READ_ONLY`
   and write the checkpoint with `verdict` (`defect` | `not_code`), `verdict_reason` and `verdict_at`
   instead of a development checkpoint. One checkpoint file per work item and repo: an existing
   development checkpoint is opened, never duplicated; re-evaluating rewrites `verdict*`.

   **Starting after an evaluation**: `/dev-task <id>` without the flag, when a `completed` `READ_ONLY`
   checkpoint exists for that work item, reclassifies that same file (`status: active`, new `task_class`,
   `verdict*` kept) instead of creating another.

3. **Route.**
   - READ_ONLY → answer it with whichever agents help. No branch, no implementation gate.
   - TRIVIAL → quick inspection → **micro plan** → STOP for approval → one implementer
     (test/change/test in one run) → targeted verification → report. If complexity appears,
     `FAST_PATH_ESCALATION_REQUIRED` and reclassify.
   - DOCUMENTATION_ONLY → quick research → micro plan → approval →
     `documentation-release-maintainer` → targeted validation.
   - CODE_REVIEW → `code-reviewer`, read-only.
   - RELEASE_PREPARATION → the release flow in `~/.claude/dev-workflow/reference/release-and-review.md` §12.
   - BUG → the bug workflow: research → `debugger` → root cause → architect → fix plan → approval →
     regression test first → RED → implementer → GREEN → documentation → review.
   - STANDARD / COMPLEX → the full workflow below.

4. **STANDARD / COMPLEX.**
   `codebase-researcher` → stack routing → the relevant architect(s) only, in parallel when
   independent → research loop (resume the **same** researcher, max 3) → planning loop (ask the user,
   resume the **same** architect) → one unified plan.

5. **Approval gate #1.** Show the plan, then STOP and ask for approval in the user's language, e.g.
   "¿Apruebas este plan para empezar el desarrollo?" / "Do you approve this plan?"
   `PLAN_APPROVED = false` until an unambiguous yes. "Sí, pero cambia X" is **not** approval — resume
   the architect and ask again. Until approved: no branch, no edit, no new test, no migration, no
   commit, no push.

6. **Implement.** Detect `DEVELOPMENT_BRANCH` (`dev` vs `develop` — never hardcoded, saved to memory)
   → create the branch safely with the repo's real naming convention → implementer(s), each owning
   its slice's RED → GREEN (`test-engineer` only when §9 says it earns itself) → refactor if it earns
   it → run the relevant suite with the project's real commands. Every brief says: few tests, short
   comments (global `CLAUDE.md` §9, §2).

7. **Finish.** `documentation-release-maintainer` (comments, OpenAPI/Swagger/Scalar, CHANGELOG,
   version metadata) → `code-reviewer` → quality loop (max 2) → final validation.

8. **Report + approval gate #2.** Compact real-data report, then STOP and ask, in the user's
   language, e.g. "¿Validas el desarrollo y quieres que prepare/publique la MR?" / "Do you validate
   this development and want me to prepare/publish the review request?"
   `MR_APPROVED = false` until then.

9. **Review request.** Prepare the integration: version bump per config `versioning` (§12 of
   `~/.claude/dev-workflow/reference/release-and-review.md`; if the pipeline owns it, do not
   duplicate it) → quick verification → commit → push → you create the review request yourself with
   the tool in config `review_request.tool` or its MCP server (title from
   `review_request.title_format`, sections from `review_request.sections`, from the actual diff —
   rules in `release-and-review.md` §12 and §16; the guard hook rejects a malformed one). No
   publisher agent unless the user asks for it.

## Blueprint tasks

`$ARGUMENTS` is a blueprint task id (`T-03.2.1`) or the user names one → find it in
`docs/blueprint/**/BACKLOG.md` (or `backlog/EP-xx.md`).
- The **context pack is the brief** to the architect, as written — do not load the blueprint documents
  unless the pack anchors one. The task's `Ready when` is checked first; an unchecked item → stop and
  say which.
- Its `Done when` lines are added to the acceptance criteria of the closing transitions (GREEN and
  gate #2), each with its evidence.
- On start and on closing, write the task's row in the blueprint's `PROGRESS.md` (`in-progress` →
  `done` with branch, review request link, `Done-when n/n`, date) and print `TASK → DONE`. Never edit
  BACKLOG.md from a development.
- The same applies when the pack names a project's own entry skill instead of this one.

## Non-negotiables

- Checkpoint written before every mutating phase, and immediately when blocked. `Next Action` is
  always one concrete executable step.
- Both approval gates. No silent scope growth.
- Every phase transition prints its block with acceptance criteria and evidence (global `CLAUDE.md`
  §21, per-phase criteria in `~/.claude/dev-workflow/reference/transitions.md`), appends it to
  `<id>.trace.md` (artifact republished only at gate #1, gate #2, closure, and any stop on a ✘), and
  adds a line to the checkpoint's `## Transitions`.
- Architect pass 1 is questions only; the user takes every decision.
- Never assume the stack. Never assume `dev` vs `develop`. Never invent a scope, a work item id, a
  version number or a test result.
- With the `revision` versioning convention, a feature going into dev/develop moves **REVISION
  only** — never MINOR.
- Do not over-orchestrate: an obvious change gets a micro plan and the main thread edits it itself.
- If a project has its own dedicated agents and workflow skills, use those instead — they
  outrank this one. The main thread still orchestrates.
