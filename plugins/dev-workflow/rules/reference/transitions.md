# Phase transitions — criteria, summary, review

Referenced by global `CLAUDE.md` §21. Every criterion is blocking unless marked ⚠. **H** = enforced by
the plugin's PreToolUse hook as well. Each block the user gets: `Done · Criteria · Review · Next`
(plus `Agent` and `Attempts` when they apply) — written in the user's language; the render script
accepts the Spanish equivalents too. "Review" = commands and shas only.

Phase names (the `TO` of each block, also what the trace page's rail reads):
`CLASSIFIED · QUESTIONS · PLAN · APPROVED · BRANCH · RED · GREEN · REFACTORED · DOCUMENTED · REVIEWED ·
READY · REVISION · MR · COMPLETED`; cross-cutting: `ROOT CAUSE · PLAN_DEVIATION · DONE · RESUMED`.

## 1 · REQUEST → CLASSIFIED · auto
- Class with a one-line reason
- Work item loaded, or its absence asked (§4)
- Pre-flight: target-branch `git log` and work-item status show the work is not already done
- Repo, stack and development branch identified, each with its source
- Earlier handoff / checkpoint reconciled with git, if any
- Trace file created (§19); the artifact is first published at gate #1

Summary: class and why · ticket subject/status/assignee · target branch + last commit · workflow and agents · contradictions found.
Review: `git log --oneline -5 origin/<dev>` · the ticket.

## 2 · CLASSIFIED → QUESTIONS · architect pass 1 · human gate
- Architect chosen by the stack found, with reason
- Survey names the seam, the closest analogue and the affected tests and doubles
- Every verified fact cites `file:line` or the query run
- Every choice with more than one reasonable answer as options (≥2, pros/cons); none taken
- Repo conventions listed apart, as "following existing convention"
- Pending consultants or research named

Summary: framing in 3-5 lines · questions with options · conventions not asked · ticket/handoff/code contradictions.
Review: plan file §1-§2 · open 1-2 cited `file:line`.

## 3 · QUESTIONS → PLAN · pass 2 · auto
- Every question answered; answers verbatim in the plan
- No new decision taken without asking
- Each task: agent, exact files, signatures (no bodies)
- Tests 3-8 per slice, one line each; existing tests that change listed
- Risks and out of scope; ≤150 lines (one repo) or ≤300

Summary: tasks one line each with agent · new and affected tests · layers/contracts touched and not · main risk.
Review: plan §3 against your answers · plan tests: does any existing assertion change value?

## 4 · PLAN → APPROVED · gate #1 · human gate
- Explicit approval of this plan version (§7); "sí, pero…" → back to 3
- Trace artifact published (first time) and its URL in `trace_artifact_url`
- `plan_fingerprint` stored in the checkpoint

Summary: goal, behaviour change, out of scope · task count, planned tests, expected suite total · risks.
Review: the whole plan file.

## 5 · APPROVED → BRANCH · auto
- User's uncommitted changes untouched and named, or tree clean
- Target fetched before branching
- Name follows the verified convention
- Pushed with upstream

Summary: branch and base sha · foreign uncommitted files.
Review: `git status --short` · `git log -1 origin/<branch>`.

## 6 · BRANCH → RED · auto
- Every planned test exists
- Real failure quoted per test
- Valid RED: assertion, or compilation because the planned member doesn't exist yet — never fixture, restore, path or syntax
- Test commit before the implementation commit

Summary: per test — name, behaviour pinned, failure in one line, type · planned tests not written and why.
Review: `git show <test-sha>`.

## 7 · RED → GREEN · auto
- Build 0 errors; warnings ≤ baseline (measured after clean)
- Suite 0 failed; total = baseline + added − removed, every removal explained
- 1 run, or 3 identical when static/shared state is touched
- No existing assertion changes value without user authorisation
- Files touched ⊆ plan files, checked by the main thread on `git diff --name-only <dev>...HEAD`
  against the plan's file list; an extra file without a reason is ✘
- Format clean (`dotnet format --verify-no-changes` or the stack's formatter)
- Secrets/PII grep on the diff clean (connection strings, tokens, plates, DNI/NIE, emails in logs)
- Writes to a live external environment (via MCP) listed in the trace: entity, action, how to revert
- Commits pushed; local == remote

Summary: files per layer with lines added · commits with sha and subject · totals vs baseline · agent's minor decisions · off-plan files.
Review: `git diff --stat <dev>...HEAD` · `git log --oneline <dev>..HEAD`.

## 8 · GREEN → REFACTORED · optional
- Concrete reason: duplication, cohesion, readability
- Same suite totals before and after
- No behaviour or scope change

Summary: what and why in one line, or "not applicable" and why.
Review: `git show <refactor-sha>`.

## 9 · GREEN → DOCUMENTED · auto
- Ticket/plan-id grep on comments of the diff: empty (**H**)
- Comment lines < ¼ of added code lines over the development diff (**H**, blocking)
- Stale-doc grep over the repo: clean
- Changed endpoints: XML docs and `ProducesResponseType` up to date
- CHANGELOG / REVISION per convention, or "not applicable" with reason

Summary: docs touched (file → what) · both grep results · version before → after · comment ratio.
Review: `git diff <dev> -- CHANGELOG.md`.

## 10 · DOCUMENTED → REVIEWED · auto
- Reviewer ran on a code diff, on a model that did not write most of it (model cited), or skipped
  as docs-only with reason
- Diff touches PII, auth, credentials or an external integration → security reviewer ran too
- 0 CRITICAL / IMPORTANT open
- Each finding has a destination: fixed (sha), deferred (ticket) or rejected (reason)
- Fixes re-verified: build and totals
- Main thread's independent grep for what the reviewer may have missed
- At most 2 fix loops (§15); then back to the user

Summary: severity → finding → destination · what the reviewer did not cover · what the independent check found.
Review: rejected and deferred findings · `git show <fix-sha>`.

## 11 · REVIEWED → READY · gate #2 · human gate
- Final build, tests and format with real numbers
- Diff = plan: nothing planned missing, nothing unplanned (`git diff --name-only` against the plan)
- 2-4 "look here" anchors (`file:line`) for the user's own read of the diff: what the reviewer
  did not cover, the riskiest change, any surplus-code finding left as IMPROVEMENT
- Anything unverified marked as such (e.g. a live write against an external environment)
- Live-environment changes and deployment preconditions listed
- A shared library/package changed → consumers listed and a local pack verified
- Trace artifact republished, so the page you review is current

Summary: development report (§14) · all earlier transitions as n/n ✔ · pending and unverified.
Review: the trace page · `git diff <dev>...HEAD`.

## 12 · MR APPROVED → REVISION · auto
- Target refreshed immediately before
- Branch contains the current `origin/<dev>` (merge, never rebase), or the conflict reported
- Version = latest on target + 1 per convention, or pipeline-managed
- Quick verification after the bump; pushed

Summary: version before → after and source file · latest version seen on target.
Review: `git show origin/<dev>:<version-file>`.

## 13 · REVISION → MR · auto
- Review-request URL exists, no conflicts
- Title per config `review_request.title_format` and only the sections from config
  `review_request.sections` (**H**)
- Every number in `## Tests` observed in this session; "failed before" only if RED proved it
- No attribution trailer or signature (**H**)
- Tracker note with the review-request URL where the project requires it, ASCII if config
  `work_item.ascii_only` is true (**H**)
- Consumer of an unpublished shared library/package → review request marked BLOCKED
- Review-request pipeline green, or pending noted for closure

Summary: URL, branches, commit count, assignee · body corrections before publishing · tracker note yes/no · pipeline.
Review: the review request · the tracker note.

## 14 · MR → COMPLETED · auto
- Checkpoint `status: completed`; trace artifact republished
- Pipeline result recorded (or still pending, with who follows it)
- Follow-ups with a destination: proposed ticket or note
- Memory updated only with durable knowledge

Summary: out-of-scope leftovers · natural next ticket.
Review: the trace page.

## Cross-cutting
**SYMPTOM → ROOT CAUSE** — symptom reproduced, or why it can't be · hypothesis confirmed by evidence · ≤3 hypotheses without new evidence · regression test fails for that cause. Summary: symptom → evidence → cause, one line each; discarded hypotheses.

**any → PLAN_DEVIATION** — what the plan assumed vs what the code requires · options for the user, none taken · approval invalidated; nothing done past the deviation point. Summary: phase and task where it stopped; options.

**TRIVIAL → DONE** — change = micro plan · targeted build/tests with numbers · greps clean (**H**) · committed and pushed. Summary: files, sha, totals.

**RESUME → RESUMED** — checkpoint read whole · git reconciled: branch, HEAD descendant, no material drift · earlier approvals still valid (same fingerprint) · trace artifact read before republishing. Summary: last transition, current phase, next action, what reconciliation changed.
