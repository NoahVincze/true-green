# truegreen

An agent skill that keeps green checks honest. It triggers before an agent
claims work is done, and whenever a test, build, data file or external call
fails and the agent is tempted to edit or skip a test, special-case inputs,
invent data, add a silent fallback or swallow an error. It gives the agent a
legitimate way out (report `BLOCKED` or `DONE WITH CAVEATS`) and a script that
audits the diff for those patterns.

## Layout

```
SKILL.md                 the skill (frontmatter + instructions)
scripts/audit_diff.py    diff auditor the skill tells the agent to run (stdlib only)
eval/RESULTS.md          what was tested so far and what it showed
```

## Install

Copy `SKILL.md` and `scripts/` into your agent's skills directory, e.g.
`~/.claude/skills/truegreen/`.

## Audit script

From the root of the repository being checked:

```
python3 path/to/truegreen/scripts/audit_diff.py              # vs. HEAD
python3 path/to/truegreen/scripts/audit_diff.py --base main  # vs. a branch
python3 path/to/truegreen/scripts/audit_diff.py --json
```

Exit code 1 means at least one HIGH finding.
