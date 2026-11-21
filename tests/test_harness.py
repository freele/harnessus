"""Run: python3 -m unittest discover -s tests"""

import importlib.util
import os
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skill"
spec = importlib.util.spec_from_file_location("harness", SKILL / "harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
}

RULES = "\n".join(f"# {h}\n\ntext\n" for h in (
    "Planning", "Review", "Verification", "State", "Stops", "Decisions",
    "Tracking", "Harness upkeep"))


class Repo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.root), *args], env=GIT_ENV,
                              capture_output=True, text=True, check=True).stdout

    def write(self, rel: str, text: str) -> None:
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, subject: str, files: dict[str, str]) -> None:
        for rel, text in files.items():
            self.write(rel, text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", subject)

    def config(self, edit=lambda text: text) -> dict:
        text = (SKILL / "templates" / "harness.toml").read_text(encoding="utf-8")
        text = text.replace('why = ""', 'why = "a named failure"')
        text = text.replace('blocking = ""', 'blocking = "breaks the goal"')
        text = text.replace("commands = []", 'commands = ["pytest"]')
        text = text.replace("risk_areas = []", 'risk_areas = ["money"]')
        self.write(".harness/harness.toml", edit(text))
        return harness.load(self.root)


class CheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(shutil.rmtree, self.repo.root)
        self.repo.write("AGENTS.md", RULES)
        for name in ("STATE.md", "DECISIONS.md", "LOG.md"):
            self.repo.write(f".harness/{name}", "# x\n")

    def errors(self, cfg: dict) -> list[str]:
        return [m for level, m in harness.check(self.repo.root, cfg) if level == "ERROR"]

    def test_filled_template_passes(self) -> None:
        self.assertEqual(self.errors(self.repo.config()), [])

    def test_raw_template_lacks_reasons(self) -> None:
        cfg = tomllib.loads((SKILL / "templates" / "harness.toml").read_text(encoding="utf-8"))
        self.assertTrue(any("no 'why'" in m for m in self.errors(cfg)))

    def test_missing_heading_and_state_file(self) -> None:
        (self.repo.root / ".harness/STATE.md").unlink()
        cfg = self.repo.config(lambda t: t.replace("AGENTS.md#Stops", "AGENTS.md#Nowhere"))
        errors = self.errors(cfg)
        self.assertTrue(any("no heading 'Nowhere'" in m for m in errors))
        self.assertTrue(any("paths.state" in m for m in errors))

    def test_cross_model_review_needs_recipe_and_two_executors(self) -> None:
        cfg = self.repo.config(lambda t: t.replace("code = 1", "code = 2"))
        errors = self.errors(cfg)
        self.assertTrue(any("'reviewer'" in m for m in errors))
        self.assertTrue(any("executors.available" in m for m in errors))

    def test_untracked_harness_warns_and_blocks_retro(self) -> None:
        def edit(text: str) -> str:
            head, tail = text.split("[dials.track]\nlevel = 1")
            tail = tail.replace("[dials.reflect]\nlevel = 1", "[dials.reflect]\nlevel = 2")
            return head + "[dials.track]\nlevel = 0" + tail
        found = harness.check(self.repo.root, self.repo.config(edit))
        self.assertTrue(any(level == "WARN" and "cannot be evaluated" in m for level, m in found))
        self.assertTrue(any(level == "ERROR" and "dials.reflect" in m for level, m in found))

    def test_budget_and_dead_link_warn(self) -> None:
        self.repo.write("AGENTS.md", RULES + "[gone](docs/gone.md)\n" + "line\n" * 400)
        found = harness.check(self.repo.root, self.repo.config())
        self.assertTrue(any("budget is 300" in m for _, m in found))
        self.assertTrue(any("docs/gone.md" in m for _, m in found))


class MetricsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(shutil.rmtree, self.repo.root)

    def test_plan_rewrites_before_and_after_code(self) -> None:
        repo = self.repo
        repo.commit("docs: plan", {".harness/work/a.md": "one\ntwo\n"})
        repo.commit("docs: replan", {".harness/work/a.md": "one\ntwo\nthree\n"})
        repo.commit("feat: code", {"src/a.py": "x = 1\n", "tests/test_a.py": "assert True\n"})
        repo.commit("docs: replan again", {".harness/work/a.md": "one\n"})
        repo.commit("fix: code", {"src/a.py": "x = 2\n"})
        repo.commit("docs: rules", {"AGENTS.md": "# Rules\n"})
        m = harness.metrics(repo.root, repo.config(), None)
        self.assertEqual(m["commits"], 6)
        self.assertEqual((m["plan_files"], m["plan_rewrites"], m["plan_rewrites_after_code"]), (1, 2, 1))
        self.assertEqual(m["lines"]["plans"], {"added": 3, "deleted": 2})
        self.assertEqual(m["lines"]["code"]["added"], 2)
        self.assertEqual(m["lines"]["tests"]["added"], 1)
        self.assertEqual(m["plan_to_code"], 1.0)
        self.assertEqual(m["rules_commits"], 1)
        self.assertEqual(m["commit_types"], {"docs": 4, "feat": 1, "fix": 1})
        self.assertIn("rewritten after code began: 1 (1 commits)", harness.render(m))

    def test_log_events_and_default_range(self) -> None:
        repo = self.repo
        repo.commit("feat: before", {"src/a.py": "x = 1\n"})
        rev = repo.git("rev-parse", "--short", "HEAD").strip()
        cfg = repo.config()
        harness.append_event(repo.root, cfg, "init", "-", f"rev={rev}")
        harness.append_event(repo.root, cfg, "friction", "phase 1", "too many\nplans | again")
        repo.commit("feat: after", {"src/b.py": "y = 1\n"})
        m = harness.metrics(repo.root, cfg, None)
        self.assertEqual(m["since"], rev)
        self.assertEqual(m["commits"], 1)
        self.assertEqual(m["events"], {"init": 1, "friction": 1})
        log = (repo.root / ".harness/LOG.md").read_text(encoding="utf-8")
        self.assertIn("| friction | phase 1 | too many / plans / again", log)

    def test_globs(self) -> None:
        classify = harness.classifier(
            {"rules": ["AGENTS.md"], "plans": [".planning/**"], "code": ["src/**", "*.py"], "tests": ["tests/"]})
        self.assertEqual(classify("AGENTS.md"), "rules")
        self.assertEqual(classify(".planning/phases/01/PLAN.md"), "plans")
        self.assertEqual(classify("src/a/b.py"), "code")
        self.assertEqual(classify("setup.py"), "code")
        self.assertEqual(classify("tests/x/test_a.py"), "tests")
        self.assertEqual(classify("docs/a.py"), "other")


if __name__ == "__main__":
    unittest.main()
