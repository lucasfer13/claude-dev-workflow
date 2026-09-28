---
name: blueprint-review
description: Consistency review loop for a blueprint — deterministic lint first, then a fresh independent reviewer that cross-checks the phase against every earlier document (PRODUCT, TECHNICAL, DESIGN, BACKLOG, an evolution against its base and the code), routing fixes to each document's owner and decisions to the user, round after round until no BLOCKER or MAJOR remains. Use when the user invokes /blueprint-review, at the end of every blueprint phase, or on "revisa el blueprint", "busca incongruencias en el backlog", "check the plan is consistent".
---

# /blueprint-review [product | technical | design | backlog | full]

`<skills>` = the parent of this skill's directory. Contract: `<skills>/blueprint/reference/contract.md`.
Scope defaults to the phase just closed; `full` before any gate that follows a change to an earlier
doc, and always before the backlog gate.

## Round

1. **Lint**: `python <skills>/blueprint/scripts/blueprint_lint.py <root>`. Errors in a doc → its owner
   fixes them first (no reviewer round is spent on structure). STALE items → the owner revisits them.
2. **Changed ids** since the last round: the `changed:` ids of changelog lines newer than REVIEW.md's
   last round. Empty or `full` → everything.
3. **Reviewer**: a **fresh** `blueprint-reviewer` every round (`blueprint:blueprint-reviewer`) — never
   resumed. Brief: root, scope, changed ids, lint output, contract path, base root, repo paths. Create
   REVIEW.md from `<this skill's directory>/templates/REVIEW.md` if missing.
4. **Route**:
   - `fix` → the owner agent of that doc, with the finding verbatim. An approved doc → status draft
     + version bump first (the guard enforces it); it goes back to its gate at the end.
   - `decision` → the user with `AskUserQuestion` (options as given); record `Q-xx`; the owner applies it.
   - MINOR → fixed with the rest, or the user accepts it (`accepted`).
5. Print `Revisión ronda <n> · lint <e>/<w>/<s> · BLOCKER <n> · MAJOR <n> · MINOR <n> · corregidos <n>`.

Repeat until the reviewer returns `CLEAN` and lint has 0 errors, 0 stale. **Every 3 rounds without
reaching CLEAN**, stop and ask the user: continue, accept the remaining ones as they are (MAJOR only
with a reason written in REVIEW.md), or change something upstream.

Then print the `any → REVIEWED` block and return to the calling skill's gate.
