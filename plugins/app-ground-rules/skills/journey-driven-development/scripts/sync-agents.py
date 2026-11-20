#!/usr/bin/env python3
"""Render the reviewer agents in .claude/agents for Codex and OpenCode.

`.claude/agents/*.md` is the single source; Claude Code and Cursor read it directly
(https://cursor.com/docs/context/subagents). Codex reads `.codex/agents/*.toml` with `name`,
`description` and `developer_instructions`
(https://learn.chatgpt.com/docs/agent-configuration/subagents). OpenCode reads
`.opencode/agents/*.md` with `description` and `mode` (https://opencode.ai/docs/agents/).
All fetched 1 Nov 2026. Run after editing an agent; `--check` fails when a copy is stale.
"""
import argparse
import json
import sys
from pathlib import Path


def parse(path):
    _, header, body = path.read_text(encoding='utf-8').split('---\n', 2)
    fields = dict(line.split(':', 1) for line in header.splitlines() if ':' in line)
    fields = {key.strip(): value.strip() for key, value in fields.items()}
    return fields.get('name', path.stem), fields['description'], body.strip() + '\n'


def renders(root):
    for source in sorted((root / '.claude' / 'agents').glob('*.md')):
        name, description, body = parse(source)
        note = f'Generated from .claude/agents/{source.name} by scripts/journeys/sync-agents.py; edit the source.'
        instructions = body.replace('\\', '\\\\').replace('"""', '\\"""')
        yield root / '.codex' / 'agents' / f'{name}.toml', (
            f'# {note}\nname = {json.dumps(name)}\ndescription = {json.dumps(description, ensure_ascii=False)}\n'
            f'developer_instructions = """\n{instructions}"""\n')
        yield root / '.opencode' / 'agents' / f'{name}.md', (
            f'---\n# {note}\ndescription: {json.dumps(description, ensure_ascii=False)}\nmode: subagent\n---\n\n{body}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='repo root (default: current folder)')
    parser.add_argument('--check', action='store_true', help='report stale copies instead of writing them')
    arguments = parser.parse_args()
    stale = []
    for target, text in renders(arguments.root):
        if target.exists() and target.read_text(encoding='utf-8') == text:
            continue
        if arguments.check:
            stale.append(str(target.relative_to(arguments.root)))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    if stale:
        print('Stale agent copies, run scripts/journeys/sync-agents.py: ' + ', '.join(stale))
        sys.exit(1)


if __name__ == '__main__':
    main()
