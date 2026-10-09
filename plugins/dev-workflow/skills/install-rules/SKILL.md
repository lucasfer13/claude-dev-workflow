---
name: install-rules
description: Install or update the dev-workflow global rules into ~/.claude — the rules block in CLAUDE.md, the reference docs and scripts under ~/.claude/dev-workflow/, and a starter ~/.claude/dev-workflow.json. Use after installing or updating the dev-workflow plugin, or when the user says "install the workflow rules", "update the rules", "instala las reglas".
---

# Install the dev-workflow rules

A plugin cannot ship a `CLAUDE.md`, so this skill copies the rules into place. It is idempotent: the
block between `<!-- dev-workflow:start -->` and `<!-- dev-workflow:end -->` is replaced; nothing
else in `CLAUDE.md` is touched, and a timestamped backup is written first.

1. Dry run and show the user what will change:
   `python "<this skill's directory>/install.py" --dry-run`
2. If `~/.claude/CLAUDE.md` already holds a *different* workflow (its own gates, TDD or agent rules
   outside the dev-workflow markers), point it out — two rule sets will conflict. Ask how to proceed.
3. On the user's OK: `python "<this skill's directory>/install.py"`.
4. If `~/.claude/dev-workflow.json` was just created, walk the user through it:
   - `work_item.prefix` — ticket id prefix (`PROJ` → `PROJ-123`); `null` for none.
   - `work_item.required` — must every development have a work item?
   - `work_item.tool` — `gh` for GitHub Issues (then `prefix` is `#`), `mcp` for an MCP tracker, or `null`.
   - `work_item.mcp_server` — MCP server of the issue tracker, or `null`; `ascii_only` if it rejects non-ASCII.
   - `review_request.tool` — `gh`, `glab` or `mcp` (+ `mcp_server`); `title_format`, `sections`.
   - `versioning` — `semver` or `revision` (4-part, REVISION moves into the dev branch).
   - `forbidden_models` — models the guard refuses for subagents.
5. Tell the user the rules load in the **next** session.
