---
name: blueprint-backlog
description: Build BACKLOG.md from the approved PRODUCT, TECHNICAL and DESIGN (or its skip) — epics, stories, tasks with t-shirt sizes, executor naming the project's own agents, dependencies, goal-based sprints, and for every agent-ready task a self-sufficient context pack, Ready when and Done when so a clean-session agent can run it with /dev-task. Use when the user invokes /blueprint-backlog, from the /blueprint hub, or on "haz el backlog", "divide el producto en tareas", "planifica los sprints".
---

# /blueprint-backlog

`<skills>` = the parent of this skill's directory. Read `<skills>/blueprint/reference/contract.md` (§5
is the task contract). Precondition: TECHNICAL approved and DESIGN approved or skipped (the guard
enforces it).

## Build

1. Sprint length (1 / 2 / 3 weeks) if BACKLOG.md does not have it. The project's workflow (entry skill,
   work item, target branch, commit style, DoD) from the hub's project-agents finding and the project
   `CLAUDE.md` — ask only what neither says.
2. Brief `delivery-manager` (`blueprint:delivery-manager`): root, template
   `<this skill's directory>/templates/BACKLOG.md`, contract, approved versions, sprint length, project
   workflow, executors available (project implementers and entry skill), lint command.
3. Send its draft to the technical owner (the project architect or `solution-architect`) for the
   agent-ready / missing-tasks / order check and the `Where:` and `Conventions:` lines of each pack;
   resume the manager with the findings. Scope or decision gaps → to the user as options.
4. `lint` must be 0 errors before review; errors go back to the manager (2 attempts).

## Tracker (optional, after approval)

Only if `~/.claude/dev-workflow.json` configures a tracker (`work_item.tool` `gh`, or
`work_item.mcp_server`) or `review_request.tool` is `gh` / `glab`. Show what would be created (counts
per level, first 5 titles) and ask. On an explicit yes: epics → stories → tasks, each task's
description = its context pack + Ready when + Done when (ASCII if `work_item.ascii_only`); write each
created id next to its `T-`/`US-` id through a `/blueprint-change` bump. Never edit or close existing
items.

Structure, as far as the tracker supports it:
- **Sprints → milestones** (title `S<n>`, description = the sprint goal); stories and tasks carry
  their sprint's milestone, epics none.
- **Hierarchy** epic → story → task as sub-issues (GitHub `POST …/issues/<n>/sub_issues`).
- **Dependencies** as "blocked by" links (GitHub `POST …/issues/<n>/dependencies/blocked_by`) and as
  `#<n>` in the body.
- **Labels**: `type:epic|story|task|spike`, `epic:EP-xx`, `size:S|M|L`, `agent-ready|human`.
- **GitHub Project** (needs the `project` token scope): one per product, linked to the repo, every
  item added; single-select fields Sprint, Type, Epic, Size, Executor, and Status = Todo; views
  *Backlog* (table), *Kanban* and *Current sprint* (boards). GraphQL in small batches (≤ 5
  `addProjectV2ItemById`, ≤ 20 field updates per request — bigger ones fail). The API cannot set a
  view's grouping: tell the user to group *Backlog* by Sprint in the UI.
- Create every issue first, then bodies, links and dependencies (they need the final numbers). Keep a
  state file so a rate-limited run resumes without duplicates.

## Close

Hub §3: `/blueprint-review backlog` → `DESIGNED → PLANNED` gate → approve → publish. Create
PROGRESS.md from `<skills>/blueprint/templates/PROGRESS.md` with every task `todo`.

## Handing a task to development

`/dev-task T-03.2.1` (or `/dev-task #<n>` once it is in the tracker): the brief to the development
architect is the task's context pack as written — the issue body when it comes from the tracker — not
the documents. The development closes on the task's `Done when` list and writes its PROGRESS.md
row (`TASK → DONE`); the hub republishes the dashboard.
