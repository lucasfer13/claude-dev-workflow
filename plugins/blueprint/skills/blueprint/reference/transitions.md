# Blueprint transitions

Same block format and rules as the development workflow's transitions (`Done · Criteria · Review · Next`,
✔ only with evidence seen in the session, ✘ blocks, "n/a" needs a reason), printed in the user's
language. **Every human gate runs `/blueprint-review` for its phase first**; the gate block quotes the
review's last round. Lint = `blueprint_lint.py <root>` output, quoted as counts.

## START → SCOPED · PRODUCT.md · human gate
- ✔ lint: 0 errors in PRODUCT scope
- ✔ every feature: story, ≥1 `AC-`, priority + phase; negative AC where permissions / personal data / integration
- ✔ vision has a measurable outcome; scope lists what is out; glossary has the domain terms
- ✔ roles, NFRs (measurable), entities / integrations filled or "n/a: <reason>"
- ✔ review clean: 0 BLOCKER / MAJOR (round n)
- ✔ open questions: none, or each `accepted-open` by the user
Summary: v, features (MVP), roles, entities.

## SCOPED → ENGINEERED · TECHNICAL.md · human gate
- ✔ every `D-` has the user's choice (DECISIONS.md `Q-` cited); none taken by an agent
- ✔ every PRODUCT entity has fields, keys, relations; ER present
- ✔ every `I-` has contract outline + failure behaviour; roles → permissions complete
- ✔ every NFR: how + verified by; test strategy covers every MVP `AC-`; threats filled or n/a with reason
- ✔ evolution: as-is cited `file:line`, rollout filled; technical owner named
- ✔ review clean (PRODUCT ↔ TECHNICAL cross-check)
Summary: v, decisions, entities, integrations, spikes.

## ENGINEERED → DESIGNED · DESIGN.md or skipped · human gate
- ✔ skipped → `skip_reason` the user confirmed; else:
- ✔ every MVP feature has ≥1 screen; every screen has states, roles, data
- ✔ every `E-x.field` on a screen exists in TECHNICAL; role visibility = TECHNICAL §6
- ✔ WCAG 2.2 AA + heuristics table filled; design system named or "none" (user's choice)
- ✔ canvas published, URL in `canvas_url`, user reviewed it
- ✔ review clean (PRODUCT ↔ TECHNICAL ↔ DESIGN)
Summary: v, flows, screens, components (new / existing).

## DESIGNED → PLANNED · BACKLOG.md · human gate
- ✔ lint 0 errors: coverage F → US, AC → task, SP → T-00, no XL, deps acyclic, packs complete
- ✔ every agent-ready task: context pack ≤ budget, Ready when, Done when with each covered `AC-` → test
- ✔ executors name the project's own agents / entry skill where they exist
- ✔ sprints respect dependencies; spikes before what they unblock; success-measure instrumentation planned
- ✔ review clean (full cross-check, including packs)
Summary: v, epics, stories, tasks (agent-ready), sprints.

## any → REVIEWED · /blueprint-review
- ✔ lint run this round, counts quoted
- ✔ reviewer was a fresh instance; scope = changed ids + neighbours (full before a gate)
- ✔ every `fix` routed to its owner and re-reviewed; every `decision` answered by the user
- ✔ 0 BLOCKER / MAJOR open; MINOR fixed or accepted
- ⚠ every 3 rounds without convergence: user asked whether to continue
Summary: rounds, findings by severity, what changed.

## ONLINE → SYNCED · team edits and comments
- ✔ diff taken against the last published snapshot, per tab
- ✔ every edit / comment is a `P-` with source; none applied without the user
- ✔ accepted ones went through the owner + review; docs bumped; republished
- ✔ every thread answered (applied in vN / rejected: reason)
Summary: proposals in / accepted / rejected, new versions.

## CHANGE → REAPPROVED · /blueprint-change
- ✔ `CR-` with impact by ids; lint cascade lists the stale items
- ✔ only affected docs bumped; only stale items revisited
- ✔ review clean; each affected doc re-approved at its gate
Summary: CR, docs and versions touched, items revisited.

## EVOLUTION → MERGED · base updated
- ✔ evolution docs all approved; user approved the merge
- ✔ base docs bumped with `merged: evolutions/<evo>` changelog lines; `(changed)` items replaced, new ids added
- ✔ lint of the base: 0 errors
Summary: ids added / changed in the base, new base versions.

## TASK → DONE · from the development workflow
- ✔ every `Done when` line has its evidence (test names, totals, artifact left)
- ✔ PROGRESS.md row `done` with review request link and date
Summary: task, done-when n/n, link.
