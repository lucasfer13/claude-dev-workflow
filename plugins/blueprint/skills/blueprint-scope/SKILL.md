---
name: blueprint-scope
description: Define a product's scope — or the product delta of an evolution in an existing project — with the user through rounds of questions until every feature has its story, acceptance criteria with ids and priority, producing PRODUCT.md. Use when the user invokes /blueprint-scope, or from the /blueprint hub; also on "ayúdame con el alcance", "qué tiene que hacer cada funcionalidad", "define the scope of…", "product discovery". Resumes an existing PRODUCT.md.
---

# /blueprint-scope

`<skills>` = the parent of this skill's directory. Read `<skills>/blueprint/reference/contract.md`.
Agent: `product-analyst` (`blueprint:product-analyst` as a plugin). You interview; it writes. The user
decides everything; nothing inferred goes in as fact. No hub context yet (mode, project, checkpoint)
→ run `/blueprint` §1 first.

## Start or resume

- **Exists** → summarise in 3 lines (version, status, open questions) and continue from its open
  questions and stale items. Approved and the user wants changes → `/blueprint-change`.
- **New** → round 0 yourself: product (or change) name, the problem in one sentence, who uses it.
  Create DECISIONS.md from `<skills>/blueprint/templates/DECISIONS.md` if missing. Brief the analyst:
  answers, root, template `<this skill's directory>/templates/PRODUCT.md`, contract path, base root in
  an evolution.

## Rounds

1. Relay the analyst's `QUESTIONS` with `AskUserQuestion` — options as given, nothing pre-selected, at
   most 4 per call. An answer that rejects the premise goes back as a reframe.
2. Record each answer in DECISIONS.md (`Q-xx`), then resume the **same** analyst with the answers
   verbatim (in a later session start a fresh one — it reads the files).
3. After each round: `Ronda <n> · PRODUCT.md v<n> · <features> funcionalidades · <open> abiertas`.
4. Stop when the analyst returns `READY_FOR_APPROVAL`, or the user says enough — open ones stay in §9
   `accepted-open` only if the user accepts each.

## Close

Back to the hub's §3: `/blueprint-review product` → `START → SCOPED` gate → approve → publish.
