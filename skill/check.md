# check — examine the harness itself

`check` reads the harness, not the work. It finds what makes a harness cost more
than it gives. It changes nothing; it ends with proposals.

## 1. Mechanical part

Run `harness.py check`. It verifies:

- `.harness/harness.toml` parses and every dial has a valid level.
- Every dial has a `why`.
- Every dial above level 0 has a `where` that points to an existing file and
  heading.
- Files and settings each level requires exist: state file, decisions log,
  event log, verification commands, reviewer recipe, round limit, risk areas.
- Work tracking is on. With `track` at 0 the harness cannot be evaluated.
- Rule files exist, stay within the line budget, and their relative links
  resolve.

Report its errors and warnings as they are.

## 2. Reading part

Read every file listed in `paths.rules` and every file a `where` points to.
Look for:

- **Contradictions.** Two rules that cannot both be followed. A rule and a later
  amendment that reverses it.
- **Layers.** A rule followed by amendments, so the reader must combine several
  paragraphs to learn what holds now. Propose one current text; the history
  belongs in the decisions log.
- **Duplicates.** The same rule in two places.
- **Rules without a reason.** No failure named, in the text or in the dial's
  `why`.
- **Rules without a dial.** Text that belongs to none of the eight dials and is
  not project knowledge. Either it guards against something unnamed, or it is
  leftover.
- **Dial text below its level.** The dial says level 2 but the text only covers
  level 1, or the reverse.
- **Dead references.** Commands, files, tools or people that no longer exist.
- **Size.** The rule files load into every session. Say how many lines they are
  and which sections are the largest.

## 3. Report

One list, most costly first. For each item: where it is, what is wrong, the
proposed change. Mark each proposal as remove, merge, rewrite or add. Do not
edit anything until the human approves.

If this run was asked for by a reviewer stage (`review.harness`), the author of
the change under review does not run it.
