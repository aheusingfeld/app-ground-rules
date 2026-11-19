#!/usr/bin/env python3
"""Set up journey-driven development in a repo: copy the checkers, config and templates without overwriting anything.

Run from anywhere: python3 -I <skill folder>/scripts/bootstrap.py --root <repo>. Existing files are kept and
listed as "kept"; rerun after a plugin update to pick up new files only. Use --update-scripts to refresh the
copied checker scripts in scripts/journeys/ (templates and the project's own files are never overwritten).
"""
import argparse
from pathlib import Path
import shutil
import sys

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = ['check-journey-coverage.py', 'check-journey-flow.py', 'goal-cost.py', 'sync-agents.py']
TEMPLATES = {
    'journeys.toml': 'journeys.toml',
    'journeys-README.md': 'docs/journeys/README.md',
    'journey.md': 'docs/journeys/J01-first-start.md',
    'threat-model.md': 'docs/threat-models/TEMPLATE.threat.md',
    'agents/ux-designer.md': '.claude/agents/ux-designer.md',
    'agents/security-reviewer.md': '.claude/agents/security-reviewer.md',
}


def copy(source, target, overwrite, report):
    if target.exists() and not overwrite:
        report.append(f'kept     {target}')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    report.append(f'written  {target}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='repo root (default: current folder)')
    parser.add_argument('--update-scripts', action='store_true', help='overwrite scripts/journeys/*.py with the plugin version')
    options = parser.parse_args()
    root = options.root.resolve()
    if not (root / '.git').exists():
        raise SystemExit(f'{root} is not a git repo root')
    report = []
    for name in SCRIPTS:
        copy(SKILL / 'scripts' / name, root / 'scripts' / 'journeys' / name, options.update_scripts, report)
    for source, target in TEMPLATES.items():
        copy(SKILL / 'templates' / source, root / target, False, report)
    print('\n'.join(str(line).replace(str(root) + '/', '') for line in report))
    print('\nNext: set the test folders in journeys.toml, fill <product> in .claude/agents/*.md, run '
          'python3 -I scripts/journeys/sync-agents.py, add templates/AGENTS-snippet.md to AGENTS.md, '
          'and add scripts/journeys/check-journey-coverage.py to CI.')
    print(f'AGENTS.md snippet: {SKILL / "templates" / "AGENTS-snippet.md"}')


if __name__ == '__main__':
    sys.exit(main())
