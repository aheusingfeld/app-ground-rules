# app-ground-rules

Alexander's ground rules for every app project built with agents. The rules live in [plugins/app-ground-rules/skills/app-ground-rules/SKILL.md](plugins/app-ground-rules/skills/app-ground-rules/SKILL.md); harnesses without plugins (Codex, Cursor, OpenCode) read that file directly via the project's AGENTS.md.

Two skills:

- [app-ground-rules](plugins/app-ground-rules/skills/app-ground-rules/SKILL.md): behaviour no app may show, threat-model baseline, stages, revert test, estimates, git flow, ARCHITECTURE.md.
- [journey-driven-development](plugins/app-ground-rules/skills/journey-driven-development/SKILL.md): journey specs with stable scenario IDs, flow tables with Mermaid, thresholds as OpenSLO objectives, OpenTelemetry journey events, tests named after scenarios, the Goal QA loop. It ships checker scripts, templates and reviewer agents; set up a repo with `python3 -I plugins/app-ground-rules/skills/journey-driven-development/scripts/bootstrap.py --root <repo>`.

Install in Claude Code:

```
/plugin marketplace add aheusingfeld/app-ground-rules
/plugin install app-ground-rules@app-ground-rules
```

Change the rules by a PR into `develop`. They take effect for everyone when Alexander merges `develop` into `main`, because projects link the `main` version.

[MIT](LICENSE) © 2026 Alexander Heusingfeld.
