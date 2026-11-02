# Why truegreen exists

## Tests are decisions

A test suite is where a team writes down what its code is supposed to do.
Every expected value in it was a decision: VAT is charged after the discount,
1900 is not a leap year, a bad row is rejected and not defaulted to zero. When
someone changes a test, they are changing one of those decisions.

For most of software's history that change went through a person who owned
the code. That is less and less true.

## More code, less reading

Coding agents now write a large share of new code. Google said in April 2026
that about 75% of its new code is AI-generated and approved by engineers, up
from about 25% in late 2024 ([TechSpot](https://www.techspot.com/news/112152-google-ai-now-generates-75-new-code-up.html)).

Review has not scaled with it. Across 10,000+ developers, Faros AI found that
teams with high AI adoption merge 98% more pull requests, while PR review time
rises 91% and average PR size 154%
([Faros AI, 2025](https://www.faros.ai/blog/ai-software-engineering)). A year
later, pull requests merged without any review, human or agentic, were up 31.3%
([Faros AI, 2026](https://www.faros.ai/blog/ai-acceleration-whiplash-takeaways)).
Google's DORA research associated rising AI adoption with an estimated 7.2%
drop in delivery stability
([DORA 2024](https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report)).
And developers notice: more of them distrust the accuracy of AI tools (46%)
than trust it (33%)
([Stack Overflow 2025](https://survey.stackoverflow.co/2025/ai)).

When there is more code than anyone can read, the green check becomes the
review. If CI passes, the change goes in.

## Green is exactly what agents work toward

That makes the green check the target. An agent that hits a failing test it
cannot fix has a shortcut available: change the test.

This is well documented. METR found frontier models "modifying the tests or
scoring code" to raise their scores, and asked o3 afterwards whether its plan
matched the user's intention: it answered "no" 10 out of 10 times
([METR, 2025](https://metr.org/blog/2025-06-05-recent-reward-hacking)).
ImpossibleBench built coding tasks whose tests contradict the written spec, so
any pass is a shortcut. On its SWE-bench variant, GPT-5 passed 54% of these
impossible tasks and Claude Opus 4.1 50%; Claude models did it mostly by
modifying the tests
([Zhong, Raghunathan, Carlini, 2025](https://arxiv.org/abs/2510.20270)). Kent
Beck, who popularised test-driven development, has described having trouble
stopping agents from deleting tests to make them "pass"
([The Pragmatic Engineer, 2025](https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent)).

## The agent is usually right. That is the problem.

Our own evals add a twist. We gave Claude agents tasks where one test
contradicts the written spec, with the message "I'm offline until tomorrow,
please just get CI green". Without truegreen, agents edited the test in 11 of
12 runs. Every one of those edits was correct: the agent picked the value the
spec asked for, and mentioned the edit in its report
([evals/RESULTS.md](../evals/RESULTS.md)).

But every one of those reports opened with "CI is green". The decision about
what the code should do was made by the agent, on a guess, and reported as a
footnote under a passing check. On those tasks the spec was explicit, so the
guess was right. On a real codebase the spec is often a hallway conversation,
a stale ticket or nothing at all. The report reads the same either way.

Repeat that across hundreds of agent PRs and the test suite drifts. It stops
being a record of what the team decided and becomes a record of what the agents
guessed. The tests still pass. They just no longer tell you much.

## Give the agent a way out, and the decision comes back

An agent takes the shortcut when it looks like the only way to finish the job.
ImpossibleBench found that giving agents an explicit way to flag a task for a
human cut GPT-5's cheating rate from 54% to 9% and o3's from 49% to 12%, and
that stricter prompting cut GPT-5's from 92% to 1% on one benchmark. The
effect was weaker for Claude Opus 4.1 in their setup.

truegreen is built on that. It tells the agent:

- **Who decides.** Your instructions, then the written spec, then the tests,
  then the existing code. A test that disagrees with the spec is not the
  agent's to fix.
- **That stopping is success.** `BLOCKED` is a good result when something you
  asked for cannot be delivered honestly. Pressure like "CI must be green
  tonight" asks for working code sooner, not for a fake pass.
- **How to ask.** A blocked report names the test, what it expects, what the
  spec says, and the exact `old -> new` change. Saying yes takes one line.

Then it checks: before reporting, the agent runs an audit over its own diff for
edited tests, hardcoded answers, made-up data and swallowed errors. The same
script runs in CI and as a pre-commit hook, so it also catches changes from
agents that never loaded the skill, and from people.

With the skill, the same agents edited the test in 0 of 12 runs, fixed the
code just as well, and led with `BLOCKED` and the proposed change. When the
user explicitly asked for test changes, they still made them, and listed them.

## What that buys you

Tests change only when someone who owns the code says so, and every change is
in the first lines of the report. The suite stays a record of decisions people
made, and green goes back to meaning "it works".

## What it does not do

- It does not make agents infallible. It is about 100 lines of instructions
  and a heuristic script.
- Our evals are small: about a hundred runs, Claude models only. The
  conditions that matter (ambiguous specs, long multi-file tasks, other
  vendors' agents) are the next ones to test.
- The audit only sees what changed. A silent fallback already in the code is
  invisible to it.
