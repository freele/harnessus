# harnessus

The harness you didn't know you needed.

A small shell for building and maintaining a project's own working rules for
coding agents — its harness — instead of adopting a fixed workflow framework.

Status: version 0. Built from one project's experience and not yet applied
end to end. Expect the dials and the interview to change.

## The idea

A fixed framework runs the same pipeline for every project and every task, so
the amount of planning follows the ceremony, not the risk. A small project ends
up with more plan text than code, and with people debugging prose.

Here the harness is generated for the repository and then lives in it as plain
files: a rules file, a state file, a decisions log, a work log. The shell is
only needed to build it and to keep it honest.

## Dials

A harness is eight dials, each guarding against one named failure, each set
from 0 to 3. See [skill/dials.md](skill/dials.md).

| Dial | Guards against |
|---|---|
| plan | building the wrong thing and finding out late |
| review | errors the author cannot see in its own work |
| verify | work declared done without evidence |
| state | context lost between sessions |
| stops | the executor acting without asking — or asking about everything |
| knowledge | decisions and rules lost in chat or in an agent's memory |
| track | no way to tell whether the harness helps or only costs |
| reflect | a harness that only grows or contradicts itself |

`plan` is set per task class (trivial, ordinary, risky) and `review` per stage
(decisions, plan, code, harness changes), each stage choosing between nobody, a
fresh session of the same model, a different model, or a human. Every dial at 3
is roughly a full spec-driven pipeline. Most projects want most dials at 1.

## Three commands

| Command | Reads | Produces |
|---|---|---|
| `harnessus init` | the repository, its existing rules, a short interview | the harness |
| `harnessus check` | the harness itself | what to remove, merge or fix |
| `harnessus retro` | how the work went: event log, corrections, git numbers | which dial to move |

All three propose and wait for a human before writing. None of them weakens a
safety rule the project already has.

## Tracking

The harness measures the work done under it, so a retro has something to stand
on besides impressions:

- From git, at no cost: plan lines against code lines, plan rewrites, plan
  rewrites after code began, rule-file churn, share of fixes and reverts.
- From a one-line event log: `friction`, `correction`, `replan`, `return`,
  `review`, `stop`, `miss`.

```bash
python3 skill/harnessus.py metrics
```

The numbers are material for a retro, not verdicts. "Rewritten after code began"
is a heuristic, and the event log is self-reported.

## What lands in your repository

```
.harnessus/harness.toml   dial levels, each with why and where
.harnessus/STATE.md       where work stopped (overwritten)
.harnessus/DECISIONS.md   what was decided, by whom, in whose words
.harnessus/LOG.md         work events, one line each
AGENTS.md               rule text for every dial above level 0
```

Paths are settings. A project that already has these files keeps them where
they are.

## Install

```bash
./install.sh
```

This links `skill/` as `~/.claude/skills/harnessus`. Pass other skills directories
as arguments for other agents. An agent without skill support reads
`skill/SKILL.md` and follows it.

`harnessus.py` needs Python 3.11 or newer and nothing else.

## Tests

```bash
python3 -m unittest discover -s tests
```
