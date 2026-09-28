---
doc: design
project: <project>
mode: new
base: null
version: 1
status: draft            # draft | approved | skipped
skip_reason: null        # when skipped: why there is no UI work
approved_version: null
approved_hash: null
based_on_product_version: 1
based_on_technical_version: 1
canvas_url: null         # Claude Design artifact
design_system: null      # name + link, or "none"
---
# <Product name> — UX / UI design

## Changelog
- v1 · <YYYY-MM-DD> · first draft · changed: none

## 1. Principles
Platforms and breakpoints · density · tone of microcopy · accessibility target (from PRODUCT §6) ·
design system and what it settles. Evolution: existing screens and components kept.

## 2. Navigation
Map of areas and how each role reaches them (mermaid when it helps). Role visibility per TECHNICAL §6.

## 3. Flows
### FL-01 · <name> — F-01
Steps, with the screen of each (`S-`) and the happy / failure branches.

## 4. Screens
### S-01 · <name> — F-01 · roles: <roles>
**Purpose:** one line.
**Data:** E-Order.total … (every field exists in TECHNICAL §4)
**Actions:** … → AC-F01-1
**States:** empty · loading · error (I-01 down → …) · no permission · success
**Microcopy:** key labels and messages, in the product language.
**Artboard:** <name in the canvas>

## 5. Components
| ID | Component | Exists in repo / design system | Used by | Variants |
|---|---|---|---|---|
| C-<Name> | … | `path` or new | S-01 | … |

## 6. Accessibility and heuristics
| Check | Result | Screens |
|---|---|---|
WCAG 2.2 AA (contrast, focus, keyboard, labels, target size) · Nielsen heuristics (status, errors,
consistency, recognition, undo) — each ✔ or the fix.
