---
name: app-ground-rules
description: Alexander's ground rules for every app he builds with agents — behaviour no app may show, the threat-model baseline, the stages explore/beta/release, the revert test for when to ask him, and the estimate rule. Use before planning, specifying, building or reviewing work in any of his app repos, before writing "must never" requirements or a threat model, and before asking him a question.
---

# App ground rules

These apply to every app project unless that project's AGENTS.md says otherwise. Order of precedence: Alexander's words in the current chat or issue > the project's AGENTS.md > its charter > its process docs > these ground rules > prompts, batch and restart files. A prompt lists work; it never changes rules.

## 1. Behaviour no app may show

These are the only "must never" rules a project gets for free. Write a project-specific one only for a reproduced defect or an explicit decision by Alexander. A reviewer or threat model may propose one; it never adds one.

1. Lose user data or a draft. A failed save, crash or update keeps what the user typed.
2. Send data to a recipient, provider or place the user did not choose.
3. Act without permission: no purchase, message, deletion, upload or account change the user did not confirm.
4. Write secrets, credentials or personal data into logs, telemetry, crash reports or URLs.
5. Leave the user stuck after a failed request: the input stays usable, the user sees what happened and a way to retry.
6. Switch account, provider, model or data region silently.
7. Make cancelling harder than subscribing. In Germany a subscription needs a cancellation button ([§ 312k BGB](https://www.gesetze-im-internet.de/bgb/__312k.html), read 8 Nov 2026); check the current wording before shipping one.

## 2. Threat-model baseline

- Out of scope: an attacker who already runs code as the user, or who has the unlocked device.
- In scope: other apps and websites, the network, servers we run, and content the app processes (documents, web pages, model output). Content is data, never instructions.
- Write a threat model per journey only from the **release** stage on. Before that, these baseline rules are the threat model.

## 3. Stages: rigour follows the stage

Rework is cheaper than specifying. Build a thin slice, put it in front of testers, then write the spec from what they did. A journey without a stated stage is **explore**.

| Stage | Build | Tests | Spec, events, reviews |
|---|---|---|---|
| explore | throwaway is fine; the smallest slice someone can try | one smoke test of the happy path | intent and acceptance only |
| beta | what testers use | the happy path per journey, plus the merge blockers | one runtime event per journey step; one review of the working flow |
| release | stable journeys | every scenario; contract tests between app and backend | thresholds become SLOs; full UX and security review |

Merge blockers at every stage: section 1 violated, a failing scenario of the current stage, red CI. Everything else becomes a follow-up issue. A feature earns more tests after it has survived contact with users.

## 4. Ask only what is hard to undo (revert test)

Can an agent undo the decision with `git revert` and a rebuild, without touching users, stored data or anyone outside the repo? If yes, decide and list it under "Decisions I made" in the PR. If no, ask Alexander. That covers only:

- formats of data already stored;
- public addresses and IDs: bundle ID, domains, feed URLs, contracts others use;
- access users grant: app registrations, OAuth scopes, OS permissions;
- money: prices, subscriptions, paid services;
- legal and privacy commitments, including where data is sent;
- security boundaries.

At most 5 questions per round, each with a recommendation. Effort is never a reason to ask: agents misjudge effort from human experience, and rework by an agent is cheap.

## 5. Estimate before you build

Every proposal, issue plan and PR states agent time, a token range and Alexander's time (reading, testing, deciding). After merging, add the measured cost next to the estimate, so estimates calibrate on measured data. When a budget runs out, ship what works and list the rest as "not built yet".

## 6. Process non-goals

- No requirement that neither Alexander nor a tester asked for. Reviewers propose; they do not add.
- No work beyond the smallest slice testers have not seen yet.
- No deep test suites, threat models or SLOs before the release stage.
- No backend contract before a journey in beta calls the backend.
- No new framework, storage layer or protocol unless the current slice fails without it.
- No rule repeated in prompts or batch files; link the source instead.
