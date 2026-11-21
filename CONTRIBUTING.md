# Contributing

harnessus is at version 0 and has been shaped by one project. What it needs most
is evidence from other projects.

## Most useful

A report from running `hsus init`, `check` or `retro` on a real repository:

- Which interview questions changed a dial, and which changed nothing.
- Which dial came out wrong, and what showed it.
- A failure in your work with agents that none of the eight dials covers.
- A number from `harnessus.py metrics` that misled you.

Open an issue. Remove anything private first; the shape of the project is
enough (size, people, agents used).

## Changes

The project holds itself to its own rule: every addition names the failure it
guards against. A pull request that adds a dial, a level, a check or a question
says which incident it would have prevented. Removing something that catches
nothing is as welcome as adding.

Keep it small:

- `harnessus.py` uses the standard library only and runs on Python 3.11+.
- The skill files are prompts read by an agent on every run. Shorter is better.
- A project's harness stays plain files that work without harnessus installed.

Run the tests before sending a change:

```bash
python3 -m unittest discover -s tests
```

## License

By contributing you agree that your contribution is licensed under the
[MIT License](LICENSE).
