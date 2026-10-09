# Versioning, review request and integrations — detail

Moved out of global `CLAUDE.md` to keep it light; section numbers kept so `§12`, `§16`, `§18`
references still resolve. Read the section you need **before** a version bump, a release or a
review request.

## 12. Versioning

Config `versioning` picks the default convention:

- `revision` — `MAJOR.MINOR.PATCH.REVISION`: SemVer for the first three; REVISION identifies a
  non-production revision / deployment (`1.2.0.12`).
  - **Into `dev` / `develop`: only REVISION moves** (`1.4.7.12 → 1.4.7.13`) — feat, fix and chore
    alike. A feature does **not** bump MINOR on its way into dev; MINOR moves when preparing a
    pre-release stage.
  - **Promotion to a pre-release stage** is the semantic bump: from the included changes take the
    highest impact (`breaking > feature > fix`) → MAJOR / MINOR / PATCH (`1.4.7` + compatible
    feature → `1.5.0`); handle REVISION per the project convention; update CHANGELOG, version
    source and release docs; run the validations.
  - **REVISION across a semantic change** (`1.4.7.x → 1.5.0.x`: reset to 1, to 0, continue, or the
    pipeline number) is project-specific — infer it from the history or ask. Never invent it.
- `semver` — plain SemVer, bumped directly on the change with the highest impact in the release; no
  revision digit.

**Source of truth — investigate, never assume the local file**: target branch, version file,
`Directory.Build.props`, `.csproj`, `AssemblyInfo`, `package.json`, Gradle, tags, pipelines, recent
review requests, tooling. **If the pipeline increments the version/revision, do not duplicate it in
code.** Refresh the target first so it is not stale.

**When**: not at branch creation, not while researching — when preparing the integration (after
implementation, tests, docs, review, validation and review-request approval), then a quick
verification, then the review request. If the repo's verified convention bumps before final review,
follow the repo. Invariant: every integrated development gets its own bump.

**Concurrency**: several branches in flight → fetch the target, check its latest version, take the
next revision per the real convention. Never invent numbers; a pipeline that resolves it wins.

DEV needs no formal release test documentation — but tests still run and the review request keeps
`## Tests`.

**RELEASE_PREPARATION** ("prepare for a pre-release stage", "prepara la release"): release
conventions → included changes → semantic impact → `documentation-release-maintainer` (version +
changelog) → verification → summary → user approval → promotion / review request if requested. Not
a new feature.

TRIVIAL changes skip the documentation agent, but one that ends in a review request into dev/develop
still follows the version and git/review-request rules — the fast path cuts orchestration, never
these rules.

## 16. Review request (PR / MR)

Created by the main thread (§18).

Into `DEVELOPMENT_BRANCH` (never hardcoded). Title from config `review_request.title_format`
(default `{id} - {subject}`), preferring the real subject. Body, in the sections from config
`review_request.sections` (default), in this order:

```markdown
## Summary

## QA

## Tests
```

- **Summary** — with GitHub Issues, its first line is `Closes #12` so the merge closes the issue
  (`Refs #12` when the PR only covers part of it). Then what changes and why, before/after behaviour, important decisions, edge cases, API
  contracts, integration behaviour, out of scope, deployment preconditions, compatibility. Neither
  "Updated provider and tests." nor a novel.
- **QA** — verifiable scenarios, preferably Given/When/Then: happy path, regression, edge cases,
  integration, failures. Never a scenario nobody validated.
- **Tests** — real commands with real results, e.g.
  `` `dotnet test -c Release --no-build` (342 passed, 0 failed) ``; name important new tests; write
  "This test failed before the implementation." only if TDD RED proved it.

Describe what shipped, in this order of authority: **the actual diff**, then the work item, the
approved plan, TDD evidence, tests, documentation changes, reviewer findings. Never something
planned but not implemented.

**No filler.** Say what a reviewer cannot read off the diff — why, decisions, risks — never a
file-by-file retelling of it. No opening boilerplate ("This PR introduces…", "In this PR we…"), no
closing summary of the summary. Each section stays under config `review_request.max_section_words`
(default 200) and avoids `review_request.banned_phrases`; the guard denies either.

**No work item at review-request time**, and `work_item.required` is
true → stop and ask: create it now, or another convention the project supports. Never invent one.

## 18. Integrations

- **Issue tracker** (optional) — GitHub Issues through `gh` when config `work_item.tool` is `gh`
  (`gh issue view|list|create`; no close/edit/comment without an explicit instruction); otherwise the
  MCP server named in config `work_item.mcp_server`, when set.
  Read: get issue, search issues, list projects, list trackers, list statuses, list priorities, list
  members. Write (gated by the integration's own write flag): create item, add note, add relation,
  assign, set status, set priority. **No top-level issue creation** if the integration only supports
  subtasks of an existing parent — see §4. If config `work_item.ascii_only` is true, tracker notes
  must be plain ASCII (some trackers 500 on non-ASCII input, e.g. emoji).
- **Review request** — the tool in config `review_request.tool` (`gh`, `glab`) or an MCP server
  named in `review_request.mcp_server`. There is **no merge tool** and no branch / commit / file API:
  branches, commits and pushes go through `git` in the shell; only the review request itself goes
  through the configured tool. Long descriptions go via a file argument when the tool supports one.

The main thread uses the issue tracker and creates the review request itself — the guard hook
validates title, sections and signature, so no publisher agent is needed;
`review-request-publisher` stays for an explicit request. `issue-tracker-coordinator` is used only
for searches, parent inference or creation. Other agents get the context they need instead of direct
external access.
