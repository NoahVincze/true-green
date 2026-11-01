# truegreen

An agent skill that keeps green checks honest. It triggers before an agent
claims work is done, and whenever a test, build, data file or external call
fails and the agent is tempted to edit or skip a test, special-case inputs,
invent data, add a silent fallback or swallow an error. It gives the agent a
legitimate way out (report `BLOCKED` or `DONE WITH CAVEATS`) and a script that
audits the diff for those patterns.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add NoahVincze/true-green
/plugin install truegreen@truegreen
```

Any other agent that reads skills: copy `skills/truegreen/` into its skills
directory, e.g. `~/.claude/skills/truegreen/`.

## Layout

```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   lets this repo be added as a marketplace
skills/truegreen/SKILL.md         the skill (frontmatter + instructions)
skills/truegreen/scripts/         audit_diff.py, the diff auditor (stdlib only)
tests/                            unit tests for the audit script, one scenario per file in audit_cases/
evals/                            agent evals with vs. without the skill (see evals/README.md)
```

Each skill lives in its own `skills/<name>/` folder whose name matches the
`name` in its frontmatter.

## Audit script

From the root of the repository being checked:

```
python3 path/to/skills/truegreen/scripts/audit_diff.py              # vs. HEAD
python3 path/to/skills/truegreen/scripts/audit_diff.py --base main  # vs. a branch
python3 path/to/skills/truegreen/scripts/audit_diff.py --json
```

Exit code 1 means at least one HIGH finding.

## Development

Everything is standard-library Python 3.10+.

```
python -m unittest discover -s tests    # audit script tests
python evals/run.py check               # eval cases and grader, no model calls
claude plugin validate .                # plugin and marketplace manifests
```

CI runs all three. Agent evals cost money and run only by hand:
`python evals/run.py run` (see [evals/README.md](evals/README.md)).

## License

MIT, see [LICENSE](LICENSE).
