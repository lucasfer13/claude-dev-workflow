---
doc: backlog
project: shop
mode: new
base: null
version: 1
status: draft
approved_version: null
approved_hash: null
based_on_product_version: 2
based_on_technical_version: 1
based_on_design_version: 1
sprint_length: 2 weeks
---
# Shop — backlog

## Changelog
- v1 · 2026-09-05 · first draft · changed: none

## Epics
### EP-00 · Foundations
##### T-00.1 · Payment sandbox spike
| Size | Executor | Agent / entry | Repo / area | Depends on |
|---|---|---|---|---|
| S | human | — | — | — |
Covers: SP-01
**Done when**
- Result written to TECHNICAL §10

### EP-01 · Ordering — covers F-01
#### US-01.1 · Place order · M · MVP
Covers: F-01 · AC-F01-1, AC-F01-2 · S-01

##### T-01.1.1 · Create order endpoint
| Size | Executor | Agent / entry | Repo / area | Depends on |
|---|---|---|---|---|
| M | agent-ready | dotnet-implementer via /dev-task | api/orders | T-00.1 |
Covers: US-01.1 · AC-F01-1, AC-F01-2 · E-Order · D-01
**Context pack**
- Goal: POST /orders creates an order.
- Facts: E-Order id uuid, total decimal >= 0; D-01 PostgreSQL.
- Where: `src/Orders/OrdersController.cs:12`
- From dependencies: sandbox keys from T-00.1.
- Conventions: /dev-task, branch main.
- Out of scope: discounts.
**Ready when**
- [ ] T-00.1 done
**Done when**
- AC-F01-1 → test `Create_order_AC_F01_1` passes
- AC-F01-2 → test `Foreign_order_403_AC_F01_2` passes
- `dotnet test` green
