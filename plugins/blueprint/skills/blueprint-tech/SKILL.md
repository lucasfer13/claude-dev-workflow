---
name: blueprint-tech
description: Turn an approved PRODUCT.md into TECHNICAL.md — decisions, architecture, data model with fields, integrations, permissions, NFR coverage, test strategy, threats, rollout, risks and spikes — routing to the project's own architect when it has one, else the stack architects, else the solution-architect. Use when the user invokes /blueprint-tech, from the /blueprint hub, or on "diseño técnico", "technical design for the product", "arquitectura de este evolutivo".
---

# /blueprint-tech

`<skills>` = the parent of this skill's directory. Read `<skills>/blueprint/reference/contract.md`.
Precondition: PRODUCT.md approved (the guard enforces it). You relay every question, pass answers
verbatim, record them in DECISIONS.md and hold the gate.

## Owner (contract §6)

1. The project's own architect (found by the hub) → brief it with the template
   `<this skill's directory>/templates/TECHNICAL.md`, the output path and the contract. If its own
   contract only writes its own plan format, `solution-architect` writes TECHNICAL.md with that
   architect's findings as its source for the code.
2. Else the stack architects the code shows (backend, frontend, mobile), in parallel for their parts;
   you merge one TECHNICAL.md through `solution-architect`.
3. Else `solution-architect`.

## Loop

1. Pass 1: brief with root, template, contract, repo paths, base root in an evolution, and the
   decisions already in DECISIONS.md. Stale items first when resuming.
2. Relay its questions (≤4 per call, options as given, nothing pre-selected); record `Q-xx`; resume the
   same agent. `UPSTREAM` for PRODUCT → ask the user; accepted → `/blueprint-change` on PRODUCT.
3. Pass 2 writes TECHNICAL.md. Check `lint` yourself; errors go back to the owner (2 attempts).

## Close

Hub §3: `/blueprint-review technical` → `SCOPED → ENGINEERED` gate → approve → publish.
