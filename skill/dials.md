# Dials

A harness is eight dials. Each dial guards against one named failure. Level 0
means the project accepts that failure as cheap enough to live with. Every dial
at 3 is roughly a full spec-driven pipeline; most projects want most dials at 1.

How levels are set:

- Take the lowest level that covers a failure the project has actually had, or
  cannot afford to have once.
- Raising a level needs an incident: what happened, or what would be
  unaffordable. Lowering a level needs evidence that the step caught nothing.
- A level is a project default, not a ceremony for every task. `plan` is set per
  task class and `review` per stage for exactly this reason.

Each dial is recorded in `.harness/harness.toml` with its level, `why` (the
failure this level answers) and `where` (the file and heading that hold the rule
text). A setting without a `why` is a defect.

## 1. plan — how much is written before code

Guards against: building the wrong thing and finding out late.

Set per task class: `trivial`, `ordinary`, `risky`. `risk_areas` names what
makes a task risky in this project (money paths, schema, public API,
irreversible operations).

| Level | The harness says |
|---|---|
| 0 | No written plan. Do the work. |
| 1 | Task card: goal, files, acceptance criteria, prohibitions. One screen. It does not restate code in prose. |
| 2 | A decisions file before the card: contracts, rules and boundaries as tables, each written once. Reviewed before code. |
| 3 | Research, decisions, plan, plan check, execution and verification as separate artifacts. |

Evidence: ratio of plan lines to code lines; plan rewrites after code began;
`return` and `miss` events; whether one person can hold the project in their head.

## 2. review — who reads the work besides its author

Guards against: errors the author cannot see in its own work.

Set per stage: `decisions`, `plan`, `code`, `harness` (changes to the harness
itself).

| Level | Reviewer |
|---|---|
| 0 | Nobody. |
| 1 | The same model in a fresh session. It gets the artifact and the acceptance criteria, not the author's reasoning. |
| 2 | A different model. |
| 3 | A human. |

A fresh session removes anchoring on the author's reasoning. Only a different
model removes blind spots the two sessions share. Plan review is usually the
worst value: a plan is derived from decisions that were already reviewed.

Must be written at level 1 and above:

- `max_rounds` — how many review rounds one artifact gets.
- `blocking` — which findings force another round. Everything else goes to a
  deferred list. Without this two models write to each other indefinitely.
- At level 2: `reviewer` — the exact way to invoke the other model. If only one
  model is available, level 1 is the ceiling and the harness says so.

Evidence: `review` events (rounds, blocking and non-blocking counts); defects
found after a review passed (`miss`).

## 3. verify — what counts as done

Guards against: work declared done without evidence.

| Level | The harness says |
|---|---|
| 0 | The author's word. |
| 1 | Named commands (tests, linters, type check) run after each unit of work. The result is reported with its output; a failure is reported as a failure. |
| 2 | Plus a goal check: each acceptance criterion is marked verified or not verified, with how. Unverified items go into the handoff. |
| 3 | Plus independent verification by another executor or acceptance by a human. |

Must be written at level 1 and above: `commands`.

## 4. state — how the next session knows where this one stopped

Guards against: context lost between sessions; a session ending with unsaved work.

| Level | The harness says |
|---|---|
| 0 | Git history is enough. |
| 1 | One state file, overwritten: revision, what is in progress, next step. |
| 2 | Plus a fixed handoff format: revision; accepted decisions; open proposals, kept apart from decisions; checks run and their results; what is not done or not verified; next step. |
| 3 | Plus mechanical enforcement where the executor supports it, such as a hook that refuses to end a session without a state update. |

Evidence: number of people and sessions; parallel sessions sharing one checkout;
`return` events caused by lost context.

## 5. stops — when the executor goes to the human

Guards against: the executor doing something costly, irreversible or visible
without asking. And against the opposite failure: asking about everything.

| Level | The harness says |
|---|---|
| 0 | The executor asks only before destructive operations. |
| 1 | An explicit stop list: irreversible actions, outward actions, spending, changes visible to users. Everything else the executor decides and marks "decided by executor". The human gets that list when the unit closes and can reverse any item. |
| 2 | Plus a scope stop: when work grows past a stated bound, the executor stops, finds the requirement that led it astray and comes with an analysis. Doubt outside the stop list goes to the reviewer, not to the human. |
| 3 | The human approves every plan and every merge. |

Safety rules already present in the project (money, secrets, destructive
operations, publishing) are carried over verbatim at any level. The shell never
proposes weakening them.

Evidence: `stop` events and whether each stop was needed; `correction` events
where the executor decided something it should have asked about.

## 6. knowledge — where decisions and rules live

Guards against: a decision made in chat and lost; the same question argued
again; a rule living in one executor's private memory.

| Level | The harness says |
|---|---|
| 0 | Commit messages. |
| 1 | A decisions log: date, who decided, the human's words quoted where the human decided, the executor's wording marked as such. Proposals are not logged as decisions. |
| 2 | Plus a glossary of project terms. A rule that must hold is written to the rules file, not to executor memory. A superseded rule is rewritten in place; its history stays in the decisions log. |
| 3 | Plus an architecture document or decision record per decision. |

## 7. track — how work under the harness is measured

Guards against: no way to tell whether the harness helps or only costs; a
feeling that something is off with nothing to check it against.

| Level | The harness says |
|---|---|
| 0 | Nothing is measured. `check` warns that the harness cannot be evaluated. |
| 1 | Numbers from git on demand (`harness.py metrics`): plan lines against code lines, plan rewrites, plan rewrites after code began, rule-file churn, share of fixes and reverts. Costs the executor nothing. |
| 2 | Plus an event log, one line per event at the moment it happens: `friction`, `correction`, `replan`, `return`, `review`, `stop`, `miss`. |
| 3 | Plus, per unit of work, estimate against actual (size, review rounds) and token or cost figures where the executor exposes them. |

Limits. Not every session is stored, and the event log is self-reported, so it
undercounts; the git numbers are the cross-check. Numbers are material for a
retro, not verdicts.

Events:

| Kind | When it is written |
|---|---|
| `friction` | The human says something feels off. No formalization needed. |
| `correction` | The human corrects the executor or changes a rule. |
| `replan` | A plan or decisions file is rewritten. Note whether code had begun. |
| `return` | Work goes back to an earlier stage or is redone. |
| `review` | A review round ends: who, round number, blocking and other findings. |
| `stop` | The executor went to the human. Later: was it needed? |
| `miss` | A failure surfaced that the harness should have caught. |
| `init`, `retro` | The shell ran. The note carries `rev=<sha>`. |

## 8. reflect — when the harness itself is examined

Guards against: a harness that only grows, contradicts itself, or holds rules
nobody follows.

| Level | The harness says |
|---|---|
| 0 | Never, unless someone thinks of it. |
| 1 | `check` on demand and before any change to the harness. |
| 2 | `retro` at each unit boundary (phase, milestone) or when friction notes accumulate (default: three). Run by an executor that did not do the period's work; a different model if one is available. It proposes, the human decides. |
| 3 | Plus the mechanical part of `check` at every session start; metric thresholds trigger a retro. |

Requires `track` at 1 or above: a retro needs material.
