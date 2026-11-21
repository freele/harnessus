# Interview

Ask only what the repository cannot tell. Read the repository first (see
`init.md`), then put the remaining questions in one batch. Where evidence
already suggests an answer, state it and ask for confirmation instead of asking
the open question. Ask in the language the user writes in.

| # | Question | Repository evidence that can replace it | Dials it sets |
|---|---|---|---|
| 1 | How many people work on this project, and who makes the decisions? | `git shortlog -sn`, roles named in rule files | stops, state, knowledge |
| 2 | Which coding agents and models are available? Which one writes by default, which can review, and how is each invoked? | Rule files, agent config directories, review artifacts | review, state |
| 3 | Can one person hold the whole project in their head? | Code size, number of modules, architecture documents | plan, knowledge |
| 4 | What is irreversible here, or costs money or reputation when it goes wrong? Name the areas. | Safety sections in rule files, deploy and payment code | stops, plan (`risk_areas`), review |
| 5 | How does work run: one long session, many short ones, several in parallel on one checkout? | Handoff files, worktrees, branch patterns | state |
| 6 | What counts as proof that a change works? | Test suite, CI config, golden cases | verify |
| 7 | What do you want to be asked about first, and what is fine to hear about afterwards? | Dated corrections and stop lists in rule files | stops |
| 8 | What went wrong recently when working with agents here? One to three cases. | Corrections in rule files, reverts, rewritten plans | every dial: each case names a failure |

Question 8 matters most. A case that happened sets a dial with more confidence
than any general preference.
