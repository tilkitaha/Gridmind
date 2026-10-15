"""Simple controllers and forecast-error sensitivity on the Polish development days.

Uses the cached LEAR walk-forward forecasts from results/polish_rl. Two questions:
1. How far do the "do nothing" and a threshold rule get, next to the MILP on the same forecast?
   The rule's one setting (slots per side) is chosen on January-May; June is reported apart.
2. How does forecast error turn into lost euros? The MILP plans on the real prices plus a
   scaled copy of the actual LEAR error, and on the real prices plus independent noise.
Development days only; the candidate test window is not read.
Run from project root with PYTHONPATH=src:
  python scripts/polish_controls_eval.py --days data/polish/prices/days --out results/polish_controls
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import price_matrix
from gridmind_research.polish_market import optimize_schedule, realized_profit
from gridmind_research.polish_rl import rule_profit

SLOTS = [2, 4, 6, 8, 10, 12, 16, 20, 24, 32]
SCALES = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
SIGMAS = [5.0, 10.0, 20.0, 30.0, 40.0, 60.0]
NOISE_SEEDS = [0, 1, 2]


def interval(x, seed=15102026):
    ci = block_bootstrap(pd.DataFrame({'x': x}), pd.DataFrame({'x': np.ones(len(x))}), block=7, draws=10000, seed=seed)
    return {'eur_per_day': ci['estimate'], 'ci95': [ci['lower95'], ci['upper95']]}


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
    _, _, prices, _ = price_matrix(args.days, '2025-10-01', '2026-06-30')
    days = list(fc.index)
    F = fc.to_numpy()
    R = np.stack([prices[str(d.date())] for d in days])
    june = np.array([d >= pd.Timestamp('2026-06-01') for d in days])

    oracle = np.array([realized_profit(optimize_schedule(r), r) for r in R])
    milp = np.array([realized_profit(optimize_schedule(f), r) for f, r in zip(F, R, strict=True)])
    rule = {k: np.array([rule_profit(f, r, k) for f, r in zip(F, R, strict=True)]) for k in SLOTS}
    rule_train = {k: float(v[~june].mean()) for k, v in rule.items()}
    best_k = max(SLOTS, key=lambda k: rule_train[k])
    print('rule slots, Jan-May EUR/day', {k: round(v, 2) for k, v in rule_train.items()}, '-> k =', best_k, flush=True)

    def block(mask):
        b = {'oracle': oracle[mask], 'milp_lear': milp[mask], f'rule_lear_k{best_k}': rule[best_k][mask],
             'do_nothing': np.zeros(mask.sum())}
        return {name: {'eur_per_day': float(v.mean()), 'captured_pct_of_oracle': float(100 * v.sum() / b['oracle'].sum()),
                       'losing_days': int((v < -1e-9).sum())} for name, v in b.items()}

    controllers = {
        'june': block(june), 'jan_may': block(~june),
        'june_rule_minus_milp': interval(rule[best_k][june] - milp[june]),
        'rule_jan_may_by_slots': rule_train, 'rule_selected_slots': best_k,
    }
    print('June', {k: round(v['eur_per_day'], 2) for k, v in controllers['june'].items()}, flush=True)

    err = F - R
    scaled = []
    for s in SCALES:
        g = R + s * err
        p = np.array([realized_profit(optimize_schedule(f), r) for f, r in zip(g, R, strict=True)])
        scaled.append({'scale': s, 'mae_eur_mwh': float(np.abs(g - R).mean()), 'eur_per_day': float(p.mean()),
                       'captured_pct_of_oracle': float(100 * p.sum() / oracle.sum())})
        print('LEAR error x', s, round(scaled[-1]['mae_eur_mwh'], 2), round(scaled[-1]['eur_per_day'], 2), flush=True)
    noise = []
    for sigma in SIGMAS:
        runs = []
        for seed in NOISE_SEEDS:
            g = R + np.random.default_rng(seed).normal(0, sigma, R.shape)
            p = np.array([realized_profit(optimize_schedule(f), r) for f, r in zip(g, R, strict=True)])
            runs.append((float(np.abs(g - R).mean()), float(p.mean())))
        noise.append({'sigma_eur_mwh': sigma, 'mae_eur_mwh': float(np.mean([m for m, _ in runs])),
                      'eur_per_day': float(np.mean([p for _, p in runs])), 'eur_per_day_by_seed': [p for _, p in runs],
                      'captured_pct_of_oracle': float(100 * np.mean([p for _, p in runs]) / oracle.mean())})
        print('iid sigma', sigma, round(noise[-1]['mae_eur_mwh'], 2), round(noise[-1]['eur_per_day'], 2), flush=True)

    pd.DataFrame({'day': [str(d.date()) for d in days], 'oracle': oracle, 'milp_lear': milp,
                  **{f'rule_k{k}': v for k, v in rule.items()}}).to_csv(out / 'daily.csv', index=False, lineterminator='\n')
    result = {
        'status': 'Development days Jan-Jun 2026; rule setting chosen on Jan-May; June is validation, not a test; test window not read',
        'forecast': 'LEAR-style LASSO walk-forward, prices only (results/polish_rl/lear_forecasts.csv)',
        'days': len(days), 'june_days': int(june.sum()),
        'controllers': controllers,
        'sensitivity': {'days': len(days), 'oracle_eur_per_day': float(oracle.mean()), 'milp_lear_eur_per_day': float(milp.mean()),
                        'lear_error_scaled': scaled, 'independent_noise': noise, 'noise_seeds': NOISE_SEEDS},
        'inputs_sha256': {'lear_forecasts.csv': hashlib.sha256(Path(args.forecasts).read_bytes()).hexdigest()},
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')


if __name__ == '__main__':
    main()
