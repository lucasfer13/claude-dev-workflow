---
name: pr-review
description: >-
  Quick review of someone else's pull request, merge request or branch: code quality, AI slop (filler
  code, invented service layers, wrappers, duplicated helpers, defensive noise, tests that prove
  nothing) and real edge cases, with C#/.NET, React+TypeScript and Android (Kotlin/Java) best
  practices. Diff against the development branch, no checkout. Use when the user invokes /pr-review,
  or says "review PR 123", "take a look at this MR", "review branch feat/x", "revisa la MR 123".
  Add --deep for opus.
---

# /pr-review

`$ARGUMENTS`: a PR/MR number (`123`, `#123`, `!123`), a PR/MR URL, or a branch name; optional `--deep`.
Read-only end to end: no checkout, no edits in the repo, nothing posted to the PR/MR.

## 1. Resolve the refs
- Run from the repo the PR/MR belongs to; if the cwd is not that repo, ask for its path.
- **Number or URL** — through config `review_request.tool`:
  - `gh`: `gh pr view <n> --json baseRefName,headRefName,title,body,state,url`.
  - `glab`: `glab mr view <n> -F json` (`target_branch`, `source_branch`, `title`, `description`).
  - `mcp`: the get-request tool of `review_request.mcp_server` (load it with `ToolSearch`).
  - none available → ask for the branch name.
  `HEAD = origin/<head>`, `BASE = origin/<base>`, goal = title + description.
- **Branch** → look for an open PR/MR with that head branch through the same tool; if one exists, use
  it. Else `BASE` = the repo's `DEVELOPMENT_BRANCH` (memory → `origin/develop`, `origin/dev`, else the
  default branch; ambiguous → ask). Goal = commit subjects.
- `git fetch origin <base> <head>` (quiet; merged request → only `<base>`, the head is usually gone). Never `checkout`, `pull` or `stash`.
- **Already merged**: the head branch is usually deleted and a stale local `origin/<head>` lies. Take
  the merge commit `M` from the tool (`gh pr view --json mergeCommit`, glab `merge_commit_sha` /
  `squash_commit_sha`), else grep the base's first-parent log for the request number; then
  `BASE = M^1`, `HEAD = M^2` (squash commit with one parent: `HEAD = M`). Not found → ask for the merge
  sha. Say so in the report.

## 2. Size and classify
- `git diff --stat --find-renames BASE...HEAD` and `git diff --name-status BASE...HEAD`.
- Group: **C#/.NET** (`.cs .csproj .razor`), **React/TS** (`.ts .tsx .js .jsx`, `package.json`),
  **Android** (`.kt .kts .java`, `res/**/*.xml`, `AndroidManifest.xml`), **other**.
  Production vs tests (`*Tests*`, `*.test.*`, `*.spec.*`, `src/test`, `androidTest`) vs generated
  (`Migrations/*.Designer.cs`, `ModelSnapshot`, `*.g.cs`, lockfiles, `dist/`, `build/`) — skip generated.
- Production diff > ~2000 changed lines → tell the user the review will be shallow and offer to scope
  it to a folder before launching.
- Diff only touches docs/markdown/config with no code → no agent: give a 3-line verdict yourself.

## 3. Launch `dev-workflow:mr-reviewer`
`model: opus` when `--deep`, else the agent default (sonnet). Brief (short):
repo root · `BASE` · `HEAD` · PR/MR number/URL or branch · goal (title + first lines of description) ·
files by stack and by production/test · **absolute paths** of the references to load, from the
`reference/` folder next to this skill (`ai-slop.md`, `edge-cases.md` + one per stack present) · the
project's own quality guide if its `CLAUDE.md` names one.

## 4. Report
- Write the agent's output, with a header, to
  `~/.claude/pr-reviews/<repo-key>/<number or branch-slug>-<YYYYMMDD-HHmm>.md`
  (`repo-key` as in dev-state: `owner__repo`; branch slug = branch with `/` → `-`).
  Header: repo, PR/MR link or branch, `BASE...HEAD` with short shas, model, date.
- Print to the user: verdict, slop score, findings one line each (`[SEV] file:line — problem`),
  and the report path. Not the whole report.
- Never post to the PR/MR. If the user wants a finding there, they paste it; offer the text.
