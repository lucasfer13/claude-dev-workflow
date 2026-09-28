---
name: blueprint
description: Hub for defining and planning a new product or an evolution of an existing project — product definition, technical design, UX/UI design, backlog with agent-ready tasks — with a checkpoint, a consistency review after every phase, and a shared online doc the team edits and comments on. Use when the user invokes /blueprint, says "quiero definir un producto", "planifica este evolutivo", "nueva funcionalidad para <proyecto>", "retoma el blueprint", "¿en qué fase está el blueprint?", "define a new feature", "plan this product", or anything equivalent. It shows the state of every phase and asks which one to do, resume or complete.
---

# /blueprint

You (main thread) orchestrate and are the only one who talks to the user. Agents ship as
`blueprint:<name>` when installed as a plugin. `<skills>` = the parent of this skill's directory.

- Contract (ids, layout, return format, context pack): `<skills>/blueprint/reference/contract.md`
- Transitions and gate criteria: `<skills>/blueprint/reference/transitions.md`
- Online doc and dashboard: `<skills>/blueprint/reference/online.md`
- Lint: `python <skills>/blueprint/scripts/blueprint_lint.py <root>` · approve: `--approve <doc>`

## 1. Locate

1. **Mode and project.** Current repo with a `docs/blueprint/<project>/` → that project. The user names
   a new feature for an existing project → **evolution** `docs/blueprint/<project>/evolutions/<evo>/`
   (base = the project root if it has approved docs; none → the technical owner documents the as-is of
   the affected area only). Nothing yet → **new**. Confirm mode, project and slug in one question.
2. **Project agents.** Read the project `CLAUDE.md`, project skills and agent descriptions: the
   project's own architect, designer, implementers and entry skill (contract §6). Remember them for
   the briefs.
3. **Checkpoint** `~/.claude/dev-state/<repo-key>/blueprint-<project>[--<evo>].md` (repo-key recipe from
   the development workflow; no repo → the project folder name). Exists → read it whole and the last
   block of its `.trace.md`; never re-ask what DECISIONS.md holds. Missing → create it (§5).
4. **Online sync** when the checkpoint has a doc URL: run `online.md` §2 before anything else.

## 2. State and next step

Print one line per phase: `Producto v3 aprobado · Técnico v2 borrador (2 stale) · Diseño — · Backlog —`
plus the lint counts and open review findings. Then ask with `AskUserQuestion` — only the options that
make sense now, no default:

| Option | When | Runs |
|---|---|---|
| Define / complete product | always | `/blueprint-scope` |
| Technical design | PRODUCT approved | `/blueprint-tech` |
| UX/UI design (or record "no UI") | TECHNICAL approved | `/blueprint-design` |
| Backlog | TECHNICAL approved and DESIGN approved or skipped | `/blueprint-backlog` |
| Review everything | any doc exists | `/blueprint-review full` |
| Change something approved | any doc approved | `/blueprint-change` |
| Merge evolution into base | evolution, all docs approved | §4 |
| Publish / share online | any doc exists | `online.md` §1, §3 |

A phase can be re-entered to complete it: its skill resumes from the doc and its open questions,
never from scratch. Stale items (lint cascade) are offered first.

## 3. Every phase ends the same way

`phase skill → /blueprint-review <scope> (loop until clean) → gate block (transitions.md) → user
approves → blueprint_lint.py --approve <doc> → publish online + dashboard → checkpoint → back to §2`.
"Sí, pero…" is a change: one more round, not an approval.

## 4. Merge an evolution

Only on the user's explicit yes. Per base doc: status draft + version bump; fold new ids in, replace
`(changed)` items; changelog `- v<n> · <date> · <what> · merged: evolutions/<evo> · changed: <ids>`
(the guard asks before this write); lint the base; `/blueprint-review full` on the base; re-approve each
base doc; mark the evolution checkpoint `completed`.

## 5. Checkpoint

The development workflow's checkpoint rules (write on transitions, whole-file writes,
`checkpoint_revision += 1`, no secrets). Frontmatter:

```yaml
schema_version: 1
kind: blueprint
development_id: blueprint-<project>[--<evo>]
repo_key: <repo-key>
repo_root: <path or null>
docs_root: docs/blueprint/<project>[/evolutions/<evo>]
mode: new | evolution
title: <product or evolution name>
status: active | waiting_user | blocked | completed
task_class: BLUEPRINT
phase: scope | technical | design | backlog | review | change | online_sync | merge | completed
docs: "product v3 approved · technical v2 draft · design - · backlog -"
review_rounds: 0
project_agents: "architect: <name|none> · designer: <name|none> · entry: <skill>"
online_doc_url: null
online_published_versions: null
dashboard_url: null
canvas_url: null
checkpoint_revision: 1
last_updated: "<ISO-8601 with offset>"
```

Body: `## User Decisions` (pointer to DECISIONS.md, last 5 one-liners) · `## Transitions` · `## Next Action`
(one concrete step). Each transition block also goes to `<id>.trace.md`.
