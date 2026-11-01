# Changelog

## Unreleased

- Codex plugin manifest (`.codex-plugin/plugin.json`) and a portable Agent
  Plugins manifest (`plugin.json`); README install steps for Codex and, via
  `npx skills`, Cursor, Kimi Code, OpenClaw and others.
- The audit script as a GitHub Action (`action.yml`), a pre-commit hook
  (`.pre-commit-hooks.yaml`) and a `truegreen-audit` command (`pyproject.toml`).
- Tests that the version and name match across all manifests.
- README: before/after image, install near the top, Contributing section.

- `audit_diff.py` skips its own file, so a vendored copy does not flag its own patterns.
- Tests for the audit script: 19 scenario files in `tests/audit_cases/` plus CLI tests.
- Reproducible evals: 6 cases with hidden tests, reference solutions and cheat
  overlays, and `evals/run.py` to run and grade agents with and without the skill.
- GitHub Actions CI: tests and eval checks on Linux, Windows and macOS, plugin validation.

## 0.1.0 - 2026-11-01

- First packaged release: `truegreen` skill with `scripts/audit_diff.py`.
- Repo laid out as a Claude Code plugin and marketplace (`.claude-plugin/`,
  `skills/<name>/`).
- MIT license.
