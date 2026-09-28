---
doc: backlog
project: <project>
mode: new
base: null
version: 1
status: draft            # draft | approved
approved_version: null
approved_hash: null
based_on_product_version: 1
based_on_technical_version: 1
based_on_design_version: 1   # null when design skipped
sprint_length: <n> weeks
---
# <Product name> — backlog

## Changelog
- v1 · <YYYY-MM-DD> · first draft · changed: none

## Sizing
S ≈ under a day · M ≈ 1-3 days · L ≈ up to a week · XL = must be split. Sprints are goal-based (no
capacity figure), so dates are indicative.

## Project workflow
Entry skill · work item needed · target branch · commit style · Definition of Done — from the project's
own workflow, cited in every task's `Done when`.

## Sprints
| Sprint | Goal | Items | Depends on |
|---|---|---|---|
| S1 | … | US-01.1, T-00.1 | — |

## Epics

### EP-00 · Foundations and spikes
##### T-00.1 · <spike from SP-01, or setup>
| Size | Executor | Agent / entry | Repo / area | Depends on |
|---|---|---|---|---|
| S | human | — | — | — |
Covers: SP-01
- Goal: …
**Done when**
- Result written back to TECHNICAL §10

### EP-01 · <name> — covers F-01
#### US-01.1 · <story title> · M · MVP
As a <role>, I want …, so that ….
Covers: F-01 · AC-F01-1, AC-F01-2 · S-01

##### T-01.1.1 · <imperative title>
| Size | Executor | Agent / entry | Repo / area | Depends on |
|---|---|---|---|---|
| M | agent-ready | <implementer> via /dev-task | <repo/area> | T-00.1 |
Covers: US-01.1 · AC-F01-1, AC-F01-2 · E-Order · D-01 · S-01
**Context pack**
- Goal: …
- Facts: …
- Where: …
- From dependencies: …
- Conventions: …
- Out of scope: …
**Ready when**
- [ ] dependencies done · [ ] spikes resolved · [ ] no open Q- / stale id cited
**Done when**
- AC-F01-1 → test `…` passes
- AC-F01-2 → test `…` passes
- `<command>` green, totals reported
- Leaves: …
- Project DoD: …

## Out of this backlog
PRODUCT features not planned yet (later phases) and why.
