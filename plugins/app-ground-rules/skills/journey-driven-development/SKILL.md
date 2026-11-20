---
name: journey-driven-development
description: How Alexander's app projects specify, test and monitor behaviour from user journeys — journey specs with SHALL/SHALL NOT requirements and stable scenario IDs, a flow table plus Mermaid diagram per journey, thresholds that become OpenSLO objectives, OpenTelemetry journey events, tests named after scenarios, delta changes after release, and the Goal QA loop with UX and security reviewers. Use when writing or changing a journey spec, flow table, threshold or SLO, naming a test or runtime event, reviewing whether spec and code agree, working a Goal, or setting this process up in a new repo ("set up journey-driven development here").
---

# Journey-driven development

Read the `app-ground-rules` skill first: its stages decide how much of this applies. The rules below apply in full from the **release** stage; in explore and beta apply only what its stage table requires. A project's AGENTS.md wins on conflict and may name its own differences; it links here instead of repeating these rules.

## 1. Aim

Desired, undesired and changing behaviour is described well enough that acceptance tests, runtime monitoring and anomaly detection follow from it. Journey specs are refined over the whole life of the system; the goal is automated software creation and zero-touch operations.

- The journey spec is the only place where a human describes behaviour. Tests, runtime events, the flow table, SLOs and release analysis are derived from it or checked against it.
- **The spec wins.** When spec and code disagree, change the code.
- **Only specified code ships.** Code that serves no specified function is removed with its tests; version control keeps it.
- **Who may change a spec:** only Alexander decides its content. Agents write into a spec only clauses he decided; every other change, reviewers' included, is a proposal in the issue.

## 2. Files

Paths are set in `journeys.toml` at the repo root (template in `templates/journeys.toml`); the defaults are:

- `docs/journeys/README.md` — the one ordered list of all journeys, with each journey's stage and release. Read it before planning work; update it in the same change that adds, renames, reorders or moves a journey.
- `docs/journeys/JNN-<name>.md` — one file per journey (template `templates/journey.md`).
- `docs/threat-models/JNN-<name>.threat.md` — from the release stage (template `templates/threat-model.md`).
- `docs/mental-model.md` — the glossary every journey uses.

## 3. Writing a journey spec

- **Provenance** after every requirement or scenario that is not obvious: *(Alexander, <date>)*, *(Alexander, Qn)*, *(code)* for behaviour taken from today's code, *(proposal)* for anything not yet decided.
- **Desired behaviour:** `### Requirement: JNN.Sn <title>` with one SHALL sentence, then `#### Scenario: <name>` with WHEN / THEN / AND bullets.
- **Undesired behaviour:** `### Requirement: JNN.Un <title>` with a SHALL NOT sentence and scenarios saying what must never happen and what the user sees instead. Only the sources in section 1 of `app-ground-rules` may add one.
- IDs are stable and shared by specs, contracts, tests and events. Never reuse a removed ID.
- **Thresholds:** every non-functional requirement is a measurable number in a scenario or in the journey's `## Non-functional` section. A number not yet known is written "threshold open, measure first". Each threshold becomes an OpenSLO objective (section 6).
- **Flow:** each journey has a `## Flow` section with a table `| From | To | When | Time budget |`, using the pseudo-states `start`, `done` and `abandoned`. A row into `done` names, in "When", the scenario that ends the pass. Time budgets are written `45 s`, `2 min` or `1 h`, or `—`. A Mermaid `flowchart` above the table shows the same steps in the same order; change both in the same edit.
- **Changes:** edit a journey in place until its first release. After that, every change to a released requirement is a delta in a section `## Change: <title>` with ADDED, MODIFIED and REMOVED requirements, merged into the requirements when the change is released. A MODIFIED or REMOVED delta needs "During the change" scenarios: what happens to work in flight (drafts, open sessions, sign-ins) while a user moves from version N to N+1.

## 4. Tests trace to scenarios

- A test covers a scenario when its display name starts with `"<ID> <scenario name>: <what it checks>"`, for example `@Test("J02.S3 Company sign-in: region defaults to Frankfurt")` or `test('J02.U1 Key never logged: …')`.
- Give a test a scenario ID only when it fully checks a THEN or AND clause.
- Run `python3 -I scripts/journeys/check-journey-coverage.py` after changing tests or journeys; it fails on a test that names an unknown scenario. A Goal is done when `--release --scope <its steps>` passes; before a milestone, `--release` without scope needs a test for every scenario.

## 5. Runtime events

- Every scenario, desired and undesired, emits a runtime event when it happens. Test and event carry the same ID, and the test that carries the ID also checks that the event is emitted.
- OpenTelemetry and open standards only. Use the semantic-convention name where one exists; read the [current conventions](https://opentelemetry.io/docs/specs/semconv/) before choosing one. The event is a log record named `journey.scenario` with:
  - `journey.id` (`J02`), `journey.step` (`J02.S3` or `J02.U1`), `journey.scenario` (the scenario name), `journey.outcome` (`desired`, `undesired` or `abandoned`);
  - the app version and an ID that correlates one pass, named after the semantic conventions (`service.version`, `session.id`).
- Events never contain secrets, file contents or personal data.
- An event whose scenario is in no journey file is written as `journey.scenario.rejected` with a fixed text and no attributes, never dropped silently.
- **Local first:** while building, events go to a local OTLP/JSON lines file. `python3 -I scripts/journeys/check-journey-flow.py <events.jsonl> --journey JNN` checks them against the flow table. In the cloud, send traces, metrics and logs to the backend the project chose.

## 6. Expectations and anomalies

- From the release stage, thresholds become [OpenSLO](https://openslo.com) objectives per step, kept next to the journey or under `slo/`; each names the step ID.
- An anomaly is a deviation from the desired flow: a transition not in the flow table, a skipped step, a step over its time budget, or any undesired event.
- Every anomaly is either a defect, which becomes a red test carrying the scenario ID, or a gap in the spec, which becomes a question for Alexander.
- Build nothing beyond checking events against the flow table without a Goal from Alexander.

## 7. Releases

- Release analysis follows from the deltas: unchanged steps stay at their baseline; MODIFIED steps are measured against their new thresholds; events of REMOVED steps disappear and events of ADDED steps appear; "During the change" scenarios hold only while the rollout runs.
- An anomaly always creates a ticket. A rollout stops automatically only for a spec-anchored violation caused by the release; a human decides everything else.

## 8. Working a Goal

The rules apply in every harness (Claude Code, Agent SDK, Codex, OpenCode, Cursor). Where a harness lacks a mechanism named here, follow the rule by hand and say so in the Goal's issue. A Goal is one journey slice with a budget, one acceptance result and one review artifact (the `goal` skill where available).

- **Budget** covers the session, every subagent and reviewer. The orchestrator may pick a cheaper model to stay within it. Measure with `python3 -I scripts/journeys/goal-cost.py <session.jsonl>` in Claude Code or the Agent SDK; elsewhere report the harness's figure, or "cost unmeasured". At 80 and 95 percent act as section 5 of `app-ground-rules` says; at 95 percent also write `.claude-continue-here.md`.

1. **Intake.** Name the scenarios in scope. Ask about the operating environment, what would bother the user in the UI, the threshold for each non-functional requirement, and permissions needed later (native apps, screenshots).
2. **Spec check.** Compare the spec with today's code; log each contradiction as an assumption.
3. **Red tests** carrying the scenario IDs, the event check included; watch them fail.
4. **Build** test-driven until green.
5. **QA loop.** Explore: the smoke test. Beta: the checkers, the affected suites and one combined UX and security review of the working flow; a walkthrough only when the UI changed; a fact check only for new dependencies or third-party behaviour. Release: the checkers, the affected suites, a review by the `ux-designer` and the `security-reviewer` agents (`.claude/agents/`; `scripts/journeys/sync-agents.py` renders copies for Codex and OpenCode), a fact check, a walkthrough of the review build, and measured thresholds. A session that cannot see these agents does not fall back to general-purpose ones: it says so in the issue, pushes the branch, and the reviews run in a session that can.
6. **Acceptance.** Alexander tests the review artifact. Each defect becomes a red test with its scenario ID; if no scenario fits, extend the spec first.

**Assumptions.** When a question comes up while building, log question, assumption, reason and impact if wrong in `build/assumptions/<goal>.md` and keep working. At the end apply the revert test of `app-ground-rules` to each: revertible ones go under "Decisions I made" in the PR; only the rest go to Alexander, at most 5 per round, numbered `Qn` (highest existing plus one), each with a recommendation, posted on the Goal's issue and listed in the project's open-questions issue. His answers go into the specs as *(Alexander, Qn)*.

**Long sessions.** Keep `.claude-continue-here.md` current so a new session in any harness can restart from it: at least every 20 minutes of work and before stopping.

## 9. Setting it up in a new repo

Run `python3 -I <this skill's folder>/scripts/bootstrap.py --root <repo>`. It copies, without overwriting existing files: the checker scripts to `scripts/journeys/`, `journeys.toml`, the journey list and one example journey, the threat-model template, and both reviewer agents to `.claude/agents/`. Then:

1. Set the test folders and file patterns in `journeys.toml`.
2. Replace the `<product>` and `<audience>` placeholders in `.claude/agents/*.md`, and run `python3 -I scripts/journeys/sync-agents.py`.
3. Add the snippet in `templates/AGENTS-snippet.md` to the repo's AGENTS.md.
4. Add `python3 -I scripts/journeys/check-journey-coverage.py` to CI.
