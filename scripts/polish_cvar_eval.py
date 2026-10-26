"""Risk-averse (mean-CVaR) scheduling on the Polish day-ahead market. Exploratory.

Added on 26 October 2026, after the confirmatory test, so no result here confirms anything:
the test windows have been scored, and this model was not in the frozen protocol.
The design and the rule that picks the risk weight were fixed before any result
(docs/RISK_AVERSE_SCHEDULING.md); the weight is picked on the development days only.

Stages (run in this order; each refuses to overwrite its result):
  forecasts    LEAR walk-forward for 4 December 2025 - 24 October 2026, the same function as
               every other Polish result, into a git-ignored cache (prices are not redistributed)
  development  every weight on the 180 development days (January-June 2026); picks the weight
  test         the picked weight and the whole grid on July-August and 1 September-24 October 2026
Run from project root with PYTHONPATH=src:
  python scripts/polish_cvar_eval.py forecasts --days data/polish/prices/days
  python scripts/polish_cvar_eval.py development --days data/polish/prices/days
  python scripts/polish_cvar_eval.py test --days data/polish/prices/days
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import lear, naive, price_matrix
from gridmind_research.polish_market import optimize_schedule, realized_profit
from gridmind_research.polish_risk import error_scenarios, optimize_cvar_schedule

CACHE = Path('data/polish/lear/forecasts.csv')
OUT = Path('results/polish_cvar')
FIRST, LAST = '2025-12-04', '2026-10-24'
# Fixed before any result (docs/RISK_AVERSE_SCHEDULING.md)
ERROR_DAYS, ALPHA, WEIGHTS = 28, 0.2, (0.0, 0.25, 0.5, 0.75, 1.0)
MIN_MEAN_SHARE = 0.95
BLOCK, DRAWS, SEED = 7, 10000, 15102026


def cvar5(x):
    x = np.sort(np.asarray(x, dtype=float))
    return float(x[:int(np.ceil(0.05 * len(x)))].mean())


def paired(a, b):
    """a minus b on the same days: mean and CVaR 5% with circular block-bootstrap 95% intervals."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ci = block_bootstrap(pd.DataFrame({'x': a - b}), pd.DataFrame({'x': np.ones(len(a))}), block=BLOCK, draws=DRAWS, seed=SEED)
    n, m = len(a), int(np.ceil(0.05 * len(a)))
    rng = np.random.default_rng(SEED)
    idx = ((rng.integers(0, n, (DRAWS, int(np.ceil(n / BLOCK))))[:, :, None] + np.arange(BLOCK)) % n).reshape(DRAWS, -1)[:, :n]
    d = np.sort(a[idx], 1)[:, :m].mean(1) - np.sort(b[idx], 1)[:, :m].mean(1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return {'mean': {'estimate': ci['estimate'], 'ci95': [ci['lower95'], ci['upper95']]},
            'cvar5': {'estimate': cvar5(a) - cvar5(b), 'ci95': [float(lo), float(hi)]}, 'days': n}


def measures(x, throughput=None):
    x = np.asarray(x, dtype=float)
    out = {'mean_eur_per_day': float(x.mean()), 'cvar5_eur': cvar5(x), 'tail_days': int(np.ceil(0.05 * len(x))),
           'losing_days': int((x < -1e-9).sum()), 'worst_day_eur': float(x.min())}
    if throughput is not None:
        out['throughput_mwh_per_day'] = float(np.mean(throughput))
    return out


def evaluate(days, forecasts, m, mtus, prices):
    """Daily profits of the deterministic baselines and of every weight on the given days."""
    usable = [d for d in forecasts.index if d in m.index and mtus[d] == 96]
    rows, through = {}, {}
    for d in days:
        r, f = prices[str(d.date())], forecasts.loc[d].to_numpy()
        past = [x for x in usable if x < d][-ERROR_DAYS:]
        if len(past) < ERROR_DAYS:
            raise SystemExit(f'Only {len(past)} past forecast errors before {d.date()}')
        S = error_scenarios(f, forecasts.loc[past].to_numpy(), m.loc[past].to_numpy())
        row = {'milp_lear': realized_profit(optimize_schedule(f), r),
               'milp_naive_d1': realized_profit(optimize_schedule(naive(m, d, 1)), r)}
        for w in WEIGHTS:
            s = optimize_cvar_schedule(S, w, ALPHA)
            row[f'cvar_w{w:.2f}'] = realized_profit(s, r)
            through.setdefault(f'cvar_w{w:.2f}', []).append(float((s['charge_mw'] + s['discharge_mw']).sum() * 0.25))
        rows[str(d.date())] = row
        print(d.date(), {k: round(v, 1) for k, v in row.items()}, flush=True)
    return pd.DataFrame.from_dict(rows, orient='index'), through


def load(days_dir):
    m, mtus, prices, _ = price_matrix(days_dir, '2025-10-01', LAST)
    if not CACHE.exists():
        raise SystemExit('Run the forecasts stage first')
    f = pd.read_csv(CACHE, index_col=0)
    f.index = pd.to_datetime(f.index)
    f.columns = range(f.shape[1])
    return m, mtus, prices, f


def check_baseline(frame, recorded, column):
    """The recomputed deterministic MILP must reproduce the recorded result exactly."""
    ref = recorded.loc[frame.index, column].to_numpy()
    diff = float(np.max(np.abs(frame['milp_lear'].to_numpy() - ref)))
    if diff > 1e-6:
        raise SystemExit(f'milp_lear differs from the recorded {column} by {diff}')
    return diff


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['forecasts', 'development', 'test'])
    ap.add_argument('--days', required=True)
    args = ap.parse_args()

    if args.stage == 'forecasts':
        if CACHE.exists():
            raise SystemExit(f'Refusing to overwrite {CACHE}')
        m, mtus, _, _ = price_matrix(args.days, '2025-10-01', LAST)
        out = {}
        for d in pd.date_range(FIRST, LAST):
            f = lear(m, d)
            if f is not None:
                out[str(d.date())] = f
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame.from_dict(out, orient='index').to_csv(CACHE, lineterminator='\n')
        print('LEAR forecasts:', len(out), 'days')
        return

    m, mtus, prices, forecasts = load(args.days)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.stage == 'development':
        if (OUT / 'development.json').exists():
            raise SystemExit('Refusing to overwrite the development result')
        recorded = pd.read_csv('results/polish_profile/daily.csv', index_col='day')
        frame, through = evaluate(pd.to_datetime(recorded.index), forecasts, m, mtus, prices)
        diff = check_baseline(frame, recorded, 'lear')
        base = frame['milp_lear'].mean()
        eligible = [w for w in WEIGHTS if frame[f'cvar_w{w:.2f}'].mean() >= MIN_MEAN_SHARE * base]
        picked = max(eligible, key=lambda w: (round(cvar5(frame[f'cvar_w{w:.2f}']), 9), -w))
        result = {
            'status': 'Exploratory; development days only (January-June 2026); weight picked here, before the test stage',
            'design': {'error_days': ERROR_DAYS, 'alpha': ALPHA, 'weights': list(WEIGHTS),
                       'rule': f'highest CVaR 5% among weights whose mean profit is at least {MIN_MEAN_SHARE:.0%} of MILP on LEAR'},
            'milp_lear_reproduced_max_abs_diff_eur': diff,
            'days': len(frame), 'picked_weight': picked,
            'policies': {k: measures(v, through.get(k)) for k, v in frame.items()},
            'picked_minus_milp_lear': paired(frame[f'cvar_w{picked:.2f}'], frame['milp_lear']),
            'picked_minus_milp_naive_d1': paired(frame[f'cvar_w{picked:.2f}'], frame['milp_naive_d1']),
        }
        frame.to_csv(OUT / 'daily_development.csv', index_label='day', lineterminator='\n')
        (OUT / 'development.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
        print('picked weight', picked, json.dumps(result['picked_minus_milp_lear']))
        return

    if (OUT / 'test.json').exists():
        raise SystemExit('Refusing to overwrite the test result')
    dev = json.loads((OUT / 'development.json').read_text(encoding='utf-8'))
    picked = f"cvar_w{dev['picked_weight']:.2f}"
    periods = {'july_august': pd.read_csv('results/polish_test/daily.csv', index_col='day'),
               'september_october': pd.read_csv('results/polish_test_extension/daily.csv', index_col='day')}
    frames, result = [], {'status': 'Exploratory; the test windows were scored before this model existed',
                          'picked_weight': dev['picked_weight'], 'periods': {}}
    for name, recorded in periods.items():
        frame, through = evaluate(pd.to_datetime(recorded.index), forecasts, m, mtus, prices)
        result['periods'][name] = {
            'days': len(frame), 'milp_lear_reproduced_max_abs_diff_eur': check_baseline(frame, recorded, 'milp_lear'),
            'policies': {k: measures(v, through.get(k)) for k, v in frame.items()},
            'picked_minus_milp_lear': paired(frame[picked], frame['milp_lear']),
            'picked_minus_milp_naive_d1': paired(frame[picked], frame['milp_naive_d1'])}
        frames.append(frame)
    both = pd.concat(frames)
    result['pooled'] = {'days': len(both), 'policies': {k: measures(v) for k, v in both.items()},
                        'picked_minus_milp_lear': paired(both[picked], both['milp_lear']),
                        'picked_minus_milp_naive_d1': paired(both[picked], both['milp_naive_d1'])}
    both.to_csv(OUT / 'daily_test.csv', index_label='day', lineterminator='\n')
    (OUT / 'test.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result['pooled']['picked_minus_milp_lear']))


if __name__ == '__main__':
    main()
