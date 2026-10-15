"""Walk-forward evaluation of price forecasts and of the MILP schedules they produce.

Development period only: the candidate test window stays locked. Each delivery day is
forecast from earlier days only; models are refitted as the window grows. Clock-change
days are inputs but are not scored. Run from project root with PYTHONPATH=src:
  python scripts/polish_forecast_eval.py --days data/polish/prices/days --out results/polish_forecast
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import (
    GBM,
    GBM_PARAMS,
    diebold_mariano,
    feature_matrices,
    lear,
    naive,
    price_matrix,
)
from gridmind_research.polish_market import optimize_schedule, realized_profit

METHODS = ['naive_d1', 'naive_d7', 'lear', 'gbm']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', required=True)
    ap.add_argument('--history-start', default='2025-10-01')
    ap.add_argument('--start', default='2026-01-01')
    ap.add_argument('--end', default='2026-06-30')
    ap.add_argument('--out', required=True)
    ap.add_argument('--features', help='folder from fetch_entsoe_features.py; adds lear_x and gbm_x')
    args = ap.parse_args()
    out = Path(args.out)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    try:
        m, mtus, prices, _ = price_matrix(args.days, args.history_start, args.end)
    except PermissionError as e:
        raise SystemExit(str(e)) from None
    out.mkdir(parents=True, exist_ok=True)
    methods = METHODS + (['lear_x', 'gbm_x'] if args.features else [])
    exog = feature_matrices(args.features, '2025-09-20', args.end) if args.features else None
    gbm, gbm_x = GBM(), GBM(exog=exog)
    rows = []
    for day in pd.date_range(args.start, args.end, freq='D'):
        if day not in m.index or mtus[day] != 96:
            continue  # missing or clock-change day: not scored
        realized = prices[str(day.date())]
        f = {'naive_d1': naive(m, day, 1), 'naive_d7': naive(m, day, 7), 'lear': lear(m, day), 'gbm': gbm(m, day)}
        if exog:
            f |= {'lear_x': lear(m, day, exog=exog), 'gbm_x': gbm_x(m, day)}
        if any(v is None for v in f.values()):
            continue
        row = {'day': str(day.date()), 'oracle_eur': realized_profit(optimize_schedule(realized), realized)}
        for k, v in f.items():
            e = v - realized
            row[f'{k}_mae'], row[f'{k}_rmse'] = float(np.abs(e).mean()), float(np.sqrt((e ** 2).mean()))
            row[f'{k}_eur'] = realized_profit(optimize_schedule(v), realized)
        rows.append(row)
        print(row['day'], ' '.join(f"{k}:{row[k + '_mae']:.1f}/{row[k + '_eur']:.0f}" for k in methods), flush=True)
    daily = pd.DataFrame(rows)
    daily.to_csv(out / 'daily.csv', index=False, lineterminator='\n')

    def summary(d):
        s = {'days': len(d), 'oracle_eur_per_day': float(d.oracle_eur.mean())}
        for k in methods:
            s[k] = {'mae': float(d[f'{k}_mae'].mean()), 'rmse': float(np.sqrt((d[f'{k}_rmse'] ** 2).mean())),
                    'rmae_vs_naive_d1': float(d[f'{k}_mae'].mean() / d.naive_d1_mae.mean()),
                    'eur_per_day': float(d[f'{k}_eur'].mean()),
                    'captured_pct_of_oracle': float(100 * d[f'{k}_eur'].sum() / d.oracle_eur.sum()),
                    'losing_days': int((d[f'{k}_eur'] < 0).sum())}
        tests = {}
        for k in [x for x in methods if x != 'naive_d1']:
            stat, p = diebold_mariano(d[f'{k}_mae'], d.naive_d1_mae)
            diff = pd.DataFrame({'x': (d[f'{k}_eur'] - d.naive_d1_eur).to_numpy()})
            ci = block_bootstrap(diff, pd.DataFrame({'x': np.ones(len(d))}), block=7, draws=10000, seed=15102026)
            tests[f'{k}_vs_naive_d1'] = {'dm_stat_mae': stat, 'dm_p_two_sided': p,
                                         'eur_per_day_difference': ci['estimate'],
                                         'eur_per_day_ci95': [ci['lower95'], ci['upper95']]}
        stat, p = diebold_mariano(d.gbm_mae, d.lear_mae)
        tests['gbm_vs_lear'] = {'dm_stat_mae': stat, 'dm_p_two_sided': p}
        for x, base in (('lear_x', 'lear'), ('gbm_x', 'gbm')):
            if x in methods:
                stat, p = diebold_mariano(d[f'{x}_mae'], d[f'{base}_mae'])
                diff = pd.DataFrame({'x': (d[f'{x}_eur'] - d[f'{base}_eur']).to_numpy()})
                ci = block_bootstrap(diff, pd.DataFrame({'x': np.ones(len(d))}), block=7, draws=10000, seed=15102026)
                tests[f'{x}_vs_{base}'] = {'dm_stat_mae': stat, 'dm_p_two_sided': p, 'eur_per_day_difference': ci['estimate'],
                                           'eur_per_day_ci95': [ci['lower95'], ci['upper95']]}
        s['tests'] = tests
        return s

    june = daily[daily.day >= '2026-06-01']
    result = {
        'status': 'Walk-forward on development days; candidate test window not read; no tuning on these results',
        'scored_range': [args.start, args.end], 'history_from': args.history_start,
        'excluded_days': {'clock_change_or_missing': int(sum(1 for d in pd.date_range(args.start, args.end) if d not in m.index or mtus.get(d, 0) != 96))},
        'models': {'naive_d1': 'same slots on D-1', 'naive_d7': 'same slots on D-7',
                   'lear': 'per-slot LassoLarsIC (AIC), asinh with median/MAD, lags D-1 hourly means, D-1/2/3/7 same slot, weekday',
                   'gbm': {'model': 'HistGradientBoostingRegressor, refit weekly', 'params': GBM_PARAMS},
                   'exogenous': ('load forecast 6.1.B for D, D-1, D-7; D-2 daily means of solar, wind (16.1.B&C) and actual load (6.1.A)'
                                 if args.features else None)},
        'inputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(args.days).glob('*.csv'))
                          if args.history_start <= p.stem <= args.end},
        'walk_forward': summary(daily), 'june_validation': summary(june),
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps({k: result[k] for k in ('walk_forward', 'june_validation')}, indent=2))


if __name__ == '__main__':
    main()
