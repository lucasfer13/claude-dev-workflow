---
doc: technical
project: shop
mode: new
base: null
version: 1
status: draft
approved_version: null
approved_hash: null
based_on_product_version: 2
---
# Shop — technical design

## Changelog
- v1 · 2026-09-03 · first draft · changed: none

## 2. Decisions
| ID | Decision | Chosen (by the user) | Discarded | Why it matters |
|---|---|---|---|---|
| D-01 | Persistence | PostgreSQL | SQLite | concurrency |

## 4. Data model
### E-Order
| Field | Type | Req. | Constraints | Notes |
|---|---|---|---|---|
| id | uuid | yes | pk | |
| total | decimal | yes | >= 0 | |

## 5. Integrations and contracts
| ID | System | Operation | Contract outline | Failure behaviour |
|---|---|---|---|---|
| I-01 | Payments | charge | POST /charge | retry 3x then fail order |

## 8. Test strategy
| Level | What it covers | Tooling | AC ids verified here |
|---|---|---|---|
| integration | API | xunit | AC-F01-1, AC-F01-2 |

## 10. Risks and spikes
| ID | Risk / unknown | Spike (becomes task T-00.n) | Result |
|---|---|---|---|
| SP-01 | payment sandbox | try sandbox | pending |
