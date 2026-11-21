#!/usr/bin/env python3
"""Mechanical helpers for a project harness: check, metrics, log.

Reads .harness/harness.toml in the repository. Standard library only;
needs Python 3.11 or newer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    sys.exit("harness.py needs Python 3.11 or newer (tomllib)")

CONFIG = Path(".harness") / "harness.toml"
PLAN_CLASSES = ("trivial", "ordinary", "risky")
REVIEW_STAGES = ("decisions", "plan", "code", "harness")
SIMPLE_DIALS = ("verify", "state", "stops", "knowledge", "track", "reflect")
DIAL_KEYS = {
    "plan": PLAN_CLASSES,
    "review": REVIEW_STAGES,
    **{name: ("level",) for name in SIMPLE_DIALS},
}
EVENT_KINDS = (
    "init", "friction", "correction", "replan", "return",
    "review", "stop", "miss", "retro",
)
LOG_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \| ([a-z]+) \| ([^|]*) \| (.*)$")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
COMMIT_TYPE = re.compile(r"^(\w+)(\([^)]*\))?!?:")
PATH_CLASSES = ("rules", "plans", "tests", "code")  # first match wins


# ---------------------------------------------------------------- config

def find_root(start: Path) -> Path:
    for folder in (start, *start.parents):
        if (folder / CONFIG).is_file():
            return folder
    sys.exit(f"no {CONFIG} found in {start} or above; run the init command first")


def load(root: Path) -> dict:
    with open(root / CONFIG, "rb") as fh:
        return tomllib.load(fh)


def as_list(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [v for v in value or [] if isinstance(v, str)]


def dial_levels(name: str, dial: dict) -> list[int]:
    return [v for k in DIAL_KEYS[name]
            if isinstance(v := dial.get(k), int) and not isinstance(v, bool)]


def glob_re(pattern: str) -> re.Pattern[str]:
    if pattern.endswith("/"):
        pattern += "**"
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def classifier(paths: dict):
    table = [(cls, [glob_re(p) for p in as_list(paths.get(cls))]) for cls in PATH_CLASSES]

    def classify(path: str) -> str:
        for cls, patterns in table:
            if any(p.match(path) for p in patterns):
                return cls
        return "other"

    return classify


# ----------------------------------------------------------------- check

def check(root: Path, cfg: dict) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    def err(msg: str) -> None:
        found.append(("ERROR", msg))

    def warn(msg: str) -> None:
        found.append(("WARN", msg))

    if cfg.get("version") != 1:
        err("version: expected 1")
    dials = cfg.get("dials") or {}
    paths = cfg.get("paths") or {}
    top: dict[str, int] = {}

    for name, keys in DIAL_KEYS.items():
        dial = dials.get(name)
        if not isinstance(dial, dict):
            err(f"dials.{name}: missing")
            continue
        for key in keys:
            value = dial.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 3:
                err(f"dials.{name}.{key}: expected a level from 0 to 3, got {value!r}")
        top[name] = max(dial_levels(name, dial), default=0)
        if not str(dial.get("why", "")).strip():
            err(f"dials.{name}: no 'why' — a setting without a reason")
        if top[name] > 0:
            check_where(root, name, str(dial.get("where", "")).strip(), err)

    plan, review = dials.get("plan") or {}, dials.get("review") or {}
    if top.get("plan", 0) >= 2 and not as_list(plan.get("risk_areas")):
        err("dials.plan: level 2 or above needs 'risk_areas'")
    if top.get("review", 0) >= 1:
        rounds = review.get("max_rounds")
        if not isinstance(rounds, int) or rounds < 1:
            err("dials.review: 'max_rounds' must be 1 or more")
        if not str(review.get("blocking", "")).strip():
            err("dials.review: no 'blocking' — nothing says which findings force another round")
    if 2 in dial_levels("review", review):
        if not str(review.get("reviewer", "")).strip():
            err("dials.review: a stage at level 2 needs 'reviewer' (how to invoke the other model)")
        if len(as_list((cfg.get("executors") or {}).get("available"))) < 2:
            err("dials.review: a stage at level 2 needs two entries in executors.available")
    if top.get("verify", 0) >= 1 and not as_list((dials.get("verify") or {}).get("commands")):
        err("dials.verify: level 1 or above needs 'commands'")

    for dial, level, key in (("state", 1, "state"), ("knowledge", 1, "decisions"), ("track", 2, "log")):
        if top.get(dial, 0) >= level:
            target = str(paths.get(key, "")).strip()
            if not target or not (root / target).is_file():
                err(f"dials.{dial}: level {level} or above needs paths.{key} to exist ({target or 'not set'})")

    track = top.get("track", 0)
    if track == 0:
        warn("dials.track is 0: work is not measured, so the harness cannot be evaluated")
    elif not as_list(paths.get("code")) or not as_list(paths.get("plans")):
        err("dials.track: needs paths.code and paths.plans to tell plans from code")
    if top.get("reflect", 0) >= 2 and track == 0:
        err("dials.reflect: level 2 or above needs dials.track at 1 or above")

    check_rules(root, cfg, err, warn)
    return found


def check_where(root: Path, name: str, where: str, err) -> None:
    if not where:
        err(f"dials.{name}: above level 0 but no 'where' — the rule text is not located")
        return
    file, _, heading = where.partition("#")
    target = root / file
    if not target.is_file():
        err(f"dials.{name}.where: {file} does not exist")
        return
    if heading:
        wanted = heading.strip().lower()
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if not any(ln.startswith("#") and wanted in ln.lower() for ln in lines):
            err(f"dials.{name}.where: no heading '{heading}' in {file}")


def check_rules(root: Path, cfg: dict, err, warn) -> None:
    rules = as_list((cfg.get("paths") or {}).get("rules"))
    if not rules:
        err("paths.rules: no rule files listed")
    total = 0
    for rel in rules:
        target = root / rel
        if not target.is_file():
            err(f"paths.rules: {rel} does not exist")
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        total += len(text.splitlines())
        for link in MD_LINK.findall(text):
            link = link.split("#")[0]
            if not link or re.match(r"[a-z][a-z0-9+.-]*:", link, re.I):
                continue
            if not (target.parent / link).exists():
                warn(f"{rel}: link to {link} does not resolve")
    budget = (cfg.get("budget") or {}).get("rules_lines")
    if isinstance(budget, int) and total > budget:
        warn(f"rule files are {total} lines, budget is {budget}; they load into every session")


# --------------------------------------------------------------- metrics

def git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if done.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def read_commits(root: Path, since: str | None) -> list[dict]:
    args = ["log", "--reverse", "--no-merges", "--no-renames", "--numstat",
            "--date=short", "--format=@@%h|%ad|%s"]
    if since:
        args.append(f"{since}..HEAD")
    commits: list[dict] = []
    for line in git(root, *args).splitlines():
        if line.startswith("@@"):
            sha, date, subject = line[2:].split("|", 2)
            commits.append({"sha": sha, "date": date, "subject": subject, "files": []})
        elif line.strip() and commits:
            added, deleted, path = line.split("\t", 2)
            commits[-1]["files"].append(
                (int(added) if added.isdigit() else 0, int(deleted) if deleted.isdigit() else 0, path))
    return commits


def measure(commits: list[dict], classify) -> dict:
    """Count lines per class and plan rewrites.

    "After code began" is a heuristic: a plan file counts as rewritten after
    code began when it changes after the first later commit that touches code
    or tests. With several plans in flight it overcounts; the `replan` events
    in the log are the precise source.
    """
    lines = {cls: [0, 0] for cls in (*PATH_CLASSES, "other")}
    plans: dict[str, dict] = {}
    types: Counter[str] = Counter()
    rules_commits = 0
    for commit in commits:
        subject = commit["subject"]
        match = COMMIT_TYPE.match(subject)
        types["revert" if subject.lower().startswith("revert") else
              match.group(1).lower() if match else "other"] += 1
        touched = set()
        for added, deleted, path in commit["files"]:
            cls = classify(path)
            touched.add(cls)
            lines[cls][0] += added
            lines[cls][1] += deleted
            if cls != "plans":
                continue
            plan = plans.get(path)
            if plan is None:
                plans[path] = {"rewrites": 0, "after_code": 0, "code_began": False}
            else:
                plan["rewrites"] += 1
                plan["after_code"] += plan["code_began"]
        rules_commits += "rules" in touched
        if touched & {"code", "tests"}:
            for plan in plans.values():
                plan["code_began"] = True
    built = lines["code"][0] + lines["tests"][0]
    return {
        "commits": len(commits),
        "first": commits[0]["date"] if commits else None,
        "last": commits[-1]["date"] if commits else None,
        "lines": {cls: {"added": a, "deleted": d} for cls, (a, d) in lines.items()},
        "plan_to_code": round(lines["plans"][0] / built, 2) if built else None,
        "plan_files": len(plans),
        "plan_files_rewritten": sum(p["rewrites"] > 0 for p in plans.values()),
        "plan_rewrites": sum(p["rewrites"] for p in plans.values()),
        "plan_files_rewritten_after_code": sum(p["after_code"] > 0 for p in plans.values()),
        "plan_rewrites_after_code": sum(p["after_code"] for p in plans.values()),
        "rules_commits": rules_commits,
        "commit_types": dict(types.most_common()),
    }


def read_events(root: Path, cfg: dict) -> list[dict]:
    rel = str((cfg.get("paths") or {}).get("log", "")).strip()
    if not rel or not (root / rel).is_file():
        return []
    events = []
    for line in (root / rel).read_text(encoding="utf-8").splitlines():
        match = LOG_LINE.match(line)
        if match:
            date, kind, unit, note = (part.strip() for part in match.groups())
            events.append({"date": date, "kind": kind, "unit": unit, "note": note})
    return events


def last_marked_rev(root: Path, events: list[dict]) -> str | None:
    for event in reversed(events):
        if event["kind"] in ("init", "retro"):
            match = re.search(r"\brev=([0-9a-f]{7,40})\b", event["note"])
            if match:
                ok = subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", match.group(1) + "^{commit}"],
                    capture_output=True)
                return match.group(1) if ok.returncode == 0 else None
            return None
    return None


def metrics(root: Path, cfg: dict, since: str | None) -> dict:
    events = read_events(root, cfg)
    since = since or last_marked_rev(root, events)
    commits = read_commits(root, since)
    result = measure(commits, classifier(cfg.get("paths") or {}))
    result["since"] = since
    if commits:
        events = [e for e in events if e["date"] >= commits[0]["date"]]
    result["events"] = dict(Counter(e["kind"] for e in events).most_common())
    return result


def render(m: dict) -> str:
    out = [f"Range: {m['since'] + '..HEAD' if m['since'] else 'whole history'}"
           f" — {m['commits']} commits, {m['first']} to {m['last']}", "", "Lines added / deleted"]
    for cls, n in m["lines"].items():
        out.append(f"  {cls:<6} {n['added']:>8} / {n['deleted']}")
    ratio = m["plan_to_code"]
    out += [
        f"  plans : code+tests (added) = {ratio if ratio is not None else 'n/a'} : 1",
        "",
        f"Plan files: {m['plan_files']}; rewritten later: {m['plan_files_rewritten']}"
        f" ({m['plan_rewrites']} commits)",
        f"  rewritten after code began: {m['plan_files_rewritten_after_code']}"
        f" ({m['plan_rewrites_after_code']} commits) — heuristic, see dials.md",
        f"Commits touching rule files: {m['rules_commits']}",
        "Commits by type: " + (", ".join(f"{k} {v}" for k, v in m["commit_types"].items()) or "none"),
        "Log events: " + (", ".join(f"{k} {v}" for k, v in m["events"].items()) or "none"),
    ]
    return "\n".join(out)


# ------------------------------------------------------------------- log

def append_event(root: Path, cfg: dict, kind: str, unit: str, note: str) -> str:
    rel = str((cfg.get("paths") or {}).get("log", "")).strip()
    if not rel:
        sys.exit("paths.log is not set in .harness/harness.toml")
    target = root / rel
    clean = lambda s: re.sub(r"\s*[\r\n|]+\s*", " / ", s).strip()  # noqa: E731
    line = f"- {dt.date.today().isoformat()} | {kind} | {clean(unit) or '-'} | {clean(note)}"
    target.parent.mkdir(parents=True, exist_ok=True)
    head = "" if target.exists() else "# Work log\n\n"
    tail = target.read_text(encoding="utf-8") if target.exists() else ""
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(head + ("" if not tail or tail.endswith("\n") else "\n") + line + "\n")
    return line


# ------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness.py", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, help="repository root (default: found from the current folder)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="verify the harness settings and files")
    p_metrics = sub.add_parser("metrics", help="numbers from git and the event log")
    p_metrics.add_argument("--since", help="revision to start from (default: last init/retro event, else all)")
    p_metrics.add_argument("--json", action="store_true")
    p_log = sub.add_parser("log", help="append one event to the work log")
    p_log.add_argument("kind", choices=EVENT_KINDS)
    p_log.add_argument("note")
    p_log.add_argument("--unit", default="-", help="phase, task or plan the event belongs to")
    args = parser.parse_args(argv)

    root = args.root.resolve() if args.root else find_root(Path.cwd())
    cfg = load(root)
    if args.command == "check":
        found = check(root, cfg)
        for level, message in found:
            print(f"{level:<5} {message}")
        errors = sum(level == "ERROR" for level, _ in found)
        print(f"{errors} errors, {len(found) - errors} warnings")
        return 1 if errors else 0
    if args.command == "metrics":
        result = metrics(root, cfg, args.since)
        print(json.dumps(result, indent=2) if args.json else render(result))
        return 0
    print(append_event(root, cfg, args.kind, args.unit, args.note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
