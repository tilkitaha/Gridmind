"""Downside risk of the Polish day-ahead controllers, from the recorded daily profits only.

Exploratory: it reads daily results that are already in the repository (no prices, no new
period) and adds risk measures to the mean profit reported so far:
  - CVaR 5% (expected shortfall): mean daily profit on the worst 5% of days, ceil(0.05 n)
    days (Rockafellar and Uryasev, 2000); higher is better
  - 5th percentile of daily profit, standard deviation, losing days, worst day
Paired differences use the same circular moving-block bootstrap as the other Polish
evaluations (blocks of 7 days, 10,000 draws, seed 15102026): mean and CVaR 5% of the
difference between two controllers on the same days.
Run from project root with PYTHONPATH=src:
  python scripts/polish_risk_eval.py --out results/polish_risk
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BLOCK, DRAWS, SEED = 7, 10000, 15102026
PPO = [f'forecast_2000_seed{s}' for s in (11, 22, 33, 44, 55)]


def cvar(x, q=0.05):
    x = np.sort(np.asarray(x, float))
    return float(x[:int(np.ceil(q * len(x)))].mean())


def measures(x):
    x = np.asarray(x, float)
    return {'days': len(x), 'mean_eur_per_day': float(x.mean()), 'sd_eur': float(x.std(ddof=1)),
            'cvar5_eur': cvar(x), 'p5_eur': float(np.percentile(x, 5)), 'losing_days': int((x < -1e-9).sum()),
            'worst_day_eur': float(x.min())}


def paired(a, b):
    """a minus b on the same days: mean and CVaR 5% with block-bootstrap 95% intervals."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    rng = np.random.default_rng(SEED)
    k = int(np.ceil(n / BLOCK))
    idx = ((rng.integers(0, n, (DRAWS, k))[:, :, None] + np.arange(BLOCK)) % n).reshape(DRAWS, -1)[:, :n]
    mean_d = (a[idx] - b[idx]).mean(1)
    m = int(np.ceil(0.05 * n))
    cvar_d = np.sort(a[idx], 1)[:, :m].mean(1) - np.sort(b[idx], 1)[:, :m].mean(1)
    out = {}
    for name, est, draws in (('mean', float((a - b).mean()), mean_d), ('cvar5', cvar(a) - cvar(b), cvar_d)):
        lo, hi = np.percentile(draws, [2.5, 97.5])
        out[name] = {'estimate_eur': est, 'lower95': float(lo), 'upper95': float(hi)}
    out['losing_days'] = {'a': int((a < -1e-9).sum()), 'b': int((b < -1e-9).sum())}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    out.mkdir(parents=True, exist_ok=True)

    prof = pd.read_csv('results/polish_profile/daily.csv', index_col='day')
    rule = pd.read_csv('results/polish_controls/daily.csv', index_col='day')['rule_k10']
    half = pd.DataFrame({'perfect_foresight': prof['oracle'], 'milp_lear': prof['lear'],
                         'milp_profile_7d': prof['profile_7d'], 'milp_naive_d1': prof['naive_d1'],
                         'threshold_rule_k10': rule}).dropna()
    june_milp = pd.read_csv('results/polish_rl/june_daily.csv', index_col='day')
    june_ppo = pd.read_csv('results/polish_rl_ablation/june_daily.csv', index_col='day')
    june = pd.DataFrame({'perfect_foresight': june_milp['oracle'], 'milp_lear': june_milp['milp_lear'],
                         'milp_naive_d1': june_milp['milp_naive_d1'],
                         'ppo_mean_of_5': june_ppo[PPO].mean(1)}).dropna()
    june = june.join(june_ppo[PPO]).join(half[['milp_profile_7d', 'threshold_rule_k10']], how='left')

    res = {
        'note': 'Exploratory: computed from recorded daily profits of the development period; no new data. '
                'January-May are PPO training months, so PPO is evaluated on June only.',
        'definitions': {'cvar5': 'mean daily profit on the worst ceil(0.05 n) days (expected shortfall)',
                        'bootstrap': {'block': BLOCK, 'draws': DRAWS, 'seed': SEED, 'kind': 'circular moving block'}},
        'january_june': {'days': len(half), 'controllers': {c: measures(half[c]) for c in half}},
        'june': {'days': len(june), 'controllers': {c: measures(june[c]) for c in june}},
        'paired': {
            'january_june_milp_lear_minus_naive_d1': paired(half['milp_lear'], half['milp_naive_d1']),
            'january_june_milp_lear_minus_profile_7d': paired(half['milp_lear'], half['milp_profile_7d']),
            'january_june_milp_lear_minus_rule_k10': paired(half['milp_lear'], half['threshold_rule_k10']),
            'june_ppo_mean_minus_milp_lear': paired(june['ppo_mean_of_5'], june['milp_lear']),
        },
    }
    (out / 'results.json').write_text(json.dumps(res, indent=2) + '\n', encoding='utf-8', newline='\n')
    rows = [{'period': p, 'controller': c, **m} for p in ('january_june', 'june')
            for c, m in res[p]['controllers'].items()]
    pd.DataFrame(rows).to_csv(out / 'summary.csv', index=False, lineterminator='\n')
    for key, r in res['paired'].items():
        print(key, {k: round(v['estimate_eur'], 2) if isinstance(v, dict) and 'estimate_eur' in v else v
                    for k, v in r.items()},
              f"mean 95% [{r['mean']['lower95']:.2f}, {r['mean']['upper95']:.2f}]",
              f"CVaR5 95% [{r['cvar5']['lower95']:.2f}, {r['cvar5']['upper95']:.2f}]")


if __name__ == '__main__':
    main()
