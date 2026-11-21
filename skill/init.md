# init — build the harness

Result: `.harnessus/harness.toml`, rule text for every dial above level 0, and the
files those levels require. Works on a new repository and on one that already
has rules or another workflow tool.

## 1. Read the repository before asking anything

- Rule files: `AGENTS.md`, `CLAUDE.md`, tool-specific rule files, contribution
  guides. Note every dated correction or amendment: each one marks a place where
  the earlier way of working failed.
- Existing workflow tooling and its artifacts: planning directories, state
  files, decision logs, handoffs, review reports.
- People and pace: `git shortlog -sn`, commit frequency, branch pattern.
- Evidence of correctness: test suite, CI configuration, golden cases.
- Size: lines of code, number of modules.
- Numbers: write a provisional `.harnessus/harness.toml` from
  `templates/harness.toml` with only `[paths]` filled in, then run
  `harnessus.py metrics`. Plan lines against code lines and plan rewrites after
  code began say more than any description of the process.

## 2. Establish what the project does now

For each dial in `dials.md`, state the level the project effectively works at
today and cite the file that shows it. Then list the failures the evidence
shows: corrections, reverts, rewritten plans, rules amended several times.

## 3. Interview

Follow `interview.md`. One batch, only the questions the repository left open.

## 4. Propose

Show one table and wait for approval:

| Dial | Now | Proposed | Why (failure) | Evidence |
|---|---|---|---|---|

Below it:

- Files to create, and existing files the harness will point at.
- Rule text to add, remove or merge in existing rule files. Rules amended
  several times are proposed as one current text; the amendments' history goes
  to the decisions log.
- What stays exactly as it is, including every safety rule.
- What the shell could not determine.

A proposed level above the current one names the incident behind it. A proposed
level below the current one names what the removed step failed to catch.

## 5. Write, after approval

- `.harnessus/harness.toml`: every dial with its level, `why` and `where`.
- Rule text for each dial above level 0, in the file `where` points to. The
  wording follows the "The harness says" column of `dials.md`, in the project's
  language and terms.
- Files required by the chosen levels, from `templates/`, unless the project
  already has an equivalent.
- If another workflow tool is being replaced, do not delete it or its artifacts.
  Removing it is a separate decision for the human.

## 6. Close

- Run `harnessus.py check`. Fix every error before reporting.
- Record the run: `harnessus.py log init "rev=<current sha> ..."`.
- Report: the dial table as written, what was not verified, and the first event
  kinds the executor should start logging.
