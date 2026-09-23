---
doc: technical
product: <slug>
version: 1
status: draft            # draft | approved
approved_version: null
based_on_product_version: 1
---
# <Product name> — technical design

## Changelog
- v1 · <YYYY-MM-DD> · first draft

## 1. Context
Greenfield, or existing repo(s): what exists and is kept (`file:line` for anything cited).

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
### E-<Name>
| Field | Type | Req. | Constraints | Notes |
|---|---|---|---|---|
Relations: … (cardinality) · Keys / indexes: … · Lifecycle: …
Cross-cutting (ids, audit, soft delete, tenancy) per D-xx. Fields marked *revisable* are settled at implementation.

## 5. Integrations and contracts
| ID | System | Operation | Contract outline | Failure behaviour |
|---|---|---|---|---|

## 6. Roles → permissions
| Role (PRODUCT §2) | Technical permission / enforcement |
|---|---|

## 7. Non-functional coverage
| NFR (PRODUCT §6) | How it is met | Verified by |
|---|---|---|

## 8. Risks and spikes
| ID | Risk / unknown | Spike (becomes a backlog task) |
|---|---|---|
