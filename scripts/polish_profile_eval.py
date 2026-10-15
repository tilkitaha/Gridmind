"""Rolling mean-profile forecasts against LEAR on the Polish development days.

Added after the no-forecast PPO arm lost money in June while a fixed schedule planned on the
May mean prices did well: the average daily shape of recent days may already carry most of
what the MILP needs. Forecast for D = mean price per quarter-hour over the last 7, 14 or 28
days (D-1 included, it is published before the D-1 gate). Same 180 days and scoring as the
LEAR run; the comparison was designed after seeing the June results, so it is exploratory.
Run from project root with PYTHONPATH=src:
  python scripts/polish_profile_eval.py --days data/polish/prices/days --out results/polish_profile
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import diebold_mariano, naive, price_matrix, profile
from gridmind_research.polish_market import optimize_schedule, realized_profit

WINDOWS = [7, 14, 28]


def interval(x):
    ci = block_bootstrap(pd.DataFrame({'x': x}), pd.DataFrame({'x': np.ones(len(x))}), block=7, draws=10000, seed=15102026)
    return [ci['lower95'], ci['upper95']]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', required=True)
    ap.add_argument('--forecasts', default='results/polish_rl/lear_forecasts.csv')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    out.mkdir(parents=True, exist_ok=True)
    fc = pd.read_csv(args.forecasts, index_col=0, parse_dates=True)
    m, _, prices, _ = price_matrix(args.days, '2025-10-01', '2026-06-30')
    days = list(fc.index)
    R = np.stack([prices[str(d.date())] for d in days])
    forecasts = {'lear': fc.to_numpy(), 'naive_d1': np.stack([naive(m, d, 1) for d in days]),
                 **{f'profile_{w}d': np.stack([profile(m, d, w) for d in days]) for w in WINDOWS}}
    oracle = np.array([realized_profit(optimize_schedule(r), r) for r in R])
    profit = {k: np.array([realized_profit(optimize_schedule(f), r) for f, r in zip(F, R, strict=True)])
              for k, F in forecasts.items()}
    month = np.array([d.month for d in days])
    june = month == 6
    fixed_june = {}
    for name, rows in (('may_mean', month == 5), ('jan_may_mean', ~june)):
        fixed = optimize_schedule(R[rows].mean(0))
        fixed_june[name] = np.array([realized_profit(fixed, r) for r in R[june]])

    methods = {}
    for k, F in forecasts.items():
        abs_err = np.abs(F - R)
        row = {'mae_eur_mwh': float(abs_err.mean()), 'eur_per_day': float(profit[k].mean()),
               'captured_pct_of_oracle': float(100 * profit[k].sum() / oracle.sum()),
               'losing_days': int((profit[k] < 0).sum()),
               'eur_per_day_by_month': {int(mo): float(profit[k][month == mo].mean()) for mo in np.unique(month)},
               'june_eur_per_day': float(profit[k][june].mean())}
        if k != 'lear':
            d = profit[k] - profit['lear']
            row['minus_lear_eur_per_day'] = float(d.mean())
            row['minus_lear_ci95'] = interval(d)
            row['months_above_lear'] = int(sum(d[month == mo].mean() > 0 for mo in np.unique(month)))
            row['mae_dm_vs_lear'] = diebold_mariano(abs_err.mean(1), np.abs(forecasts['lear'] - R).mean(1))
        methods[k] = row
        print(k, round(row['mae_eur_mwh'], 2), round(row['eur_per_day'], 2), flush=True)

    pd.DataFrame({'day': [str(d.date()) for d in days], 'oracle': oracle, **profit}).to_csv(
        out / 'daily.csv', index=False, lineterminator='\n')
    result = {
        'status': 'Exploratory: designed after the June PPO results; development days Jan-Jun 2026; test window not read',
        'days': len(days), 'oracle_eur_per_day': float(oracle.mean()), 'methods': methods,
        'june_fixed_schedule': {
            name: {'eur_per_day': float(v.mean()), 'losing_days': int((v < 0).sum())} for name, v in fixed_june.items()},
        'june_fixed_schedule_note': 'One schedule, planned once on the mean price per quarter-hour of May (or January-May), repeated every June day',
        'inputs_sha256': {'lear_forecasts.csv': hashlib.sha256(Path(args.forecasts).read_bytes()).hexdigest()},
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')


if __name__ == '__main__':
    main()
