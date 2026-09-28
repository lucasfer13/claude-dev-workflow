---
doc: product
project: shop
mode: new
base: null
version: 2
status: draft
approved_version: null
approved_hash: null
---
# Shop — product definition

## Changelog
- v1 · 2026-09-01 · first draft · changed: none
- v2 · 2026-09-02 · discount rule · changed: F-01

## 1. Vision
Customers order online; success = 30% orders online in 3 months.

## 2. Users and roles
| Role | Who | Can | Cannot |
|---|---|---|---|
| Customer | buyer | order | see others' orders |

## 3. Scope
**In:** ordering. **Out (explicitly):** returns.

## 4. MVP and phases
| Feature | Priority (MoSCoW) | Phase |
|---|---|---|
| F-01 | Must | MVP |

## 5. Features
### F-01 · Place order
**Story:** As a Customer, I want to order, so that I get products.
**Acceptance criteria:**
- AC-F01-1 · Given a cart, when I confirm, then an order is created.
- AC-F01-2 · Given another customer's order, when I open it, then I get 403.
**Entities:** E-Order

## 6. Non-functional requirements
| NFR | Requirement | Measure |
|---|---|---|
| Performance | confirm fast | p95 < 300 ms |

## 7. Business entities and integrations
| Entity | Meaning | Owned by / source |
|---|---|---|
| E-Order | an order | shop |

## 8. Glossary
| Term | Meaning | Not to confuse with |
|---|---|---|
| G-cart | items before ordering | order |
