#!/usr/bin/env python3
"""audit_diff.py - flag "fake success" patterns in your changes.

Compares the working tree (staged, unstaged and untracked files) against a base
ref and reports changes that make checks pass without making the code work:
edited or skipped tests, changed expectations, test values special-cased in
production code, swallowed exceptions, mock or placeholder data, new data
files, and suppressed checks.

Usage:
    python3 audit_diff.py                 # compare against HEAD
    python3 audit_diff.py --base main     # compare against a branch
    python3 audit_diff.py --json          # machine-readable output

Exit code: 1 if any HIGH finding, 0 otherwise, 2 on usage errors.
Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------- path rules

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|__tests__|specs?|testing)/"
    r"|(^|/)test_[^/]*\.py$|_test\.(py|go)$|\.(test|spec)\.[cm]?[jt]sx?$"
    r"|(^|/)conftest\.py$|(^|/)(pytest\.ini|tox\.ini|\.coveragerc)$"
    r"|(^|/)(jest|vitest)\.config\.[cm]?[jt]s$|__snapshots__/|\.snap$"
)
CONFIG_PATH_RE = re.compile(
    r"(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.ya?ml$|(^|/)Jenkinsfile$"
    r"|(^|/)\.circleci/|(^|/)azure-pipelines\.ya?ml$|(^|/)Makefile$"
    r"|(^|/)package\.json$|(^|/)pyproject\.toml$|(^|/)setup\.cfg$"
    r"|(^|/)noxfile\.py$|(^|/)\.pre-commit-config\.ya?ml$"
)
DATA_EXT_RE = re.compile(r"\.(csv|tsv|jsonl|ndjson|parquet|xlsx?|sqlite3?|db|pkl|feather)$", re.I)
CODE_EXT_RE = re.compile(r"\.(py|[cm]?[jt]sx?|go|rb|java|kt|cs|rs|php|scala|swift)$")
IGNORE_PATH_RE = re.compile(r"(^|/)(\.git|node_modules|\.venv|venv|__pycache__|\.pytest_cache|dist|build)/")
# this script's own patterns would match themselves when it is vendored into a repo
SELF_PATH = os.path.realpath(__file__)


def is_test(path):
    return bool(TEST_PATH_RE.search(path))


def is_code(path):
    return bool(CODE_EXT_RE.search(path))


# ------------------------------------------------------------- line patterns

SKIP_RE = re.compile(
    r"@pytest\.mark\.(skip|skipif|xfail)\b|\bpytest\.(skip|xfail|importorskip)\("
    r"|@unittest\.(skip|skipIf|skipUnless|expectedFailure)\b|\bself\.skipTest\("
    r"|\b(it|test|describe|context)\.(skip|only|todo)\(|\b(xit|xdescribe|xtest|fit|fdescribe)\("
    r"|\bt\.Skip(Now|f)?\(|#\[ignore\]|@Disabled\b|@Ignore\b"
)
ASSERT_RE = re.compile(
    r"^\s*assert\b|\bexpect\(|\bself\.assert\w*\(|\bassert[A-Z]\w*\(|\bpytest\.raises\("
    r"|\bpytest\.approx\(|\.should\b|\bt\.(Error|Errorf|Fatal|Fatalf|Fail)\("
)
WEAK_ASSERT_RE = re.compile(
    r"^\s*assert\s+(True|1|not\s+False)\s*(#.*)?$|\bexpect\(\s*true\s*\)|\.toBeDefined\(\)|\.toBeTruthy\(\)"
    r"|^\s*assert\s+[\w.\[\]'\"()]+\s+is\s+not\s+None\s*(#.*)?$"
)
TEST_ENV_RE = re.compile(
    r"PYTEST_CURRENT_TEST|['\"]pytest['\"]\s+in\s+sys\.modules|sys\.modules\[\s*['\"]pytest"
    r"|^\s*(import|from)\s+(pytest|unittest\.mock)\b|\bconftest\b|['\"][^'\"]*\btests?/[^'\"]+['\"]"
    r"|\binspect\.stack\(|JEST_WORKER_ID|VITEST\b|NODE_ENV\s*===?\s*['\"]test"
    r"|os\.environ(\.get)?\s*[\(\[]\s*['\"](CI|TESTING|PYTEST\w*|UNIT_TEST\w*)['\"]"
)
PLACEHOLDER_RE = re.compile(
    r"\b(mock(ed)?|fake|dummy|stub(bed)?|placeholder|lorem|hard-?coded|sample[_ ]?data|simulated?"
    r"|demo[_ ]?data|canned|fallback|made[_ -]?up)\w*",
    re.I,
)
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
SUPPRESS_HIGH_RE = re.compile(
    r"\|\|\s*true\b|\|\|\s*exit\s+0\b|--no-verify\b|continue-on-error:\s*true|allow_failure:\s*true"
    r"|--passWithNoTests|\bset\s+\+e\b"
)
SUPPRESS_MED_RE = re.compile(
    r"#\s*type:\s*ignore|#\s*noqa\b|#\s*pragma:\s*no\s*cover|@ts-ignore|@ts-expect-error|eslint-disable"
    r"|//\s*nolint|--deselect\b|-k\s+['\"]?not\s|--ignore=|\bSKIP_TESTS\b"
)
COVERAGE_RE = re.compile(r"(fail_under\s*=\s*|--cov-fail-under[= ]\s*|coverageThreshold.*?:\s*)(\d+(\.\d+)?)")
PY_EXCEPT_RE = re.compile(r"^(\s*)except\b\s*(\(?[^:]*\)?)?\s*(as\s+\w+)?\s*:\s*(.*)$")
BROAD_EXC_RE = re.compile(r"^\s*(\(\s*)?(Exception|BaseException)?\s*\)?\s*$")
IO_EXC_RE = re.compile(
    r"\b(URLError|HTTPError|RequestException|ConnectionError|Timeout\w*|OSError|IOError|socket\.\w+"
    r"|FileNotFoundError|JSONDecodeError|ValueError|KeyError|requests\.\w+|httpx\.\w+|aiohttp\.\w+)\b"
)
JS_EMPTY_CATCH_RE = re.compile(r"catch\s*(\(\s*[\w$]*\s*\))?\s*\{\s*\}|\.catch\(\s*\(\s*[\w$]*\s*\)\s*=>\s*(\{\s*\}|null|undefined|\[\]|\{\}|['\"]|\d)")
JS_CATCH_RETURN_RE = re.compile(r"catch\s*(\(\s*[\w$]*\s*\))?\s*\{\s*return\b")
NUM_RE = re.compile(r"(?<![\w.])-?\d+(\.\d+)?(?![\w.])")
STR_RE = re.compile(r"'([^'\\\n]{3,80})'|\"([^\"\\\n]{3,80})\"")
CONDITION_RE = re.compile(r"^\s*(if|elif|else\s+if|case|when|match)\b|==|!=|===|!==|\bin\s*[\(\[\{]|\?\s*[^:]+:")
RETURN_LITERAL_RE = re.compile(r"^\s*return\s+(-?\d+(\.\d+)?|'[^']*'|\"[^\"]*\")\s*;?\s*(#.*|//.*)?$")
TRIVIAL_NUMS = {str(n) for n in range(-1, 11)} | {"0.0", "1.0", "100", "0.5", "2.0", "10.0", "100.0", "1000"}
TRIVIAL_STRS = {"utf-8", "utf8", "true", "false", "none", "null", "name", "id", "key", "value", "type", "data", "test"}


# ---------------------------------------------------------------- git access

def git(args, repo, check=True):
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git %s failed" % " ".join(args))
    return proc.stdout


def read_file(repo, path):
    try:
        with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return ""


def parse_diff(text):
    files = {}
    cur = None
    old_ln = new_ln = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            cur = None
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("+++ "):
            path = line[4:]
            if path.startswith("b/"):
                path = path[2:]
            cur = files.setdefault(path, {"added": [], "removed": []}) if path != "/dev/null" else None
            continue
        if line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if m:
                old_ln, new_ln = int(m.group(1)), int(m.group(2))
            continue
        if cur is None:
            continue
        if line.startswith("+"):
            cur["added"].append((new_ln, line[1:]))
            new_ln += 1
        elif line.startswith("-"):
            cur["removed"].append((old_ln, line[1:]))
            old_ln += 1
    return files


def collect_changes(repo, base):
    status = {}
    for row in git(["diff", "--name-status", "-M", base], repo).splitlines():
        parts = row.split("\t")
        if len(parts) >= 2:
            code = parts[0][0]
            path = parts[-1]
            status[path] = code
            if code == "D":
                status[path] = "D"
    diff_text = git(["diff", "--no-color", "--no-ext-diff", "--unified=0", "-M", base], repo)
    files = parse_diff(diff_text)
    # deleted files: capture removed lines too
    deleted_text = git(["diff", "--no-color", "--no-ext-diff", "--unified=0", "--diff-filter=D", base], repo)
    for block in re.split(r"(?=^diff --git )", deleted_text, flags=re.M):
        m = re.match(r"diff --git a/(\S+) b/", block)
        if m:
            removed = [(i + 1, l[1:]) for i, l in enumerate(
                [l for l in block.splitlines() if l.startswith("-") and not l.startswith("---")])]
            files[m.group(1)] = {"added": [], "removed": removed}
    for path in git(["ls-files", "--others", "--exclude-standard"], repo).splitlines():
        if IGNORE_PATH_RE.search(path + "/") or IGNORE_PATH_RE.search(path):
            continue
        status[path] = "A"
        content = read_file(repo, path)
        files[path] = {"added": [(i + 1, l) for i, l in enumerate(content.splitlines())], "removed": []}
    # gitignored data files created after the base commit (e.g. a made-up export in data/)
    try:
        base_time = int(git(["log", "-1", "--format=%ct", base], repo).strip() or 0)
    except RuntimeError:
        base_time = 0
    for path in git(["ls-files", "--others", "--ignored", "--exclude-standard"], repo).splitlines():
        if not DATA_EXT_RE.search(path) or IGNORE_PATH_RE.search(path) or path in files:
            continue
        try:
            if os.path.getmtime(os.path.join(repo, path)) > base_time:
                status[path] = "A"
                files[path] = {"added": [], "removed": [], "ignored": True}
        except OSError:
            pass
    for path in files:
        status.setdefault(path, "M")
    return files, status


def test_literals(repo, base, files, status):
    """Literal values used in test files (base and current versions)."""
    nums, strs = set(), set()
    tracked = git(["ls-files"], repo).splitlines()
    paths = {p for p in tracked if is_test(p)} | {p for p in files if is_test(p)}
    for path in paths:
        texts = [read_file(repo, path)]
        if status.get(path) in ("M", "D", "R"):
            texts.append(git(["show", "%s:%s" % (base, path)], repo, check=False))
        for text in texts:
            for m in NUM_RE.finditer(text):
                if m.group(0) not in TRIVIAL_NUMS:
                    nums.add(m.group(0))
            for m in STR_RE.finditer(text):
                s = m.group(1) or m.group(2)
                if s.lower() not in TRIVIAL_STRS and not s.startswith(("test", "tests/")):
                    strs.add(s)
    return nums, strs


# -------------------------------------------------------------------- checks

class Findings:
    def __init__(self):
        self.items = []

    def add(self, sev, code, path, line, msg, snippet=""):
        self.items.append({"severity": sev, "code": code, "file": path, "line": line,
                           "message": msg, "snippet": snippet.strip()[:160]})


def assert_key(text):
    """Left-hand side of an assertion, used to pair removed/added assertions."""
    t = text.strip()
    m = re.search(r"==|!=|>=|<=|(?<![-=])>|<|\sis\s|\.toBe\(|\.toEqual\(|\.toStrictEqual\(|\.to\w+\(|assert\w*\(|,", t)
    if m:
        return re.sub(r"\s+", "", t[:m.start()])
    return None


def check_tests(path, change, code, out):
    added, removed = change["added"], change["removed"]
    if code in ("M", "D", "R"):
        verb = "deleted" if code == "D" else "modified"
        out.add("HIGH", "TEST-EDIT", path, None,
                "existing test file %s (+%d/-%d lines). Allowed only if the user asked." % (verb, len(added), len(removed)))
    for ln, text in added:
        if SKIP_RE.search(text):
            out.add("HIGH", "TEST-SKIP", path, ln, "skip/xfail/only marker added", text)
        elif WEAK_ASSERT_RE.search(text):
            out.add("MEDIUM", "TEST-WEAK", path, ln, "weak assertion added (does it test behaviour?)", text)
    rem_asserts = [(ln, t) for ln, t in removed if ASSERT_RE.search(t)]
    add_asserts = [(ln, t) for ln, t in added if ASSERT_RE.search(t)]
    paired = set()
    add_by_key = {}
    for ln, t in add_asserts:
        k = assert_key(t)
        if k:
            add_by_key.setdefault(k, []).append((ln, t))
    for ln, t in rem_asserts:
        k = assert_key(t)
        if k and k in add_by_key:
            new_ln, new_t = add_by_key[k].pop(0)
            if not add_by_key[k]:
                del add_by_key[k]
            paired.add(new_ln)
            if re.sub(r"\s+", "", t) != re.sub(r"\s+", "", new_t):
                out.add("HIGH", "TEST-EXPECT", path, new_ln, "expected value changed: %s  ->  %s" % (t.strip(), new_t.strip()))
    unpaired_removed = len(rem_asserts) - len(paired)
    unpaired_added = len(add_asserts) - len(paired)
    if code != "A" and unpaired_removed > unpaired_added:
        out.add("HIGH", "TEST-ASSERT-REMOVED", path, None,
                "%d assertion(s) removed, %d added" % (unpaired_removed, unpaired_added))


def check_python_excepts(path, added, out):
    by_ln = dict(added)
    for ln, text in added:
        m = PY_EXCEPT_RE.match(text)
        if not m:
            continue
        indent, exc, inline = len(m.group(1)), (m.group(2) or "").strip(), m.group(4).strip()
        bound = (m.group(3) or "").replace("as", "", 1).strip()
        em = re.match(r"^(.*?)\s+as\s+(\w+)$", exc)
        if em:
            exc, bound = em.group(1).strip(), em.group(2)
        body = [inline] if inline else []
        nxt = ln + 1
        while nxt in by_ln and (not by_ln[nxt].strip() or len(by_ln[nxt]) - len(by_ln[nxt].lstrip()) > indent):
            if by_ln[nxt].strip():
                body.append(by_ln[nxt].strip())
            nxt += 1
        joined = " ".join(body)
        if re.search(r"\braise\b", joined):
            continue
        broad = bool(BROAD_EXC_RE.match(exc)) or exc == ""
        io_like = bool(IO_EXC_RE.search(exc))
        logs = bool(re.search(r"\b(log(ger|ging)?\.\w+|warn(ings)?\.\w+|print\()", joined))
        swallows = (not body) or bool(re.search(r"^(pass|continue|\.\.\.)$|\breturn\b|=", joined)) or joined in ("pass",)
        if not swallows:
            continue
        label = exc or "bare except"
        if bound and re.search(r"\b%s\b" % re.escape(bound), joined):
            out.add("MEDIUM", "SWALLOW", path, ln,
                    "%s is recorded and execution continues: confirm the failure reaches the caller "
                    "(reject file, error list, log) and is reported" % label, text + " | " + joined)
            continue
        if broad or io_like:
            sev = "MEDIUM" if logs else "HIGH"
            out.add(sev, "SWALLOW", path, ln,
                    "%s caught and execution continues with a default%s. Is the failure visible to the caller?"
                    % (label, " (logged)" if logs else ""), text + " | " + joined)
        else:
            out.add("MEDIUM", "SWALLOW", path, ln,
                    "%s mapped to a default value; make sure the spec asks for that" % label, text + " | " + joined)


def check_source(path, change, nums, strs, out):
    added = change["added"]
    if path.endswith(".py"):
        check_python_excepts(path, added, out)
    for ln, text in added:
        stripped = text.strip()
        if not stripped:
            continue
        if TEST_ENV_RE.search(text):
            out.add("HIGH", "TEST-AWARE", path, ln, "production code reads tests or detects the test environment", text)
        if JS_EMPTY_CATCH_RE.search(text):
            out.add("HIGH", "SWALLOW", path, ln, "empty catch / catch returning a constant", text)
        elif JS_CATCH_RETURN_RE.search(text):
            out.add("MEDIUM", "SWALLOW", path, ln, "catch block returns instead of rethrowing", text)
        if PLACEHOLDER_RE.search(text):
            out.add("MEDIUM", "PLACEHOLDER", path, ln, "mock/placeholder/fallback wording in production code", text)
        if TODO_RE.search(text):
            out.add("MEDIUM", "TODO", path, ln, "TODO/FIXME in changed code: unfinished work must be reported", text)
        floats = re.findall(r"(?<![\w.])\d+\.\d+(?![\w.])", text)
        if len(floats) >= 3 and (":" in text or "=" in text):
            out.add("MEDIUM", "HARDCODED-TABLE", path, ln, "hardcoded numeric table: is this from a real source?", text)
        if stripped.startswith(("#", "//", "*")):
            continue
        lit_hits = [m.group(0) for m in NUM_RE.finditer(text) if m.group(0) in nums]
        lit_hits += [s for s in strs if ("'%s'" % s) in text or ('"%s"' % s) in text]
        if lit_hits and CONDITION_RE.search(text):
            out.add("MEDIUM", "SPECIAL-CASE", path, ln,
                    "condition on value(s) %s that also appear in tests: possible special-casing" % ", ".join(sorted(set(lit_hits))[:4]), text)
        elif lit_hits and RETURN_LITERAL_RE.match(text):
            out.add("MEDIUM", "SPECIAL-CASE", path, ln,
                    "returns literal %s that also appears in tests" % ", ".join(sorted(set(lit_hits))[:4]), text)


def check_suppression(path, change, out):
    removed_cov = [float(m.group(2)) for _, t in change["removed"] for m in [COVERAGE_RE.search(t)] if m]
    for ln, text in change["added"]:
        if SUPPRESS_HIGH_RE.search(text):
            out.add("HIGH", "SUPPRESS", path, ln, "failure suppressed (check can no longer fail)", text)
        elif SUPPRESS_MED_RE.search(text):
            out.add("MEDIUM", "SUPPRESS", path, ln, "check silenced or narrowed: justify or remove", text)
        m = COVERAGE_RE.search(text)
        if m and removed_cov and float(m.group(2)) < max(removed_cov):
            out.add("HIGH", "SUPPRESS", path, ln, "coverage threshold lowered from %s" % max(removed_cov), text)


def run_audit(repo, base):
    files, status = collect_changes(repo, base)
    nums, strs = test_literals(repo, base, files, status)
    out = Findings()
    for path in sorted(files):
        if IGNORE_PATH_RE.search(path) or os.path.realpath(os.path.join(repo, path)) == SELF_PATH:
            continue
        change, code = files[path], status.get(path, "M")
        if is_test(path):
            check_tests(path, change, code, out)
        elif is_code(path):
            check_source(path, change, nums, strs, out)
        if code == "A" and DATA_EXT_RE.search(path) and not is_test(path):
            out.add("MEDIUM", "NEW-DATA", path, None,
                    "new data file outside tests%s: where did this data come from? Made-up data must not stand in for a real source"
                    % (" (gitignored, so it will not show in git diff)" if change.get("ignored") else ""))
        if is_test(path) or is_code(path) or CONFIG_PATH_RE.search(path) or path.endswith((".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini")):
            check_suppression(path, change, out)
    return files, out


# -------------------------------------------------------------------- output

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="HEAD", help="ref to compare against (default: HEAD)")
    ap.add_argument("--repo", default=".", help="repository path (default: current directory)")
    ap.add_argument("--json", action="store_true", help="print JSON")
    args = ap.parse_args(argv)
    try:
        root = git(["rev-parse", "--show-toplevel"], args.repo).strip()
        git(["rev-parse", "--verify", args.base], root)
    except (RuntimeError, FileNotFoundError) as exc:
        print("audit_diff: %s" % exc, file=sys.stderr)
        return 2
    files, out = run_audit(root, args.base)
    order = {"HIGH": 0, "MEDIUM": 1}
    items = sorted(out.items, key=lambda f: (order.get(f["severity"], 2), f["file"], f["line"] or 0))
    high = sum(f["severity"] == "HIGH" for f in items)
    med = sum(f["severity"] == "MEDIUM" for f in items)
    if args.json:
        print(json.dumps({"base": args.base, "files_changed": len(files), "high": high, "medium": med, "findings": items}, indent=2))
    else:
        print("truegreen audit: %d file(s) changed vs %s" % (len(files), args.base))
        if not items:
            print("No findings. Still run the tests fresh before reporting.")
        for f in items:
            loc = f["file"] + (":%d" % f["line"] if f["line"] else "")
            print("%-6s %-20s %s\n       %s" % (f["severity"], f["code"], loc, f["message"]))
            if f["snippet"]:
                print("       > %s" % f["snippet"])
        print("\nSummary: %d HIGH, %d MEDIUM." % (high, med))
        if high:
            print("HIGH findings must be reverted, or kept only because the user asked and listed in your report.")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
