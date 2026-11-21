# retro — re-tune the harness from how the work went

`retro` reads the work, not the rule text. It answers one question: which dials
are set wrong for this project. It proposes; the human decides.

Who runs it: an executor that did not do the work of the period. A different
model if one is available, otherwise a fresh session. The author of the work
does not judge the process it worked under.

## 1. Gather

- `harnessus.py metrics` for the period since the last `init` or `retro` event.
  That is the default range when the event's note carries `rev=<sha>`.
- The event log for the same period, every line.
- Changes to rule files in the period: `git log -p` on `paths.rules`.
- One question to the human, asked plainly: what felt off in this period? Take
  the answer as it comes. It does not need to be formal or complete.

## 2. Read the evidence per dial

Signs a dial is set too high:

- A review stage that produced no blocking findings round after round.
- Plan lines several times the code lines, with plans rewritten after code began.
- Stops where the human answered "just do it".
- Artifacts nobody read afterwards.

Signs a dial is set too low:

- `miss`: a failure the harness should have caught.
- `correction`: the executor decided something it should have asked about, or
  the human had to restate a rule.
- `return` caused by lost context or a wrong start.
- `friction` notes that point at the same place.

Numbers and events are material, not verdicts. A high ratio or a count means
"look here". Say what you found when you looked.

## 3. Propose

At most a few moves; a retro that changes everything teaches nothing. For each:

| Dial | From | To | Evidence | What the change costs or saves |
|---|---|---|---|---|

- Lowering a level or removing a step: name what it failed to catch in the
  period.
- Raising a level or adding a rule: name the incident it would have prevented.
  A feeling from the human counts as an incident when they can point at the
  moment it arose.
- A `friction` note with no clear cause stays open. List it; do not invent a
  rule to close it.
- Never propose lowering `stops` or touching a safety rule on your own
  initiative.

## 4. Close

After the human decides:

- Apply the approved changes to `.harnessus/harness.toml` and the rule text.
  Record each as a decision with the human's words.
- Run `harnessus.py check`.
- Record the run: `harnessus.py log retro "rev=<current sha> moved: ..."`.
