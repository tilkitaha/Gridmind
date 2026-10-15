"""PPO against MILP on the same LEAR forecasts, Polish development days.

Forecasts: LEAR-style LASSO, walk-forward (each day from earlier days only), January to
June 2026. PPO trains on January–May and selects its checkpoint on June; MILP needs no
training. June is a validation month, not a test: the candidate test window is locked.
Run from project root with PYTHONPATH=src:
  python scripts/polish_rl_eval.py --days data/polish/prices/days --out results/polish_rl
"""
import argparse
import hashlib
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from gridmind_research.holdout import block_bootstrap
from gridmind_research.polish_forecast import lear, naive, price_matrix
from gridmind_research.polish_market import optimize_schedule, realized_profit
from gridmind_research.polish_rl import PPO, Policy, run_days, train

SEEDS = [11, 22, 33, 44, 55]


def forecasts(days_dir, out):
    """LEAR walk-forward forecasts for every scorable day; cached so reruns reuse the same inputs."""
    path = out / 'lear_forecasts.csv'
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    m, mtus, _, _ = price_matrix(days_dir, '2025-10-01', '2026-06-30')
    rows = {}
    for day in pd.date_range('2026-01-01', '2026-06-30'):
        if day in m.index and mtus[day] == 96 and (f := lear(m, day)) is not None:
            rows[day] = f
            print('forecast', day.date(), flush=True)
    frame = pd.DataFrame.from_dict(rows, orient='index')
    frame.to_csv(path, lineterminator='\n')
    return frame


def job(args):
    seed, tf, tp, vf, vp = args
    torch.set_num_threads(1)
    m, info = train(seed, tf, tp, vf, vp)
    return seed, m.state_dict(), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'models').mkdir(exist_ok=True)
    fc = forecasts(args.days, out)
    m, _, prices, _ = price_matrix(args.days, '2025-10-01', '2026-06-30')
    days = list(fc.index)
    F = fc.to_numpy()
    R = np.stack([prices[str(d.date())] for d in days])
    train_mask = np.array([d < pd.Timestamp('2026-06-01') for d in days])
    tf, tp, vf, vp = F[train_mask], R[train_mask], F[~train_mask], R[~train_mask]

    def baselines(Fs, Rs, ds):
        b = {'oracle': [], 'milp_lear': [], 'milp_naive_d1': []}
        for f, r, d in zip(Fs, Rs, ds, strict=True):
            b['oracle'].append(realized_profit(optimize_schedule(r), r))
            b['milp_lear'].append(realized_profit(optimize_schedule(f), r))
            b['milp_naive_d1'].append(realized_profit(optimize_schedule(naive(m, d, 1)), r))
        return {k: np.array(v) for k, v in b.items()}

    val_days = [d for d, k in zip(days, train_mask, strict=True) if not k]
    train_days = [d for d, k in zip(days, train_mask, strict=True) if k]
    base_val, base_train = baselines(vf, vp, val_days), baselines(tf, tp, train_days)
    print('baselines June EUR/day', {k: round(v.mean(), 2) for k, v in base_val.items()}, flush=True)

    with Pool(len(SEEDS)) as pool:
        trained = pool.map(job, [(s, tf, tp, vf, vp) for s in SEEDS])

    runs, daily = [], {'day': [str(d.date()) for d in val_days], **{k: v for k, v in base_val.items()}}
    for seed, state, info in trained:
        path = out / 'models' / f'ppo_seed{seed}.pt'
        torch.save({'seed': seed, 'config': PPO, 'training': info, 'state_dict': state}, path)
        pol = Policy(PPO['hidden'])
        pol.load_state_dict(state)
        val_profit, val_through = run_days(pol, vf, vp)
        tr_profit, _ = run_days(pol, tf, tp)
        daily[f'ppo_seed{seed}'] = val_profit
        diff = pd.DataFrame({'x': val_profit - base_val['milp_lear']})
        ci = block_bootstrap(diff, pd.DataFrame({'x': np.ones(len(diff))}), block=7, draws=10000, seed=15102026)
        runs.append({'seed': seed, 'june_eur_per_day': float(val_profit.mean()), 'train_eur_per_day': float(tr_profit.mean()),
                     'june_captured_pct_of_oracle': float(100 * val_profit.sum() / base_val['oracle'].sum()),
                     'june_minus_milp_eur_per_day': ci['estimate'], 'june_minus_milp_ci95': [ci['lower95'], ci['upper95']],
                     'june_losing_days': int((val_profit < 0).sum()), 'june_throughput_mwh_per_day': float(val_through.mean()),
                     'selected_update': info['selected_update'],
                     'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'history': info['history']})
        print(f"seed {seed}: June {runs[-1]['june_eur_per_day']:.2f} EUR/day, minus MILP {ci['estimate']:.2f} "
              f"[{ci['lower95']:.2f}, {ci['upper95']:.2f}]", flush=True)
    pd.DataFrame(daily).to_csv(out / 'june_daily.csv', index=False, lineterminator='\n')
    summary = lambda b: {k: {'eur_per_day': float(v.mean()), 'captured_pct_of_oracle': float(100 * v.sum() / b['oracle'].sum()),
                             'losing_days': int((v < 0).sum())} for k, v in b.items()}
    result = {
        'status': 'Development days; PPO selected on June, so June is validation, not a test; test window not read',
        'forecast': 'LEAR-style LASSO, walk-forward, prices only (results/polish_forecast)',
        'train_days': len(train_days), 'june_days': len(val_days), 'ppo_config': PPO, 'seeds': SEEDS,
        'baselines_june': summary(base_val), 'baselines_train': summary(base_train),
        'ppo_mean_june_eur_per_day': float(np.mean([r['june_eur_per_day'] for r in runs])),
        'runs': runs,
        'inputs_sha256': {'lear_forecasts.csv': hashlib.sha256((out / 'lear_forecasts.csv').read_bytes()).hexdigest()},
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps({k: result[k] for k in ('baselines_june', 'ppo_mean_june_eur_per_day')}, indent=2))


if __name__ == '__main__':
    main()
