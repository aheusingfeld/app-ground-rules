#!/usr/bin/env python3
"""Show which journey scenarios have automated tests, by the scenario ID that tests carry in their names.

A test covers a scenario when its display name starts with "<step ID> <scenario name>:", for example
@Test("J02.S3 Company sign-in: region defaults to Frankfurt") or test("J01.S1 First launch: ...").
Desired steps (JNN.Sn) and undesired behaviour (JNN.Un) count alike. A test naming a scenario that no journey specifies always fails the check; --release also fails on
scenarios without any test.
Paths and test file patterns come from journeys.toml (see the journey-driven-development skill).
"""
import argparse
import json
from pathlib import Path
import re
import sys

REQUIREMENT = re.compile(r'^### Requirement: (J\d{2}\.[SU]\d+)\b')
SCENARIO = re.compile(r'^#### Scenario: (.+?)\s*(?:\*\(.*\)\*)?\s*$')
REFERENCE = re.compile(r'''(?P<quote>["'`])(?P<reference>J\d{2}\.[SU]\d+ (?:(?!(?P=quote)|:)[^\n])+?):''')


def config(root):
    """Paths from journeys.toml at the repo root; defaults when it is missing (Python 3.11+ for tomllib)."""
    settings = {"journeys_dir": "docs/journeys", "tests": [["Tests", "*.swift"], ["test", "*.ts"]]}
    path = root / "journeys.toml"
    if path.exists():
        import tomllib
        settings.update(tomllib.loads(path.read_text(encoding="utf-8")))
    return settings


def scenarios(root):
    found = []
    for journey in sorted((root / config(root)['journeys_dir']).glob('J[0-9][0-9]-*.md')):
        step = None
        for number, line in enumerate(journey.read_text(encoding='utf-8').splitlines(), 1):
            if match := REQUIREMENT.match(line):
                step = match.group(1)
            elif (match := SCENARIO.match(line)) and step:
                found.append({'id': f'{step} {match.group(1)}', 'spec': f'{journey.relative_to(root)}:{number}', 'tests': []})
    return found


def references(root):
    for folder, pattern in config(root)['tests']:
        for path in sorted((root / folder).rglob(pattern)):
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                for match in REFERENCE.finditer(line):
                    yield match.group("reference"), f'{path.relative_to(root)}:{number}'


def check(root, scope=(), selected_scenarios=()):
    if scope and selected_scenarios:
        raise ValueError("Choose step scope or exact scenarios, not both.")
    specified = scenarios(root)
    by_id = {s['id']: s for s in specified}
    unknown = []
    for reference, at in references(root):
        if reference in by_id:
            by_id[reference]['tests'].append(at)
        else:
            unknown.append({'reference': reference, 'at': at})
    steps = {s['id'].split(' ', 1)[0] for s in specified}
    unknown += [{'reference': step, 'at': '--scope'} for step in scope if step not in steps]
    unknown += [{'reference': name, 'at': '--scenario'} for name in selected_scenarios if name not in by_id]
    if scope:
        specified = [s for s in specified if s['id'].split(' ', 1)[0] in scope]
    if selected_scenarios:
        specified = [s for s in specified if s['id'] in selected_scenarios]
    return {'scenarios': specified, 'unknown': unknown}


def table(report):
    lines = ['| Scenario | Tests |', '|---|---|']
    lines += [f"| {s['id']} | {', '.join(s['tests']) or '—'} |" for s in report['scenarios']]
    covered = sum(1 for s in report['scenarios'] if s['tests'])
    lines.append(f"\n{covered} of {len(report['scenarios'])} scenarios have a test.")
    lines += [f"Unknown scenario {u['reference']!r} at {u['at']}" for u in report['unknown']]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='repo root (default: current folder)')
    parser.add_argument('--json', action='store_true', help='print the report as JSON')
    parser.add_argument('--release', '--require-covered', dest='release', action='store_true',
                        help='fail when any selected scenario has no test (--release remains supported)')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--scope', type=lambda value: value.split(','), default=[],
                        help="only these steps, for example J02.S3,J02.U1 (a Goal's scenarios)")
    selection.add_argument('--scenario', action='append', default=[],
                           help='one exact scenario ID and name; repeat for a subset, including names with commas')
    arguments = parser.parse_args()
    report = check(arguments.root, arguments.scope, arguments.scenario)
    print(json.dumps(report, indent=2) if arguments.json else table(report))
    uncovered = any(not s['tests'] for s in report['scenarios'])
    return 1 if report['unknown'] or (arguments.release and uncovered) else 0


if __name__ == '__main__':
    sys.exit(main())
