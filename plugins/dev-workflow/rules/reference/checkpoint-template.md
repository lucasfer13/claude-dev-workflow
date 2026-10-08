# Checkpoint — write template

What to use when writing `~/.claude/dev-state/<repo-key>/<development-id>.md`. Field names and values
are fixed (a Dev Hub reads them); unknown → `null`, never invented. Doubts, `repo-key` recipe, id
migration, trace format: `checkpoint-schema.md`.

```markdown
---
schema_version: 1
development_id: PROJ-123              # or local-YYYYMMDD-HHmm-<slug>
previous_development_id: null
repo_key: acme__shop__orders-api
repo_root: ~/src/orders-api
title: <subject>
status: active                        # active | waiting_user | blocked | completed | cancelled
phase: planning                       # work_item · research · planning · waiting_for_plan_approval · branch_preparation
                                      # · tdd_red · implementation · tdd_green · documentation · review · fixing · validation
                                      # · waiting_for_mr_approval · revision_preparation · publishing_mr · blocked · completed · cancelled
task_class: STANDARD
verdict: null                         # READ_ONLY evaluations only: defect | not_code
verdict_reason: null
verdict_at: null
work_item_status: existing            # none | existing | created | pending_creation | blocked_missing_parent | declined_by_user
work_item_id: PROJ-123
work_item_parent: PROJ-100
development_branch: develop
working_branch: null
branch_status: pending                # not_needed | pending | created
commit_status: none                   # none | partial | committed
push_status: none                     # none | pushed
mr_status: none                       # none | approved_pending | created | blocked
plan_version: 1
plan_approved: false
plan_fingerprint: null                # sha256 of the approved plan text / plan file
plan_artifact: null                   # path when the plan lives in a file
research_status: not_started
research_loops_used: 0
tdd_red: false
tdd_green: false
tdd_exception: null
documentation_status: pending
review_status: pending
review_fix_loops_used: 0
version_before: null
version_after: null
development_revision_status: pending  # pending | completed | pipeline_managed | not_applicable
mr_approved: false
mr_created: false
mr_iid: null
mr_url: null
trace_artifact_url: null
checkpoint_revision: 1
last_updated: "<ISO-8601 with offset>"
git_head_at_checkpoint: null
dirty_worktree_at_checkpoint: false
---
# Development State
## Work Item
## Requirement Summary
## User Decisions
## Research Findings
## Approved Plan
## Progress
## TDD
## Files / Areas Changed
## Current Problem
## Validation
## Transitions
## Next Action
## Resume Notes
```

Keep only sections with content. `Next Action` is mandatory: one concrete executable step + the expected
next state. `Transitions`: one line per transition, append-only (`<YYYY-MM-DD HH:mm> FROM → TO · n/n ✔ ·
evidence`); the full block goes to `<id>.trace.md`.

**Every write**: `checkpoint_revision += 1`, refresh `last_updated`, `git_head_at_checkpoint`,
`dirty_worktree_at_checkpoint`; one whole-file write (or temp file + move). Material plan change →
`plan_version += 1`, `plan_approved: false`, new fingerprint. `blocked_missing_parent` → `status:
blocked`, `phase: work_item`, next action asks for a tracker parent.

**Never**: secrets, tokens, cookies, auth headers, credential-bearing strings, unnecessary PII, full
logs, diffs, file contents, chain-of-thought.
