---
name: app-ground-rules
description: Alexander's ground rules for every app he builds with agents — behaviour no app may show, the threat-model baseline, the stages explore/beta/release, the revert test for when to ask him, the estimate and budget rule, who merges where, and the ARCHITECTURE.md overview. Use before planning, specifying, building or reviewing work in any of his app repos, before writing "must never" requirements or a threat model, and before asking him a question.
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

Every proposal, issue plan and PR states agent time, a token range and Alexander's time (reading, testing, deciding). After merging, add the measured cost next to the estimate, so estimates calibrate on measured data.

A budget is what Alexander set: EUR, agent time or tokens. At 80 percent, warn where the work is tracked. At 95 percent, start nothing new: ship what works, list the rest as "not built yet", and stop. Stopping at 95 rather than 100 percent leaves room for the shipping itself, so the budget is not exceeded.

## 6. Process non-goals

- No requirement that neither Alexander nor a tester asked for. Reviewers propose; they do not add.
- No work beyond the smallest slice testers have not seen yet.
- No deep test suites, threat models or SLOs before the release stage.
- No backend contract before a journey in beta calls the backend.
- No new framework, storage layer or protocol unless the current slice fails without it.
- No rule repeated in prompts, batch files or a project's own docs; link the source and write down only the project's differences.

## 7. Git flow: who merges where

- Agents branch from `develop` and merge their own PRs into `develop` (rebase merge) once CI is green, there are no conflicts and no merge blocker (section 3) remains. This includes spec and docs PRs, as long as every behaviour clause they add is backed by a decision of Alexander. Proposals go into the issue, not into a merged spec.
- Only Alexander merges into `main`. Agents open the `develop` → `main` PR for a release and never push or force-push to `main`.

## 8. ARCHITECTURE.md: the current picture

Every app repo has an `ARCHITECTURE.md` at its root, so Alexander can see at any moment what the app consists of right now. It holds:

- an overview of the components that exist today (mermaid diagram + table), each in one or two plain sentences, with its main source folder;
- how they interact, as one diagram (Mermaid) plus a short list of the important calls, events and data stores;
- for each component, the journeys and steps it serves (`JNN`, `JNN.Sn`), linked to the journey files;
- links to the ADRs that shaped it. Not every decision needs an ADR (section 4 says which do); ARCHITECTURE.md covers the rest e.g. the base primitives and mental model the agents follow during implementation.

It describes the current state only, not history or plans. The PR that adds, removes, renames or rewires a component updates it in the same change. A PR that leaves it out of date fails review.
