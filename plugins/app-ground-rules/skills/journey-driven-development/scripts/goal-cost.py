#!/usr/bin/env python3
"""Report what a Goal cost in EUR, from Claude Code session transcripts.

Pass one or more session transcripts (`~/.claude/projects/<dir>/<session>.jsonl`). The
session's subagents (`<session>/subagents/*.jsonl`) are included and listed separately, so
reviewer costs show on their own line. Each API message is billed once, even when the
transcript repeats it while streaming.

Prices are Anthropic list prices in USD per million tokens, fetched 1 Nov 2026 from
https://platform.claude.com/docs/en/about-claude/pricing. `--regional` adds the 10 percent
premium for Bedrock regional endpoints stated on the same page. The default exchange rate is
the ECB reference rate of 30 Oct 2026 (1 EUR = 1.1172 USD),
https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml. Update both when they change.
The result is the list-price value of the work, not an invoice: plan subscriptions and
negotiated rates are not modelled.
"""
import argparse
import json
import sys
from pathlib import Path

# model: (base input, 5m cache write, 1h cache write, cache read, output) in USD per MTok
PRICES = {
    'claude-fable-5-1': (10, 12.50, 20, 0.25, 50),
    'claude-opus-5-5': (4, 5, 8, 0.20, 20),
    'claude-opus-5': (5, 6.25, 10, 0.50, 25),
    'claude-opus-4-8': (5, 6.25, 10, 0.50, 25),
    'claude-opus-4-7': (5, 6.25, 10, 0.50, 25),
    'claude-sonnet-5-5': (2, 2.50, 4, 0.10, 10),
    'claude-sonnet-5': (2, 2.50, 4, 0.20, 10),
    'claude-haiku-5-5': (0.10, 0.125, 0.20, 0.01, 0.50),  # prompts up to 100k tokens
}
USD_PER_EUR = 1.1172
REGIONAL_PREMIUM = 1.10


def price_for(model):
    """Match `claude-opus-5-5-20261001` or a Bedrock id such as `eu.anthropic.claude-opus-5-5-v1:0`."""
    model = model.split('anthropic.')[-1]
    for name in sorted(PRICES, key=len, reverse=True):
        if model == name or model.startswith(name + '-') or model.startswith(name + '@'):
            return PRICES[name]
    return None


def usd(path, unpriced):
    seen, total = set(), 0.0
    for line in path.open(errors='replace'):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get('message') if record.get('type') == 'assistant' else None
        if not isinstance(message, dict) or message.get('id') in seen or not message.get('usage'):
            continue
        seen.add(message.get('id'))
        usage, prices = message['usage'], price_for(message.get('model', ''))
        if prices is None:
            unpriced.add(message.get('model', ''))
            continue
        creation = usage.get('cache_creation') or {}
        written_1h = creation.get('ephemeral_1h_input_tokens', 0)
        written_5m = creation.get('ephemeral_5m_input_tokens',
                                  usage.get('cache_creation_input_tokens', 0) - written_1h)
        counts = (usage.get('input_tokens', 0), written_5m, written_1h,
                  usage.get('cache_read_input_tokens', 0), usage.get('output_tokens', 0))
        total += sum(count * price for count, price in zip(counts, prices)) / 1e6
    return total


def agent_name(transcript):
    try:
        meta = json.loads(transcript.with_suffix('.meta.json').read_text())
    except (OSError, ValueError):
        return transcript.stem, ''
    return meta.get('agentType', transcript.stem), meta.get('description', '')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('sessions', nargs='+', type=Path)
    parser.add_argument('--usd-per-eur', type=float, default=USD_PER_EUR)
    parser.add_argument('--regional', action='store_true', help='add the Bedrock regional-endpoint premium')
    parser.add_argument('--json', action='store_true')
    arguments = parser.parse_args()
    factor = (REGIONAL_PREMIUM if arguments.regional else 1) / arguments.usd_per_eur
    unpriced, parts = set(), []
    for session in arguments.sessions:
        parts.append({'agent': 'session', 'description': session.stem,
                      'eur': round(usd(session, unpriced) * factor, 2)})
        for transcript in sorted(session.with_suffix('').glob('subagents/*.jsonl')):
            agent, description = agent_name(transcript)
            parts.append({'agent': agent, 'description': description,
                          'eur': round(usd(transcript, unpriced) * factor, 2)})
    report = {'total_eur': round(sum(part['eur'] for part in parts), 2), 'parts': parts,
              'unpriced_models': sorted(unpriced)}
    if arguments.json:
        print(json.dumps(report))
        return
    for part in parts:
        print(f"{part['eur']:>9.2f} EUR  {part['agent']}  {part['description']}")
    print(f"{report['total_eur']:>9.2f} EUR  total")
    if unpriced:
        print('Not priced, add to PRICES: ' + ', '.join(sorted(unpriced)), file=sys.stderr)


if __name__ == '__main__':
    main()
