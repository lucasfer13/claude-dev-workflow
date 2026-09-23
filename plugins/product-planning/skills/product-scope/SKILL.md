---
name: product-scope
description: Define a product's scope with the user through rounds of questions until every feature has its story, acceptance criteria and priority — producing docs/product/<slug>/PRODUCT.md. Use when the user says "quiero definir un producto", "ayúdame con el alcance", "define the scope of…", "product discovery", "qué tiene que hacer cada funcionalidad", or invokes /product-scope. Resumes an existing PRODUCT.md. First step of the product flow; /product-plan comes next.
---

# Product scope

You (main thread) interview the user; the `product-analyst` agent (`product-planning:product-analyst`
when installed as a plugin) writes the document and prepares each round. The user decides
everything; nothing inferred goes into the document as fact.

## Start or resume

- Slug from the product name (`booking-app`); folder `docs/product/<slug>/` in the current directory
  (ask once if there is no obvious project root).
- **Exists** → read PRODUCT.md, summarise in 3 lines (version, status, open questions) and continue
  from its open questions. `status: approved` and the user wants changes → new version, back to draft.
- **New** → round 0 yourself, no agent: product name, the problem in one sentence, who uses it,
  existing system or greenfield. Then brief the analyst with those answers and the template path
  `<this skill's directory>/templates/PRODUCT.md`.

## Rounds

1. Relay the analyst's `QUESTIONS` with `AskUserQuestion` — options as given, nothing pre-selected,
   at most 4 per call. An answer that rejects the options' premise goes back as a reframe.
2. Resume the **same** analyst with the answers verbatim (keeps its context warm within a session;
   in a later session, start a fresh one — it reads PRODUCT.md).
3. After each round print one line: `Ronda <n> · PRODUCT.md v<n> · <features> funcionalidades · <open> abiertas`.
4. Stop when the analyst returns `READY_FOR_APPROVAL`, or when the user says enough — then the open
   ones stay in §8 marked `accepted-open` only if the user accepts each.

## Gate — SCOPE → DEFINED

Print the block (✔ only with evidence you saw in the file):

```
▶ SCOPE → DEFINED · <slug>
Done: PRODUCT.md v<n> — <n> features (<n> MVP), <n> roles, <n> entities
Criteria:
- ✔ every feature has a story, ≥1 Given/When/Then and a priority
- ✔ vision has a measurable outcome; scope lists what is out
- ✔ roles, NFRs, entities/integrations filled or "n/a: <reason>"
- ✔ no contradictions reported by the analyst
- ✔ open questions: none, or each accepted-open by the user
Review: docs/product/<slug>/PRODUCT.md
Next: /product-plan
```

Then **stop**: "¿Apruebas esta definición de producto?" Only an unambiguous yes sets `status:
approved` and `approved_version: <n>`. "Sí, pero…" is a change: one more round.
