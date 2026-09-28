---
doc: technical
project: <project>
mode: new
base: null
version: 1
status: draft
approved_version: null
approved_hash: null
based_on_product_version: 1
---
# <Product name> — technical design

## Changelog
- v1 · <YYYY-MM-DD> · first draft · changed: none

## 1. Context
Greenfield, or existing repo(s): what exists and is kept (`file:line` for anything cited).
Evolution: as-is of the affected area only. Technical owner: <agent> (contract §6).

## 2. Decisions
| ID | Decision | Chosen (by the user) | Discarded | Why it matters |
|---|---|---|---|---|
| D-01 | … | … | … | … |
Following existing convention (not asked): …

## 3. Architecture
Components / services, responsibility of each, how they talk. Mermaid diagram when it helps.

## 4. Data model
```mermaid
erDiagram
```
### E-Order
| Field | Type | Req. | Constraints | Notes |
|---|---|---|---|---|
| id | … | yes | pk | |
| total | … | yes | … | |
Relations: … (cardinality) · Keys / indexes: … · Lifecycle: …
Cross-cutting (ids, audit, soft delete, tenancy, time zones) per D-xx. *revisable* fields settle at implementation.

## 5. Integrations and contracts
| ID | System | Operation | Contract outline | Failure behaviour |
|---|---|---|---|---|
| I-01 | … | … | … | … |

## 6. Roles → permissions
| Role (PRODUCT §2) | Technical permission / enforcement |
|---|---|

## 7. Non-functional coverage
| NFR (PRODUCT §6) | How it is met | Verified by |
|---|---|---|

## 8. Test strategy
| Level | What it covers | Tooling | AC ids verified here |
|---|---|---|---|
| unit / integration / e2e | … | … | AC-F01-1, AC-F01-2 |

## 9. Threats (light)
| Asset (data / endpoint) | Threat | Mitigation | Verified by |
|---|---|---|---|
Personal data, auth, secrets, external input. "n/a: <reason>" only when none apply.

## 10. Risks and spikes
| ID | Risk / unknown | Spike (becomes task T-00.n) | Result |
|---|---|---|---|
| SP-01 | … | … | pending |

## 11. Rollout (evolutions and anything live)
Order across repos · migrations and backfills · feature flags · compatibility window · rollback ·
how the success measure (PRODUCT §1) is instrumented.
