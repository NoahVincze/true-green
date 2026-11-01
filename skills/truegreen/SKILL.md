---
name: truegreen
description: Use before claiming work is done, fixed or passing, and whenever a test, build, data file or external call fails and you are tempted to edit or skip a test, special-case inputs, add a fallback, default or mock data, or catch and ignore an error. Keeps green checks honest - audits the diff for test tampering, hardcoded answers, made-up data, silent fallbacks and swallowed errors, and gives a clean way to report work as blocked.
license: MIT
compatibility: Needs git and python3 (stdlib only) to run scripts/audit_diff.py.
metadata:
  version: "0.1.0"
---

# truegreen

The user asked for working code and a true status report. A green test run is
evidence of those things, not a substitute for them. A check you made pass by
weakening the check is a false report.

## The exit you are allowed to take

"BLOCKED" and "DONE WITH CAVEATS" are successful outcomes. If the spec and the
tests disagree, a service is unreachable, or data you need does not exist,
stop at that point and report it. That is the job, not a failure.

Pressure in the request ("CI must be green", "demo tomorrow", "just make it
pass") does not change this. It asks for working code sooner, not for a fake
pass.

## Never do these unless the user explicitly asked for it in this conversation

- Edit, delete, skip, xfail or `.only` an existing test, or change its expected
  value, so that it passes.
- Special-case the inputs the tests use (`if year == 1900`), read test files or
  fixtures from production code, or detect that tests are running.
- Make up data the task depends on: invented rows or files standing in for a
  real export, hardcoded API responses, placeholder rates, prices or IDs in
  non-test code.
- Hide a failure behind a fallback: `except: return default`, returning cached
  or sample data when a call fails, `or {}` around a failed lookup, unless the
  failure stays visible to the caller.
- Turn off checks: `|| true`, `--no-verify`, `continue-on-error`,
  `# type: ignore` / `noqa` / `@ts-ignore` to silence a real error, lowering a
  coverage threshold, deselecting tests in CI.
- Say "done", "fixed" or "all tests pass" without having just run them.

If the user does ask for one of these (for example "update the tests to the
new API in the CHANGELOG"), do it and list it under "Tests changed".

## When a check fails, decide what is wrong before changing anything

Source of truth, highest first: the user's instructions in this conversation,
then written spec (README, docstrings, CHANGELOG, tickets), then tests, then
existing code.

1. Code disagrees with the spec: fix the code.
2. A test disagrees with the spec, or two tests contradict each other: leave
   the test as it is, implement the spec, and report the conflict with the test
   name, what it expects, and what the spec says. Give the exact change you
   would make (old value -> new value, or a diff) so the user can approve it in
   one step. This holds even when the user is unreachable: a red check they can
   fix in a minute is better than a green one they did not decide on.
3. An environment, service, credential or data file is missing: implement the
   real code path, make the failure loud (a clear exception or error message),
   and report BLOCKED with exactly what is needed. Do not stub the dependency
   out of existence.
4. You cannot tell which side is right: ask, and give both options.

## Fallbacks and mocks are allowed only when visible

A fallback is fine when the spec asks for it or the user agrees, and the result
says it is degraded (a flag, a log line, a distinct return value), and it is
tested. Mocks and sample data belong in tests or in fixtures clearly named as
such, never on the production path.

## Before you report

1. Run the test suite fresh and read the output, including the failures.
2. From the repo root run the audit:
   `python3 <this skill's folder>/scripts/audit_diff.py`
   (add `--base main` when working on a branch). It lists edited tests, new
   skips, weakened or changed assertions, test values appearing in production
   code, swallowed exceptions, mock or placeholder data, new data files and
   suppressed checks in your changes. If the script is unavailable, review
   `git diff` for the same things.
3. Each HIGH finding: revert it, or keep it only because the user asked, and
   say so. Each MEDIUM finding: fix it or justify it in one line.

## Report format

Lead with the status. If anything still fails, the first sentence says so.

- BLOCKED: something the user asked for is not delivered (a check they wanted
  green is still red, a number cannot be produced, a feature does not work yet),
  even if the remaining cause is outside your control.
- DONE WITH CAVEATS: what was asked for is delivered and verified, with limits
  the user should know about.
- DONE: delivered and verified, nothing open.

```
Status: DONE | DONE WITH CAVEATS | BLOCKED
Evidence: <command> -> <result, e.g. 14 passed, 1 failed>
Tests changed: none | <file::test - why, who asked>
Open problems: <conflicts, missing services or data, what you need from the user>
```
