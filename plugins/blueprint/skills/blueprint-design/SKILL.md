---
name: blueprint-design
description: UX/UI design phase of a blueprint — a UX/UI expert asks the user about flows, navigation, screens, states and the design system, contrasting every choice with PRODUCT.md and TECHNICAL.md, writes DESIGN.md, and the main thread paints each screen in a Claude Design canvas the user reviews. Use when the user invokes /blueprint-design, from the /blueprint hub, or on "haz el diseño", "diseña las pantallas", "UX/UI for the product", "diseño con Claude Design". Also records "no UI work" as an explicit skip.
---

# /blueprint-design

`<skills>` = the parent of this skill's directory. Read `<skills>/blueprint/reference/contract.md`.
Precondition: TECHNICAL.md approved (the guard enforces it).

## No UI?

Ask first when it is not obvious. The user confirms there is no UI work → create DESIGN.md from the
template with `status: skipped` and their `skip_reason`; `ENGINEERED → DESIGNED` block with the
reason; back to the hub. Never skip on your own. A skipped DESIGN.md keeps only the frontmatter and
one line with the reason.

## Owner

The project's own designer if the hub found one, else `ux-designer` (`blueprint:ux-designer`). Brief:
root, template `<this skill's directory>/templates/DESIGN.md`, contract, repo paths (screens,
components, tokens), base root in an evolution, and the design-system candidates: list the user's
design systems with the Artifact tool (`action: "list"`, type Design System) and give their names; the
user chooses in pass 1.

## Loop

1. Pass 1 questions → `AskUserQuestion` (≤4, options as given, nothing pre-selected) → DECISIONS.md →
   resume the same agent. `UPSTREAM` for TECHNICAL (a field, a permission) → to the user; accepted →
   `/blueprint-change` on TECHNICAL before going on.
2. Pass 2 writes DESIGN.md and returns `ARTBOARDS:`.
3. **Canvas** (main thread — agents have no Artifact tool): `Artifact action: "quickstart"`, intent
   `design`, then create from the Design type with title `<project> · UX`, the chosen design system
   (or none), and fill one artboard per `ARTBOARDS:` entry following the type's own instructions.
   Record `canvas_url` in DESIGN.md frontmatter and the checkpoint. The design-system tool failing to
   connect → tell the user (`/design-login`) and continue with DESIGN.md only.
4. The user reviews the canvas; their feedback (and canvas comments) → resume the agent → update
   DESIGN.md and repaint only the changed artboards. Repeat until the user is happy.

## Close

Hub §3: `/blueprint-review design` → `ENGINEERED → DESIGNED` gate → approve → publish.
