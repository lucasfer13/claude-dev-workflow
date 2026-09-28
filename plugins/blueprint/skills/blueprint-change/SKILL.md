---
name: blueprint-change
description: Change request on an approved blueprint document — impact analysis by ids, cascade of stale items to the downstream documents, only the affected items revisited, review, and re-approval of only what changed. Use when the user invokes /blueprint-change, from the /blueprint hub, when an accepted online proposal or a review fix touches an approved doc, or on "cambia esta funcionalidad aprobada", "hay que modificar el diseño técnico", "change request".
---

# /blueprint-change

`<skills>` = the parent of this skill's directory. Contract: `<skills>/blueprint/reference/contract.md`.

1. **Record** `CR-xx` in CHANGES.md (template `<skills>/blueprint/templates/CHANGES.md`): source (user,
   `P-`, `RV-`), the request in one line.
2. **Impact**: the ids the change touches in its doc; then what cites them downstream (lint
   `--json` → `items[*].cites`). Show `CR-xx · <doc> · <ids> → stale: <downstream ids>` and ask the user
   to approve the CR. Rejected → `rejected` with the reason; stop.
3. **Apply upstream first**: the owner agent of the first affected doc sets status draft, bumps the
   version, changes only those ids, changelog `changed: <ids>`.
4. **Cascade**: lint lists stale items per downstream doc; each owner revisits only those, updates
   `based_on_*_version`, bumps its own version.
5. `/blueprint-review` with scope = the most downstream doc touched (changed ids only).
6. Re-approve each touched doc at its gate (`CHANGE → REAPPROVED`), `--approve`, publish, checkpoint.
   CHANGES.md row → `applied v<n>`.

Never a full replan for a local change; a change that reopens many decisions → tell the user and
offer re-entering the phase instead.
