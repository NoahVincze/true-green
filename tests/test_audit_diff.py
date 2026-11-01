"""Tests for skills/truegreen/scripts/audit_diff.py.

Each file in tests/audit_cases/ is one scenario run in a throwaway git repo:

    # free-text description
    expect: HIGH TEST-SKIP tests/test_calc.py    (one line per finding, or "expect: none")
    === base <path>      file content committed as the base
    === change <path>    file content written on top, left uncommitted
    === delete <path>    file removed on top of the base

The audit must report exactly the expected (severity, code, file) set.
Run with: python -m unittest discover -s tests
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "truegreen" / "scripts" / "audit_diff.py"
CASES = Path(__file__).resolve().parent / "audit_cases"


def parse_case(text):
    base, change, deleted, expect = {}, {}, [], set()
    target = None
    for line in text.splitlines(keepends=True):
        if line.startswith("=== "):
            kind, path = line[4:].split(None, 1)
            path = path.strip()
            if kind == "delete":
                deleted.append(path)
                target = None
            else:
                files = {"base": base, "change": change}[kind]
                files[path] = ""
                target = (files, path)
            continue
        if target:
            files, path = target
            files[path] += line
        elif line.startswith("expect:"):
            parts = line[len("expect:"):].split()
            if parts != ["none"]:
                expect.add(tuple(parts))
    return base, change, deleted, expect


def git(repo, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
                    "-c", "core.autocrlf=false", *args],
                   cwd=repo, check=True, capture_output=True)


def write(repo, files):
    for path, content in files.items():
        dest = Path(repo, path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8", newline="\n")


def make_repo(base):
    repo = tempfile.mkdtemp(prefix="truegreen-test-")
    git(repo, "init", "-q", "-b", "main")
    write(repo, base)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def run_audit(repo, *args):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", repo, *args],
                          capture_output=True, text=True)
    return proc


class AuditCases(unittest.TestCase):
    def test_cases(self):
        cases = sorted(CASES.glob("*.case"))
        self.assertTrue(cases, "no cases found in %s" % CASES)
        for case in cases:
            with self.subTest(case=case.stem):
                base, change, deleted, expect = parse_case(case.read_text(encoding="utf-8"))
                repo = make_repo(base)
                try:
                    write(repo, change)
                    for path in deleted:
                        Path(repo, path).unlink()
                    proc = run_audit(repo, "--json")
                    report = json.loads(proc.stdout)
                    got = {(f["severity"], f["code"], f["file"]) for f in report["findings"]}
                    self.assertEqual(got, expect, json.dumps(report["findings"], indent=2))
                    self.assertEqual(proc.returncode, 1 if any(e[0] == "HIGH" for e in expect) else 0)
                finally:
                    shutil.rmtree(repo, ignore_errors=True)


class AuditCli(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo({"calc.py": "def add(a, b):\n    return a + b\n"})

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_text_output_without_changes(self):
        proc = run_audit(self.repo)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("No findings.", proc.stdout)
        self.assertIn("Summary: 0 HIGH, 0 MEDIUM.", proc.stdout)

    def test_unknown_base_is_usage_error(self):
        proc = run_audit(self.repo, "--base", "no-such-branch")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("audit_diff:", proc.stderr)

    def test_not_a_repo_is_usage_error(self):
        empty = tempfile.mkdtemp(prefix="truegreen-test-")
        try:
            self.assertEqual(run_audit(empty).returncode, 2)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_base_branch_includes_committed_changes(self):
        git(self.repo, "switch", "-q", "-c", "feature")
        write(self.repo, {"calc.py": "def add(a, b):\n    try:\n        return a + b\n    except Exception:\n        return 0\n"})
        git(self.repo, "commit", "-q", "-am", "swallow")
        self.assertEqual(run_audit(self.repo).returncode, 0, "nothing uncommitted vs HEAD")
        proc = run_audit(self.repo, "--base", "main", "--json")
        self.assertEqual(proc.returncode, 1)
        codes = {f["code"] for f in json.loads(proc.stdout)["findings"]}
        self.assertEqual(codes, {"SWALLOW"})

    def test_skips_its_own_file(self):
        vendored = Path(self.repo, "tools", "audit_diff.py")
        vendored.parent.mkdir()
        shutil.copy(SCRIPT, vendored)
        proc = subprocess.run([sys.executable, str(vendored), "--repo", self.repo, "--json"],
                              capture_output=True, text=True)
        self.assertEqual(json.loads(proc.stdout)["findings"], [])
        # the copy is still audited when a different copy of the script runs
        self.assertNotEqual(json.loads(run_audit(self.repo, "--json").stdout)["findings"], [])


if __name__ == "__main__":
    unittest.main()
