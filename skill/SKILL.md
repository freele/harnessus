---
name: hsus
description: Build, check or re-tune this repository's own harness — the working rules for coding agents (planning depth, cross-model review, verification, session state, stops, decisions, work tracking). `init` builds it from repository evidence and a short interview; `check` finds contradictions, redundancy and gaps; `retro` adjusts it from how the work actually went.
---

# harnessus

The harness is the project's own set of working rules for coding agents. It is
plain files in the repository. This skill is the shell around it: it helps build
the harness and keep it honest. After `init` the project works without this
skill; only `check` and `retro` come back to it.

Pick the command from the argument and follow its file, which sits next to this
one:

| Argument | File | Reads | Produces |
|---|---|---|---|
| `init` | `init.md` | the repository, existing rules, interview answers | the harness |
| `check` | `check.md` | the harness itself | proposals: remove, merge, fix |
| `retro` | `retro.md` | how the work went: event log, corrections, git numbers | proposals: which dial to move |

No argument: if `.harnessus/harness.toml` is missing, say so and offer `init`;
otherwise run `check`.

`dials.md` defines the eight dials and their levels. `harnessus.py` does the
mechanical part: `check`, `metrics`, `log`. It needs Python 3.11 or newer and
only the standard library.

## Rules for all three commands

- **Propose, then write.** Show the proposal and wait for the human's approval
  before changing any rule file or `.harnessus/harness.toml`.
- **Never weaken safety rules.** Rules about money, secrets, destructive
  operations and publishing found in the project are carried over verbatim. Do
  not propose lowering `stops` on your own initiative.
- **Adopt in place.** If the project already has a state file, a decisions log
  or a planning directory, point the harness at it. Do not move or rename
  working files to fit a template.
- **Every rule names its failure.** Do not add a step that has no incident or
  unaffordable risk behind it. All dials at 3 is the ceiling, not the goal.
- **Languages.** Talk to the user in their language. Write the harness in the
  language of the project's existing rule files.
- **Follow the project's own rules** on commits, branches and parallel sessions
  while doing any of this.
