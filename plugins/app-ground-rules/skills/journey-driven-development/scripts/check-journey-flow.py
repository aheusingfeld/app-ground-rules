#!/usr/bin/env python3
"""Check a local journey event file against a journey's flow table (journey-driven-development skill, section 5).

The app writes one OTLP/JSON LogsData object per line. Events are grouped into passes by `session.id`
and ordered by time. Each pass runs from `start` through its steps to `done`, when its last scenario is
named by a `done` row, or otherwise to `abandoned`. The check reports every transition the flow table
does not list, every transition over its time budget, and every event with an undesired outcome.
It exits 1 when it reports anything.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROW = re.compile(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$')
BUDGET = re.compile(r'^(\d+(?:\.\d+)?)\s*(s|min|h)$')
UNITS = {'s': 1, 'min': 60, 'h': 3600}


def config(root):
    """Paths from journeys.toml at the repo root; defaults when it is missing (Python 3.11+ for tomllib)."""
    settings = {"journeys_dir": "docs/journeys", "tests": [["Tests", "*.swift"], ["test", "*.ts"]]}
    path = root / "journeys.toml"
    if path.exists():
        import tomllib
        settings.update(tomllib.loads(path.read_text(encoding="utf-8")))
    return settings


def flow(journey):
    """Rows of the journey's `## Flow` table as {(from, to): [(when, seconds or None)]}."""
    rows, inside = defaultdict(list), False
    for line in journey.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            inside = line.strip() == '## Flow' or line.startswith('## Flow ')
            continue
        match = ROW.match(line) if inside else None
        if not match or match.group(1) in ('From', '---') or set(match.group(1)) <= set('-'):
            continue
        source, target, when, budget = match.groups()
        limit = BUDGET.match(budget)
        rows[(source, target)].append((when, float(limit.group(1)) * UNITS[limit.group(2)] if limit else None))
    if not rows:
        raise SystemExit(f'{journey}: no ## Flow table found')
    return rows


def specified_scenarios(journey):
    known, step = set(), None
    for line in journey.read_text(encoding='utf-8').splitlines():
        if match := re.match(r'^### Requirement: (J\d{2}\.[SU]\d+)\b', line):
            step = match.group(1)
        elif step and (match := re.match(r'^#### Scenario: (.+?)\s*(?:\*\(.*\)\*)?\s*$', line)):
            known.add(step + ' ' + match.group(1))
    return known


def events(path, journey_id, known=None):
    """Journey events of one journey from an OTLP/JSON lines file; unreadable lines and rejected records are reported.

    A rejected record (`journey.scenario.rejected`) stands for a scenario name that is not in any journey file. It carries no
    journey, so every one is reported, whatever journey is checked."""
    found, unreadable, rejected = [], [], []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            records = [record for resource in json.loads(line)['resourceLogs'] for scope in resource['scopeLogs']
                       for record in scope['logRecords']]
        except (ValueError, KeyError, TypeError):
            unreadable.append(number)
            continue
        for record in records:
            try:
                if record.get('eventName') == 'journey.scenario.rejected':
                    rejected.append(number)
                    continue
                if record.get('eventName') != 'journey.scenario':
                    continue
                values = {}
                for item in record.get('attributes', []):
                    key = item['key']
                    if not isinstance(key, str) or key in values:
                        raise ValueError('duplicate or malformed attribute')
                    values[key] = item['value'].get('stringValue')
                required = ['journey.id', 'journey.step', 'journey.scenario', 'journey.outcome', 'session.id']
                if any(not isinstance(values.get(key), str) or not values[key].strip() for key in required):
                    raise ValueError('missing string attribute')
                if values['journey.outcome'] not in {'desired', 'undesired', 'abandoned'}:
                    raise ValueError('unknown outcome')
                if not re.fullmatch(r'J\d{2}', values['journey.id']) or not re.fullmatch(re.escape(values['journey.id']) + r'\.[SU]\d+', values['journey.step']):
                    raise ValueError('inconsistent journey and step')
                if values['journey.id'] != journey_id:
                    continue
                if known is not None and values['journey.step'] + ' ' + values['journey.scenario'] not in known:
                    rejected.append(number)
                    continue
                timestamp = int(record['timeUnixNano']) / 1e9
                if timestamp < 0:
                    raise ValueError('negative timestamp')
                found.append({'time': timestamp, 'step': values['journey.step'],
                              'scenario': values['journey.scenario'], 'outcome': values['journey.outcome'],
                              'pass': values['session.id'], 'line': number})
            except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
                unreadable.append(number)
    return found, unreadable, rejected


def check(rows, found):
    passes = defaultdict(list)
    for event in found:
        passes[event['pass']].append(event)
    reports = []
    for pass_id, items in passes.items():
        items.sort(key=lambda event: event['time'])
        for event in items:
            if event['outcome'] == 'undesired':
                reports.append({'pass': pass_id, 'kind': 'undesired', 'line': event['line'],
                                'detail': f"{event['step']} {event['scenario']}"})
        steps = [event for event in items if '.U' not in event['step']]
        if not steps:
            continue
        last = steps[-1]
        ends = 'done' if any(when == last['scenario'] for when, _ in rows.get((last['step'], 'done'), [])) else 'abandoned'
        path = [('start', None)] + [(event['step'], event) for event in steps] + [(ends, None)]
        for (source, before), (target, after) in zip(path, path[1:]):
            listed = rows.get((source, target))
            line = (after or before)['line']
            if not listed:
                reports.append({'pass': pass_id, 'kind': 'transition', 'line': line, 'detail': f'{source} -> {target}'})
                continue
            budgets = [limit for _, limit in listed if limit is not None]
            if before and after and budgets and len(budgets) == len(listed):
                took = after['time'] - before['time']
                if took > max(budgets):
                    reports.append({'pass': pass_id, 'kind': 'budget', 'line': line,
                                    'detail': f'{source} -> {target} took {took:.0f} s, budget {max(budgets):.0f} s'})
    return passes, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('events', type=Path, help='journey-events.jsonl written by the app')
    parser.add_argument('--journey', required=True, help='journey ID, for example J02')
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='repo root (default: current folder)')
    parser.add_argument('--json', action='store_true')
    options = parser.parse_args()
    journeys = sorted((options.root / config(options.root)['journeys_dir']).glob(f'{options.journey}-*.md'))
    if len(journeys) != 1:
        raise SystemExit(f'expected one journey file for {options.journey}, found {len(journeys)}')
    rows = flow(journeys[0])
    found, unreadable, rejected = events(options.events, options.journey, specified_scenarios(journeys[0]))
    passes, reports = check(rows, found)
    reports += [{'pass': None, 'kind': 'unreadable', 'line': number, 'detail': 'not an OTLP/JSON LogsData line'} for number in unreadable]
    reports += [{'pass': None, 'kind': 'rejected', 'line': number, 'detail': 'a scenario name not in any journey file was recorded'} for number in rejected]
    if options.json:
        print(json.dumps({'passes': len(passes), 'events': len(found), 'rejected': len(rejected), 'reports': reports}, indent=2))
    else:
        for pass_id, items in passes.items():
            steps = ' -> '.join(f"{event['step']} {event['scenario']}" for event in sorted(items, key=lambda event: event['time']))
            print(f'pass {pass_id}: {steps}')
        for report in reports:
            print(f"{options.events}:{report['line']}: {report['kind']}: {report['detail']}")
        print(f"{len(passes)} passes, {len(found)} events, {len(rejected)} rejected, {len(reports)} reports"
              + ('; every transition is in the flow table' if not reports else ''))
    return 1 if reports or not found else 0


if __name__ == '__main__':
    sys.exit(main())
