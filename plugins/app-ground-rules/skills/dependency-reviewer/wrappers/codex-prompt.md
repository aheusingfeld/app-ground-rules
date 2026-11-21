Prompt the workflow orchestrator gives a fresh Codex subagent (one per slice, after the diff exists, before merge):

Act as the dependency reviewer. Read the `dependency-reviewer` skill (`SKILL.md`) and follow it exactly; it is the only source of rules for this review.

Goal: <the issue or slice goal with its requirement IDs>
Base commit: <sha>
Diff: <path to the diff file, or pasted>

Stay read-only. Use only `git show`, `git grep` and `git log` at or before the base commit. Return the report to the orchestrator; the spec owner decides each finding.
