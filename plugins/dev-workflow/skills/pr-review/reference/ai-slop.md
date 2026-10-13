# AI slop — review checklist

Code that compiles and passes tests but the change does not need. Flag only what the diff introduces;
grep the repo before claiming something is duplicated or unused. One finding per kind, listing anchors.
IMPORTANT when it adds public surface, a contract or a new layer; IMPROVEMENT otherwise.

## Invented structure
- New service/manager/handler/helper layer between two pieces that already talked directly, with no
  second caller and no behaviour of its own — pure pass-through.
- Interface with a single implementation and no test double, plugin point or architecture rule that
  requires it (check the closest analogue in the repo: if siblings have no interface, neither should this).
- Factory, builder, strategy or generic base class for exactly one concrete case.
- New DTO/model that copies an existing one field by field, plus a mapper between them.
- New project/module/folder for a handful of files that fit an existing one.
- Configuration option, feature flag or parameter that no caller sets to a non-default value.
- Overloads or optional parameters "for flexibility" with no caller.

## Duplication
- Helper/extension/util that already exists in the repo or the framework (string, date, collection,
  HTTP, retry, mapping) — grep the name and the behaviour.
- Copy-pasted block from a sibling file instead of calling or extracting it.
- Re-implemented validation the framework or an existing validator already performs.

## Defensive noise
- `try/catch` that catches everything and logs/rethrows/returns default with no recovery decision.
- Null/empty checks on values the type system, the caller or the framework already guarantee.
- Fallback branch for a case that cannot occur here (enum already exhaustive, value already validated).
- Retry/timeout/circuit wrapper added at one call site while the rest of the repo uses a shared policy.
- Swallowed errors: `catch {}`, `.catch(() => {})`, `runCatching {}` result ignored.

## Text noise
- Comments that restate the code, narrate history ("changed X to Y"), cite tickets or plans.
- Doc blocks longer than the member they document; `<remarks>`/JSDoc on obvious private members.
- Log lines at every step ("Entering method", "Successfully did X") — noise and cost.
- Commented-out code, TODOs without owner, leftover debug output.

## Tests that prove nothing
- Assertion only on a stub/mock the test itself configured.
- Tests for mappings, getters, field copies, DI registration or framework behaviour.
- One test per field where a parameterised test fits; the same shared code tested again per caller.
- Snapshot of a huge object instead of asserting the behaviour that matters.
- Test names promising a scenario the body does not exercise.

## Scope creep
- Files or refactors unrelated to the MR's stated goal (renames, reformatting, moved files mixed with
  behaviour changes).
- Version bumps, package additions or config edits the change does not use.
