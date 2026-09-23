---
doc: backlog
product: <slug>
version: 1
status: draft            # draft | approved
approved_version: null
based_on_product_version: 1
based_on_technical_version: 1
sprint_length: <n> weeks
---
# <Product name> — backlog

## Changelog
- v1 · <YYYY-MM-DD> · first draft

## Sizing
S ≈ under a day · M ≈ 1-3 days · L ≈ up to a week · XL = must be split. Sprints are goal-based (no
capacity figure), so dates are indicative.

## Sprints
| Sprint | Goal | Items | Depends on |
|---|---|---|---|
| S1 | … | US-01.1, T-00.1 | — |

## Epics

### EP-01 · <name> — covers F-01, F-02
#### US-01.1 · <story title> · M · MVP
As a <role>, I want …, so that ….
Acceptance: Given … when … then … (from PRODUCT F-01, refined)
| Task | Size | Executor | Repo / area | Entities | Decisions | Depends on | Acceptance |
|---|---|---|---|---|---|---|---|
| T-01.1.1 · … | S | agent-ready | orders-api | E-Order | D-02 | — | … |
| T-01.1.2 · … | M | human | design | — | — | T-01.1.1 | … |

Spikes from TECHNICAL §8 appear as `T-00.x` tasks.

## Out of this backlog
PRODUCT features not planned yet (later phases) and why.
