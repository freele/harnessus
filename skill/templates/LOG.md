# Work log

One line per event, written when it happens. Append with
`harnessus.py log <kind> [--unit <unit>] "<note>"`, or by hand in the same format.

Kinds: `friction` (the human says something feels off), `correction` (the human
corrects the executor or a rule), `replan` (a plan is rewritten; say whether
code had begun), `return` (work goes back or is redone), `review` (a round
ends: who, round, blocking, other), `stop` (the executor went to the human),
`miss` (a failure the harness should have caught), `init`, `retro`.

Format: `- YYYY-MM-DD | kind | unit | note`

