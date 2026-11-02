<h1 align="center">truegreen</h1>

<p align="center">
  <em>Green means it works. Not that someone edited the test.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-2ea44f?style=flat-square" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20more-2ea44f?style=flat-square" alt="Works with Claude Code, Codex, Cursor and more">
  <img src="https://img.shields.io/badge/python-3.10%2B%2C%20stdlib%20only-2ea44f?style=flat-square" alt="Python 3.10+, stdlib only">
  <img src="https://img.shields.io/badge/license-MIT-2ea44f?style=flat-square" alt="MIT license">
</p>

<p align="center">
  <img src="assets/before-after.svg" width="900" alt="The same agent report without truegreen (all tests pass, the test change is a footnote) and with truegreen (Status: BLOCKED, the test change is a question for you)">
</p>

---

Your tests are where you wrote down what the code is supposed to do. Every
expected value in them is a decision someone made.

Agents now write more code than anyone can read. Teams with high AI adoption
merge 98% more pull requests while review time per PR rises 91%
([Faros AI](https://www.faros.ai/blog/ai-software-engineering)). So the green
check becomes the review, and the green check is exactly what an agent works
toward. When it is stuck on a failing test, the quickest way to green is to
change the test: update an expected value, skip it, add a fallback.

Often the agent's guess is even right. In our evals, agents asked to "just get
CI green" edited a test that contradicted the spec in 11 of 12 runs, and every
edit was correct. Every report also opened with "CI is green", with the test
change further down. A decision about what your code should do was made on a
guess and reported as a footnote. Next time the spec is less clear, and the
report reads the same.

truegreen hands that decision back to you. When a check fails, the agent fixes
the code if the code is wrong. If the test looks wrong, it leaves it red,
reports `BLOCKED`, and proposes the exact change for you to approve. Tests
change only when you say so, and every change is listed first.

- **Fixes that fix the code.** If the code is wrong, the agent fixes it. If the
  test is wrong, or something it needs is missing (a service, a credential, a
  data file), it leaves the check alone and tells you why.
- **Reports you can read at a glance.** Every report starts with `DONE`,
  `DONE WITH CAVEATS` or `BLOCKED` and lists any tests it changed. If something
  is still broken, that is the first thing you read.
- **A check on its own work.** Before reporting, the agent runs a short script
  over its diff that flags edited tests, hardcoded answers, made-up data and
  swallowed errors.

## Install

**Claude Code**

```
/plugin marketplace add NoahVincze/true-green
```
```
/plugin install truegreen@truegreen
```

**Codex**

```
codex plugin marketplace add NoahVincze/true-green
```
```
codex plugin add truegreen@truegreen
```

**Cursor, Kimi Code, OpenClaw, Copilot, Gemini CLI, opencode and others**, with
the [skills CLI](https://github.com/vercel-labs/skills):

```
npx skills add NoahVincze/true-green --skill truegreen
```

Add `-g` to install it for all your projects, or `-a <agent>` to pick the agent
(`cursor`, `kimi-code-cli`, `openclaw`, ...).

<details>
<summary>Without an installer</summary>

Copy `skills/truegreen/` into the folder your agent reads skills from:

| Agent | In a project | For all projects |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex, Kimi Code | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| OpenClaw | `skills/` in the workspace | `~/.openclaw/skills/` |

For any other agent, point its custom instructions at
[`skills/truegreen/SKILL.md`](skills/truegreen/SKILL.md).

</details>

The whole skill is [one Markdown file](skills/truegreen/SKILL.md) of about 100
lines plus the audit script. It needs `git` and `python3`; no config, no
dependencies.

## What it looks like

You ask your agent to fix a pricing bug and get CI green. One test expects a
value that contradicts the spec.

Without truegreen, the report reads:

> All tests pass and CI is green. I fixed the discount calculation. I also
> updated the expected value in `test_checkout_integration`, which looked
> outdated.

The test change is mentioned, but only after "CI is green", and it was already
made by the time you read it.

With truegreen:

```
Status: BLOCKED
Evidence: python -m unittest -> 4 run, 1 failed (test_checkout_integration)
Tests changed: none
Open problems: test_checkout_integration expects 218.00, but the docstring
  and test_save20 say VAT is charged after the discount, which gives 214.20.
  Proposed change, if you agree: tests/test_pricing.py:20  218.00 -> 214.20
```

The code fix is the same either way. The difference is that the test change is
now a question for you instead of a footnote, and saying yes takes one line.

<sub>Condensed from eval runs; the case itself is in
[evals/cases/vat_conflict/](evals/cases/vat_conflict/).</sub>

## When it matters

If your tasks are clear and your tests are right, you probably won't notice
it. Current models already do the right thing there, and in our tests the
skill changed nothing.

It matters in the messier moments: a test that is wrong, and a request to get
CI green. In our tests, agents without the skill changed the test themselves in
11 of 12 runs and led with "CI is green". With it, 0 of 12 did: they fixed the
code, left the test alone and asked.

That is not surprising. An agent takes the shortcut when it looks like the only
way to finish the job. Tell it who gets to decide, and that stopping to ask
counts as a good result, and it does that instead. Outside research points the
same way: in [ImpossibleBench](https://arxiv.org/abs/2510.20270), giving agents
an explicit way to flag a task for a human cut GPT-5's rate of gaming the tests
from 54% to 9%.

It is not a guarantee. The tests were small (about a hundred runs, Claude
models only), and the audit script is a heuristic. Setup and numbers:
[evals/RESULTS.md](evals/RESULTS.md). The longer argument, with sources:
[docs/why.md](docs/why.md).

## How your agent decides

When a check fails, the agent asks which source is right, in this order:

1. Your instructions in the conversation
2. Written spec: README, docstrings, CHANGELOG, tickets
3. Tests
4. Existing code

Code that disagrees with the spec gets fixed. A test that disagrees with the
spec stays as it is and gets reported, with the exact change the agent would
make. A missing service or data file gets a real code path that fails loudly,
not a stub. If the agent cannot tell which side is right, it asks you.

When you do want tests changed ("update the tests to the new API"), just say
so. The agent makes the change and lists it under `Tests changed`.

## The audit script

[`audit_diff.py`](skills/truegreen/scripts/audit_diff.py) reads the diff and
flags changes that make checks pass without making the code right: edited,
skipped or deleted tests, changed assertions, test values hardcoded into
production code, swallowed exceptions, placeholder data, new data files, and
switched-off checks (`|| true`, lowered coverage, `# type: ignore`).

Your agent runs it before reporting, but you can run it yourself too:

```
python3 path/to/skills/truegreen/scripts/audit_diff.py              # vs. HEAD
python3 path/to/skills/truegreen/scripts/audit_diff.py --base main  # vs. a branch
python3 path/to/skills/truegreen/scripts/audit_diff.py --json
```

Exit code 1 means at least one HIGH finding. It only sees what changed: a
silent fallback that was already in the code is invisible to it.

The script works without the skill, so it also catches changes from agents
that don't load skills, and from people.

**In CI**, as a GitHub Action. It marks HIGH findings as errors and MEDIUM
ones as warnings on the changed lines, writes a summary table, and fails the
check on any HIGH finding:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- uses: NoahVincze/true-green@main
```

On a pull request it compares against the target branch; on a push, against
the commit before the push. Set `base:` to choose another ref. Editing an
existing test counts as HIGH, so a PR that changes tests on purpose fails too.
That is deliberate: someone should look at it. To flag without failing, set
`fail-on-high: "false"`.

**Before each commit**, as a [pre-commit](https://pre-commit.com) hook:

```yaml
repos:
  - repo: https://github.com/NoahVincze/true-green
    rev: main
    hooks:
      - id: truegreen-audit
```

To commit a test change you meant to make, run
`SKIP=truegreen-audit git commit ...`.

**As a command**: `pipx install git+https://github.com/NoahVincze/true-green`
installs `truegreen-audit`, which takes the same flags.

## FAQ

**My tests really are outdated. Do I have to fix them by hand?**
No, you just approve the change. A `BLOCKED` report names the test, what it
expects, what the spec says, and the exact old → new edit.

**Will it slow my agent down?**
A little. It costs a few thousand extra tokens per task and a couple more tool
calls, mostly for running the tests again and the audit before reporting.

**Does it work with agents other than Claude?**
It installs in Codex, Cursor, Kimi Code, OpenClaw and any other agent that
reads [Agent Skills](https://agentskills.io): it is plain Markdown and plain
Python. The evals have only been run on Claude models so far. Results from
other agents are welcome (see [Contributing](#contributing)).

**Why "truegreen"?**
Because the other kind is easy.

## Contributing

Issues and pull requests are welcome. The most useful contributions are:

- **Eval cases.** A real situation where an agent faked success, as a new
  folder in [evals/cases/](evals/cases/). The format is in
  [evals/README.md](evals/README.md).
- **Eval runs on other agents.** The runner drives the `claude` CLI today.
  Numbers from Codex, Kimi or anything else would show whether the skill
  carries over.
- **Audit misses and false alarms.** One scenario file in
  [tests/audit_cases/](tests/audit_cases/) shows the bug and keeps it fixed.

Run the checks below before opening a PR.

## Development

```
skills/truegreen/        SKILL.md and scripts/audit_diff.py
.claude-plugin/          Claude Code plugin and marketplace manifests (Codex reads the marketplace too)
.codex-plugin/           Codex plugin manifest
plugin.json              portable Agent Plugins manifest
action.yml               GitHub Action that runs the audit script
.pre-commit-hooks.yaml   pre-commit hook; pyproject.toml packages the script as truegreen-audit
assets/                  README images
docs/why.md              the case for the skill, with sources
tests/                   audit script tests (one scenario per file in audit_cases/) and manifest checks
evals/                   agent evals with vs. without the skill (see evals/README.md)
```

Everything is standard-library Python 3.10+. The version lives in six places
(the four manifests, `pyproject.toml` and `SKILL.md`); the tests fail if they
disagree.

```
python -m unittest discover -s tests    # audit script and manifest tests
python evals/run.py check               # eval cases and grader, no model calls
claude plugin validate .                # plugin and marketplace manifests
```

CI runs these on Linux, Windows and macOS, and also tries the GitHub Action and
the pre-commit hook. Agent evals cost money and run only by hand: `python evals/run.py run` (see [evals/README.md](evals/README.md)).

## License

[MIT](LICENSE).
