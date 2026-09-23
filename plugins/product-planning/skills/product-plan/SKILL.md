---
name: product-plan
description: Turn an approved PRODUCT.md into a technical design (TECHNICAL.md — decisions, architecture, data model with entities and fields, integrations, permissions, NFR coverage, risks) and then an agile backlog (BACKLOG.md — epics, stories, tasks with t-shirt sizes, agent-ready/human executor, dependencies, goal-based sprints), each behind its own approval gate. Use after /product-scope, or when the user says "divide el producto en tareas", "planifica los sprints", "haz el backlog", "technical design for the product", or invokes /product-plan.
---

# Product plan

Agents (prefix `product-planning:` when installed as a plugin): `solution-architect`, then
`delivery-manager`. You (main thread) relay every question with `AskUserQuestion`, pass answers
verbatim, check the evidence and hold the gates. Templates: `<this skill's directory>/templates/`.

## Preconditions

`docs/product/<slug>/PRODUCT.md` has `status: approved`. If not → run /product-scope first.
If TECHNICAL.md or BACKLOG.md exist, resume: compare their `based_on_*_version` with the current
approved versions. Behind → replan **only what the changelog lines touch** (by ids), never from scratch.

## Phase A — technical design

1. Brief `solution-architect` pass 1: slug, paths, repo paths if any.
2. Relay its questions (≤4 per call, options as given, nothing pre-selected); resume it with the answers.
   Loop until it has what it needs, then pass 2 writes TECHNICAL.md.
3. Gate — DEFINED → DESIGNED:

```
▶ DEFINED → DESIGNED · <slug>
Done: TECHNICAL.md v<n> — <n> decisions, <n> entities, <n> integrations, <n> spikes
Criteria:
- ✔ every D-xx has the user's choice recorded; none taken by the agent
- ✔ every PRODUCT entity has fields, keys and relations; ER diagram present
- ✔ every integration has a contract outline and failure behaviour
- ✔ every role mapped to permissions; every NFR has how + how verified
- ✔ existing code cited file:line (or greenfield stated)
Review: docs/product/<slug>/TECHNICAL.md
Next: backlog
```

   Stop: "¿Apruebas el diseño técnico?" Unambiguous yes → `status: approved`, `approved_version`.

## Phase B — backlog

1. Ask the sprint length (1 / 2 / 3 weeks) if BACKLOG.md does not have it.
2. Brief `delivery-manager` with the approved versions and sprint length.
3. Send its draft split to `solution-architect` for the agent-ready / missing-tasks / order check;
   resume the manager with the findings. Gaps in scope or decisions → to the user as options.
4. Gate — DESIGNED → PLANNED:

```
▶ DESIGNED → PLANNED · <slug>
Done: BACKLOG.md v<n> — <n> epics, <n> stories, <n> tasks (<n> agent-ready), <n> sprints
Criteria:
- ✔ every MVP feature covered by ≥1 story (list any uncovered: none)
- ✔ no XL left; every task sized and with an executor
- ✔ every agent-ready task has acceptance criteria and one repo/area
- ✔ dependencies acyclic; sprints respect them; spikes before what they unblock
- ✔ tasks cite their E-/D- ids; nothing contradicts TECHNICAL.md
Review: docs/product/<slug>/BACKLOG.md
Next: create in tracker (optional) · /dev-task T-xx for agent-ready tasks
```

   Stop: "¿Apruebas el backlog?" Unambiguous yes → `status: approved`.

## After approval — tracker (optional)

Only if `~/.claude/dev-workflow.json` configures a tracker (`work_item.mcp_server`) or
`review_request.tool` is `gh` / `glab`. Show what would be created (counts per level, first 5 titles)
and ask. Only on an explicit yes: create epics → stories → tasks (`gh issue create`, `glab issue
create` or the MCP), ASCII if `work_item.ascii_only`, and write each created id next to its `T-`/`US-`
id in BACKLOG.md. Never edit or close existing tracker items. No config → skip this step silently.

## Handing a task to development

`/dev-task T-03.2.1`: the brief to the development architect is the task row plus the story's
acceptance criteria and the cited `E-`/`D-` sections — not the whole documents.
