#!/usr/bin/env python3
"""Validate provider stability before allowing the full SABLE benchmark."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', required=True)
    ap.add_argument('--expected', type=int, default=10)
    ap.add_argument('--max-model-errors', type=int, default=1)
    args = ap.parse_args()

    rows = [json.loads(line) for line in Path(args.results).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != args.expected:
        print(f'SMOKE FAIL: expected {args.expected} rows, got {len(rows)}')
        return 1
    model_errors = sum(r.get('integrity', {}).get('termination') == 'model_error' for r in rows)
    completed = args.expected - model_errors
    env_pass = sum(bool(r.get('environment', {}).get('task_success')) for r in rows)
    print(f'SMOKE rows={len(rows)} completed={completed} model_errors={model_errors} task_pass={env_pass}/{args.expected}')
    if model_errors > args.max_model_errors:
        print('SMOKE FAIL: provider instability above threshold')
        return 1
    print('SMOKE PASS: provider is stable enough to run the full benchmark')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
