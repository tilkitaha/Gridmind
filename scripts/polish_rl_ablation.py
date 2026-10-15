"""Two follow-ups to the Polish PPO run, same forecasts, split and seeds as results/polish_rl.

1. Training budget: the 300-update run picked its checkpoints at updates 210-300, so it may
   have stopped early. Same settings with 1000 and 2000 updates.
2. No forecast: the policy sees only the battery level and the time of day (forecast input
   set to zero), so it can learn at best one fixed daily pattern. The gap to the run with the
   forecast is what the forecast adds to the learned policy.
June selects the checkpoint, so June stays validation, not a test; the test window is not read.
Run from project root with PYTHONPATH=src:
  python scripts/polish_rl_ablation.py --days data/polish/prices/days --out results/polish_rl_ablation
"""
import argparse
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import price_matrix
from gridmind_research.polish_rl import PPO, Policy, run_days, train

SEEDS = [11, 22, 33, 44, 55]
ARMS = {'forecast_1000': (True, 1000), 'forecast_2000': (True, 2000), 'no_forecast_300': (False, 300)}


def job(args):
    arm, seed, tf, tp, vf, vp = args
    torch.set_num_threads(1)
    m, info = train(seed, tf, tp, vf, vp, dict(PPO, updates=ARMS[arm][1]))
    return arm, seed, m.state_dict(), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', required=True)
    ap.add_argument('--base', default='results/polish_rl')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out, base = Path(args.out), Path(args.base)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    (out / 'models').mkdir(parents=True, exist_ok=True)
    fc = pd.read_csv(base / 'lear_forecasts.csv', index_col=0, parse_dates=True)
    _, _, prices, _ = price_matrix(args.days, '2025-10-01', '2026-06-30')
    days = list(fc.index)
    F = fc.to_numpy()
    R = np.stack([prices[str(d.date())] for d in days])
    tr = np.array([d < pd.Timestamp('2026-06-01') for d in days])
    june = pd.read_csv(base / 'june_daily.csv')
    milp = june['milp_lear'].to_numpy()

    inputs = {True: (F[tr], F[~tr]), False: (np.zeros_like(F[tr]), np.zeros_like(F[~tr]))}
    jobs = [(arm, s, inputs[uses][0], R[tr], inputs[uses][1], R[~tr]) for arm, (uses, _) in ARMS.items() for s in SEEDS]
    with Pool(len(jobs)) as pool:
        trained = pool.map(job, jobs)

    arms, daily = {}, {'day': june['day']}
    for arm, seed, state, info in trained:
        torch.save({'seed': seed, 'arm': arm, 'config': dict(PPO, updates=ARMS[arm][1]), 'training': info, 'state_dict': state},
                   out / 'models' / f'{arm}_seed{seed}.pt')
        pol = Policy(PPO['hidden'])
        pol.load_state_dict(state)
        vf = inputs[ARMS[arm][0]][1]
        profit, through = run_days(pol, vf, R[~tr])
        daily[f'{arm}_seed{seed}'] = profit
        ci = block_bootstrap(pd.DataFrame({'x': profit - milp}), pd.DataFrame({'x': np.ones(len(milp))}),
                             block=7, draws=10000, seed=15102026)
        arms.setdefault(arm, []).append({
            'seed': seed, 'june_eur_per_day': float(profit.mean()), 'june_minus_milp_eur_per_day': ci['estimate'],
            'june_minus_milp_ci95': [ci['lower95'], ci['upper95']], 'june_throughput_mwh_per_day': float(through.mean()),
            'selected_update': info['selected_update'], 'history': info['history']})
        print(arm, seed, round(profit.mean(), 2), info['selected_update'], flush=True)
    pd.DataFrame(daily).to_csv(out / 'june_daily.csv', index=False, lineterminator='\n')
    result = {
        'status': 'Development days; checkpoints selected on June, so June is validation, not a test; test window not read',
        'base_run': args.base, 'seeds': SEEDS, 'june_milp_lear_eur_per_day': float(milp.mean()),
        'arms': {arm: {'uses_forecast': ARMS[arm][0], 'updates': ARMS[arm][1],
                       'mean_june_eur_per_day': float(np.mean([r['june_eur_per_day'] for r in runs])),
                       'runs': sorted(runs, key=lambda r: r['seed'])} for arm, runs in arms.items()},
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps({a: round(v['mean_june_eur_per_day'], 2) for a, v in result['arms'].items()}))


if __name__ == '__main__':
    main()
