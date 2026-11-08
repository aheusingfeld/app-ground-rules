# app-ground-rules

Alexander's ground rules for every app project built with agents. The rules live in [plugins/app-ground-rules/skills/app-ground-rules/SKILL.md](plugins/app-ground-rules/skills/app-ground-rules/SKILL.md); harnesses without plugins (Codex, Cursor, OpenCode) read that file directly via the project's AGENTS.md.

Install in Claude Code:

```
/plugin marketplace add aheusingfeld/app-ground-rules
/plugin install app-ground-rules@app-ground-rules
```

Change the rules by a PR into `develop`. They take effect for everyone when Alexander merges `develop` into `main`, because projects link the `main` version.
