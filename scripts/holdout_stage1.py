"""Stage 1 of the held-out 24-hour study: quality-only eligibility and the execution lock.

Reads only whether values are present. Without --dry-run it requires a frozen
protocol, held-out households only, a clean git tree and a new lock.
Run from project root with PYTHONPATH=src.

Dry run on development data:
  python scripts/holdout_stage1.py --dry-run --households H1 H2 H3 H4 H5 H6 \
      --data data/later_period/storenet_h1_h6_2020_15min.csv --out results/holdout_24h_dry_run
"""
import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from gridmind_research.holdout import DEVELOPMENT, RULES, eligibility, protocol_frozen, sha

PROTOCOL = Path('docs/PROTOCOL_24H_HOLDOUT_DRAFT.md')
FINAL = Path('results/holdout_24h')
CODE = ['src/gridmind_research/holdout.py', 'src/gridmind_research/battery.py',
        'src/gridmind_research/forecast_control.py', 'scripts/holdout_stage1.py', 'scripts/holdout_stage2.py']


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--households', nargs='+', default=[f'H{i}' for i in range(7, 21)])
    ap.add_argument('--data', default='data/holdout/storenet_' + '_'.join(f'h{i}' for i in range(7, 21)) + '_2020_15min.csv')
    ap.add_argument('--out', default=str(FINAL))
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    out = Path(args.out)
    if args.dry_run:
        if out.resolve() == FINAL.resolve():
            raise SystemExit('A dry run must not write to the final result directory')
    else:
        if not protocol_frozen(PROTOCOL):
            raise SystemExit('Protocol is not frozen')
        if set(args.households) & set(DEVELOPMENT):
            raise SystemExit('Development households cannot enter the held-out study')
        if git('status', '--porcelain', '--untracked-files=no'):
            raise SystemExit('Commit all tracked changes before locking')
    out.mkdir(parents=True, exist_ok=True)
    lock = out / 'execution_lock.json'
    if lock.exists():
        raise SystemExit(f'Refusing to overwrite {lock}')

    processed = pd.read_csv(args.data, index_col=0, parse_dates=True)
    result = eligibility(processed, args.households)
    (out / 'eligibility.json').write_text(json.dumps(result, indent=2), newline='\n')
    payload = {
        'created_utc': datetime.now(UTC).isoformat(),
        'dry_run': args.dry_run,
        'protocol': {'path': PROTOCOL.as_posix(), 'sha256': sha(PROTOCOL), 'frozen': protocol_frozen(PROTOCOL)},
        'git_commit': git('rev-parse', 'HEAD'),
        'households': args.households,
        'data': {'path': Path(args.data).as_posix(), 'sha256': sha(args.data)},
        'eligibility_sha256': sha(out / 'eligibility.json'),
        'code': {p: sha(p) for p in CODE},
        'rules': RULES,
    }
    with lock.open('x', newline='\n') as f:
        json.dump(payload, f, indent=2)
    included = [c for c in result['communities'] if c['included']]
    print(json.dumps({'eligible': result['eligible'], 'excluded_remainder': result['excluded_remainder'],
                      'communities': [(c['community'], c['households'], len(c['days']), c['included'])
                                      for c in result['communities']],
                      'study_runs': bool(included)}, indent=2))


if __name__ == '__main__':
    main()
