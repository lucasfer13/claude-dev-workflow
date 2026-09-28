# Blueprint contract

Shared by every blueprint skill and agent. The brief gives this file's path; read it before working.
The main thread orchestrates and is the only one who talks to the user.

## 1. Layout

| Mode | Root |
|---|---|
| new product | `docs/blueprint/<project>/` |
| evolution of an existing project | `docs/blueprint/<project>/evolutions/<evo>/` — base = the project root above, if it exists |

| File | Owner | Holds |
|---|---|---|
| `PRODUCT.md` | product-analyst | vision, roles, scope, MVP, features + acceptance, NFRs, entities, glossary |
| `TECHNICAL.md` | technical owner (§6) | decisions, architecture, data model, integrations, permissions, NFR coverage, test strategy, threats, rollout, risks |
| `DESIGN.md` | ux-designer | platforms, navigation, flows, screens with states, components, accessibility |
| `BACKLOG.md` (+ `backlog/EP-xx.md` when over ~40 tasks) | delivery-manager | epics, stories, tasks with context pack, DoR, done-when, sprints |
| `DECISIONS.md` | main thread | every user answer: `Q-xx` · question · chosen · discarded · date · docs affected |
| `REVIEW.md` | blueprint-reviewer | findings `RV-xx` and online proposals `P-xx`, with status |
| `CHANGES.md` | main thread | change requests `CR-xx` with impact and status |
| `PROGRESS.md` | the development workflow | task status after the backlog is approved |

Agents write only the file they own. A change another file needs goes back as `UPSTREAM` (§8).

## 2. Frontmatter

```yaml
doc: product | technical | design | backlog
project: <project>
mode: new | evolution
base: null | ../..            # evolution: path to the base docs
version: 1
status: draft                 # draft | approved | skipped (design only, with skip_reason)
approved_version: null
approved_hash: null           # set only by `blueprint_lint.py --approve`
based_on_product_version: 1   # technical, design, backlog
based_on_technical_version: 1 # design, backlog
based_on_design_version: 1    # backlog (null when design skipped)
```

- An approved doc is edited only by setting `status: draft`, `version: n+1` and its changelog line **in
  one edit** (Write or MultiEdit); the change then goes back to its gate. The guard denies anything
  else, except moving only `based_on_*` when nothing it cites changed.
- Changelog line: `- v<n> · <YYYY-MM-DD> · <what> · changed: <ids>`. The `changed:` list feeds the
  cascade (§7); `none` when only wording moved (downstream then only moves `based_on_*`).
- Approval is recorded by `python <scripts>/blueprint_lint.py --approve <file>` (hash of the body), never
  by hand: the guard denies any edit that sets `status: approved`, `approved_version` or `approved_hash`.
  `<scripts>` = the `scripts/` folder of the `blueprint` skill.
- A skipped DESIGN.md is its frontmatter plus one line; the lint ignores its body.

## 3. Ids

Assigned once, never renumbered, never reused. Evolutions continue after the base's highest number;
a base item the evolution changes keeps its id and its defining line ends in `(changed)`. Defined
where the table says; cited anywhere.

| Id | Defined in | Form |
|---|---|---|
| `F-01` feature | PRODUCT §5 heading `### F-01 · name` | |
| `AC-F01-1` acceptance criterion | list item under its feature | `- AC-F01-1 · Given … when … then …` |
| `E-Name` entity | PRODUCT §7 row; fields in TECHNICAL `### E-Name` | PascalCase |
| `G-term` glossary term | PRODUCT §8 row | |
| `Q-01` question / decision asked | DECISIONS.md row | |
| `D-01` technical decision | TECHNICAL §2 row | |
| `I-01` integration | TECHNICAL §5 row | |
| `SP-01` spike | TECHNICAL §10 row → task `T-00.n` | |
| `FL-01` flow · `S-01` screen · `C-Name` component | DESIGN headings / rows | |
| `EP-01` epic · `US-01.1` story · `T-01.1.1` task | BACKLOG headings | story/task number starts with its feature number |
| `RV-01` finding · `P-01` online proposal | REVIEW.md | |
| `CR-01` change request | CHANGES.md | |

Fixed English labels the lint parses, whatever the document language: `Covers:`, `Context pack`,
`Ready when`, `Done when`, `Depends on`, `Executor`, and the table headers in the templates.

## 4. Acceptance criteria

- Gherkin, one observable outcome each, with its `AC-` id. Tests in the development cite the id.
- A **negative** criterion is mandatory when the feature touches permissions, personal data or an
  external integration (who cannot, what is refused, what happens when the system is down).
- NFRs are measurable (`p95 < 300 ms`, `WCAG 2.2 AA`, `RPO 1 h`) — never "fast" or "accessible".
- Stories pass INVEST; a story that is not independent or not testable is split or reported.

## 5. Tasks — context pack, ready, done

Every `agent-ready` task is written for an agent in a **clean session** that has seen nothing else:

```markdown
##### T-03.2.1 · <imperative title>
| Size | Executor | Agent / entry | Repo / area | Depends on |
|---|---|---|---|---|
| M | agent-ready | react-implementer via /dev-task | web/orders | T-00.1, T-03.1.2 |
Covers: US-03.2 · AC-F03-1, AC-F03-2 · E-Order · D-02 · S-04
**Context pack**
- Goal: one line.
- Facts: only what the task uses, inline — fields with type and constraints, decisions one line
  each, role permissions, screen states. Big things by anchor (`TECHNICAL.md#e-order`).
- Where: `path/file.ext:line` of the seam and the closest analogue; greenfield → planned path.
- From dependencies: the contracts, types, endpoints earlier tasks leave behind.
- Conventions: the project workflow's needs — work item, target branch, commit style, entry skill.
- Out of scope: what a well-meaning agent would add and must not.
**Ready when**
- [ ] dependencies done · [ ] spikes it needs resolved · [ ] no open `Q-` / stale id it cites
**Done when**
- AC-F03-1 → test `<name that cites the id>` passes
- `<build / test command>` green, totals reported
- Leaves: <artifact — endpoint, screen, migration, event>
- Project DoD: <from the project's workflow — review, docs, review request>
```

- Budget ~250 words for the pack; the lint fails over 400. No "see above", no reference to this
  conversation.
- `human` tasks: Goal, Covers, Done when.
- `/dev-task T-xx` briefs the architect with the pack as is and closes on the `Done when` list.

## 6. Routing to the project's own agents

Technical owner, in order: the project's own architect (named in the project `CLAUDE.md`, a project
skill, or an agent whose description covers that repo) → the stack architects the code shows, in
parallel, one unified document → `solution-architect`. The owner gets the template and output path; the
project's conventions win on content. If its own contract only writes its own plan format,
`solution-architect` writes TECHNICAL.md and consults it as the source for the code.
Design owner: the project's own designer if any, else `ux-designer` with the project's screens,
components and design system. Executors in tasks name the project's own implementers and entry skill
when they exist.

## 7. Cascade

When an upstream doc bumps, the lint lists downstream items that cite any id in the new `changed:`
lines as **stale**. The owner revisits only those, then updates its `based_on_*_version`. Never a
full replan for a local change.

## 8. Agent return format

```
STATUS: NEEDS_USER_INPUT | READY_FOR_APPROVAL | NEEDS_UPSTREAM_CHANGE
DOC: <file> v<n> · <counts>
CHANGED: <one line per section touched, with ids>
QUESTIONS:                    (NEEDS_USER_INPUT)
1. <question> — unblocks <ids> — contrasts with <ids of other docs>
   a) <option> — <pro> / <con>
   b) …
UPSTREAM:                     (NEEDS_UPSTREAM_CHANGE)
- <doc> · <id> · <what must change> · <why, citing ids>
FOLLOWING CONVENTION: <what the code or base settles, not asked>
COVERAGE:
- ✔/✘ <gate criterion> · <evidence: ids, counts>
```

- At most 4 questions a round, highest impact first, 2-4 options, never a default, never one
  already in DECISIONS.md. What the user's words already answer is not a question.
- Anything inferred and not said is a question, never content.
- Docs are written in the user's language, terse: tables over prose, one line per rule.
