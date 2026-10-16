"""The one test of the Polish study: PPO against MILP on unseen months, as fixed in the protocol.

Three modes:
  rehearse  runs the identical pipeline on June 2026 (development) so the mechanics can be
            checked against the development results; needs no freeze and never reads the test window
  lock      after the freeze and the test-data download: records the hashes of the protocol,
            the code commit, the checkpoints and every test day, before any score exists
  run       verifies the lock and scores the test window exactly once
Run from project root with PYTHONPATH=src:
  python scripts/polish_test_run.py rehearse --days data/polish/prices/days --out results/polish_test_rehearsal
  python scripts/polish_test_run.py lock --days data/polish/prices/days
  python scripts/polish_test_run.py run --days data/polish/prices/days
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import lear, naive, price_matrix, profile
from gridmind_research.polish_market import optimize_schedule, realized_profit
from gridmind_research.polish_rl import PPO, Policy, rule_profit, run_days

PROTOCOL = Path('configs/polish_test_protocol.json')
OUT = Path('results/polish_test')
REHEARSAL = ('2026-06-01', '2026-06-30')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()


def checkpoints(protocol):
    policies = []
    for path, expected in protocol['treatment_checkpoints'].items():
        if sha(path) != expected:
            raise SystemExit(f'Checkpoint {path} does not match the protocol hash')
        pol = Policy(PPO['hidden'])
        pol.load_state_dict(torch.load(path, weights_only=True)['state_dict'])
        policies.append(pol)
    return policies


def test_window(protocol, fallback):
    if fallback:
        return protocol['fallback_test']['window']
    seen = [k for k, v in protocol['access_declaration'].items() if k != 'question' and v is not False]
    if seen:
        raise SystemExit(f'Access declaration not answered "no" by {seen}; use --fallback or complete it')
    return protocol['candidate_test']


def evaluate(days_dir, first, last, policies, rule_slots=10, profile_days=7):
    m, mtus, prices, skipped = price_matrix(days_dir, '2025-10-01', last)
    days = [d for d in pd.date_range(first, last) if str(d.date()) in prices and mtus[d] == 96]
    excluded = sorted({str(d.date()) for d in pd.date_range(first, last)} - {str(d.date()) for d in days})
    R = np.stack([prices[str(d.date())] for d in days])
    F = np.stack([lear(m, d) for d in days])
    daily = {
        'bound': [realized_profit(optimize_schedule(r), r) for r in R],
        'milp_lear': [realized_profit(optimize_schedule(f), r) for f, r in zip(F, R, strict=True)],
        'milp_profile_7d': [realized_profit(optimize_schedule(profile(m, d, profile_days)), r) for d, r in zip(days, R, strict=True)],
        'milp_naive_d1': [realized_profit(optimize_schedule(naive(m, d, 1)), r) for d, r in zip(days, R, strict=True)],
        f'rule_lear_k{rule_slots}': [rule_profit(f, r, rule_slots) for f, r in zip(F, R, strict=True)],
        'do_nothing': [0.0] * len(days),
    }
    through = []
    for i, pol in enumerate(policies):
        profit, th = run_days(pol, F, R)
        daily[f'ppo_{i + 1}'] = list(profit)
        through.append(float(th.mean()))
    frame = pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in daily.items()}, index=[str(d.date()) for d in days])
    frame['ppo_mean'] = frame[[f'ppo_{i + 1}' for i in range(len(policies))]].mean(1)
    return frame, excluded, {k: v for k, v in skipped.items() if first <= k <= last}, through


def contrast(x):
    ci = block_bootstrap(pd.DataFrame({'x': x}), pd.DataFrame({'x': np.ones(len(x))}), block=7, draws=10000, seed=15102026)
    return {'estimate': ci['estimate'], 'ci95': [ci['lower95'], ci['upper95']]}


def summarize(frame, excluded, skipped, through, protocol):
    p = frame['ppo_mean'] - frame['milp_lear']
    primary = contrast(p.to_numpy())
    margin = protocol['margin_eur_per_day']
    if margin is not None and primary['ci95'][0] > margin:
        decision = 'ppo_better'
    elif primary['ci95'][1] < 0:
        decision = 'ppo_worse'
    else:
        decision = 'no_demonstrated_gain'
    month = pd.to_datetime(frame.index).month
    return {
        'days': len(frame), 'excluded_days': excluded, 'skipped_reasons': skipped,
        'primary': {**primary, 'margin_eur_per_day': margin, 'decision': decision},
        'eur_per_day': {k: float(v.mean()) for k, v in frame.items()},
        'share_of_bound_pct': {k: float(100 * v.sum() / frame['bound'].sum()) for k, v in frame.items()},
        'losing_days': {k: int((v < -1e-9).sum()) for k, v in frame.items()},
        'by_month': {int(mo): {k: float(v[month == mo].mean()) for k, v in frame.items()} for mo in sorted(set(month))},
        'each_checkpoint_minus_milp': {k: contrast((frame[k] - frame['milp_lear']).to_numpy())
                                       for k in frame if k.startswith('ppo_') and k != 'ppo_mean'},
        'secondary_minus_milp': {k: contrast((frame[k] - frame['milp_lear']).to_numpy())
                                 for k in frame if not k.startswith(('ppo', 'milp_lear', 'bound'))},
        'ppo_mean_minus_secondary': {k: contrast((frame['ppo_mean'] - frame[k]).to_numpy())
                                     for k in frame if not k.startswith(('ppo', 'milp_lear', 'bound'))},
        'ppo_throughput_mwh_per_day': through,
    }


def write(out, frame, result):
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / 'daily.csv', index_label='day', lineterminator='\n')
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['rehearse', 'lock', 'run'])
    ap.add_argument('--days', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--fallback', action='store_true')
    args = ap.parse_args()
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    policies = checkpoints(protocol)

    if args.mode == 'rehearse':
        out = Path(args.out or 'results/polish_test_rehearsal')
        if out.resolve() == OUT.resolve() or (out / 'results.json').exists():
            raise SystemExit(f'Refusing to write the rehearsal to {out}')
        frame, excluded, skipped, through = evaluate(args.days, *REHEARSAL, policies)
        result = summarize(frame, excluded, skipped, through, protocol)
        result = {'status': 'Rehearsal on June 2026 (development, validation month); not the test',
                  'window': list(REHEARSAL), 'protocol_sha256': sha(PROTOCOL), **result}
        write(out, frame, result)
        print(json.dumps({k: round(v, 2) for k, v in result['eur_per_day'].items()}), result['primary'])
        return

    if not str(protocol['status']).startswith('FROZEN'):
        raise SystemExit('The protocol is not frozen')
    if protocol['margin_eur_per_day'] is None:
        raise SystemExit('margin_eur_per_day is not set')
    first, last = test_window(protocol, args.fallback)
    lock_path = OUT / 'execution_lock.json'

    if args.mode == 'lock':
        if lock_path.exists():
            raise SystemExit(f'{lock_path} exists')
        if git('status', '--porcelain', '--untracked-files=no'):
            raise SystemExit('Commit every tracked change before locking')
        prov = json.loads((Path(args.days).parent / 'provenance.json').read_text(encoding='utf-8'))
        recorded = {day: h for req in prov['requests'] for day, h in req.get('days', {}).items() if first <= day <= last}
        for day, h in recorded.items():
            path = Path(args.days) / f'{day}.csv'
            if not h.startswith('excluded') and (not path.exists() or sha(path) != h):
                raise SystemExit(f'{path} does not match provenance')
        lock = {'created_utc': dt.datetime.now(dt.UTC).isoformat(), 'window': [first, last],
                'fallback': args.fallback, 'protocol_sha256': sha(PROTOCOL), 'code_commit': git('rev-parse', 'HEAD'),
                'checkpoints': protocol['treatment_checkpoints'], 'test_days_sha256': recorded}
        OUT.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(json.dumps(lock, indent=2), newline='\n')
        print('Locked', len(recorded), 'test days; commit the lock, then run once')
        return

    if not lock_path.exists():
        raise SystemExit('No execution lock; run the lock mode first')
    if (OUT / 'results.json').exists():
        raise SystemExit('The test has already been run')
    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    if lock['protocol_sha256'] != sha(PROTOCOL) or lock['window'] != [first, last]:
        raise SystemExit('The protocol changed after the lock')
    if git('diff', '--name-only', lock['code_commit'], '--', 'src', 'scripts', 'configs'):
        raise SystemExit('Code or configuration changed after the lock')
    for day, h in lock['test_days_sha256'].items():
        if not h.startswith('excluded') and sha(Path(args.days) / f'{day}.csv') != h:
            raise SystemExit(f'Test data for {day} changed after the lock')
    frame, excluded, skipped, through = evaluate(args.days, first, last, policies)
    result = summarize(frame, excluded, skipped, through, protocol)
    result = {'status': 'CONFIRMATORY test, run once under the execution lock', 'window': [first, last],
              'lock_sha256': sha(lock_path), **result}
    write(OUT, frame, result)
    print(json.dumps(result['primary']))


if __name__ == '__main__':
    main()
