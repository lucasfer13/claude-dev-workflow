---
doc: product
project: <project>
mode: new                # new | evolution
base: null               # evolution: ../..
version: 1
status: draft            # draft | approved
approved_version: null
approved_hash: null
---
# <Product name> — product definition

## Changelog
- v1 · <YYYY-MM-DD> · first draft · changed: none

## 1. Vision
Problem, who has it, what success looks like: 1 measurable outcome and how it is measured. 3-5 lines.
Evolution: the change and why now; the base features it touches.

## 2. Users and roles
| Role | Who | Can | Cannot |
|---|---|---|---|

## 3. Scope
**In:** …
**Out (explicitly):** …
**Assumptions:** …

## 4. MVP and phases
| Feature | Priority (MoSCoW) | Phase |
|---|---|---|
| F-01 | Must | MVP |

## 5. Features
### F-01 · <name>
**Story:** As a <role>, I want <capability>, so that <benefit>.
**Acceptance criteria:**
- AC-F01-1 · Given <state>, when <action>, then <observable outcome>.
- AC-F01-2 · Given <a role without permission>, when …, then <refused, how>.
**Rules / edge cases:** empty · limits · concurrency · external system down · personal data.
**Entities:** E-Order, …

## 6. Non-functional requirements
| NFR | Requirement | Measure |
|---|---|---|
Performance · security · personal data · availability · platforms / devices · languages · accessibility —
each measurable, or "n/a: <reason>".

## 7. Business entities and integrations
| Entity | Meaning | Owned by / source |
|---|---|---|
| E-Order | … | … |

| External system | What we exchange | Direction |
|---|---|---|
No fields here — fields live in TECHNICAL.md.

## 8. Glossary
| Term | Meaning | Not to confuse with |
|---|---|---|
| G-<term> | … | … |

## 9. Open questions
- Q-01 · <question> · blocks: F-xx · status: open | accepted-open
