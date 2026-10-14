"""Stage 2 of the held-out 24-hour study: outcomes, executed once.

Refuses to run unless the Stage 1 lock exists and every hash in it still
matches, and refuses to overwrite results. Run from project root with
PYTHONPATH=src:
  python scripts/holdout_stage2.py --out results/holdout_24h
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from gridmind_research.holdout import (
    Forecaster,
    block_bootstrap,
    decide,
    episode_starts,
    fill,
    net_load,
    ridge_params,
    run_episodes,
    sha,
)

THRESHOLD = 0.01
BLOCKS = [7, 1, 3, 14]  # first is primary
ARMS = [  # (name, forecaster, episode length, fill)
    ('ridge_mpc_24h', 'ridge', '24h', 'linear'),
    ('ridge_mpc_4h', 'ridge', '4h', 'linear'),
    ('persistence_mpc_24h', 'persistence', '24h', 'linear'),
    ('persistence_mpc_4h', 'persistence', '4h', 'linear'),
    ('oracle_24h', 'oracle', '24h', 'linear'),
    ('oracle_4h', 'oracle', '4h', 'linear'),
    ('ridge_mpc_24h_median_fill', 'ridge', '24h', 'slot_median'),
]


def verify_lock(out):
    if not (out / 'execution_lock.json').exists():
        raise SystemExit(f'No Stage 1 execution lock in {out}')
    lock = json.loads((out / 'execution_lock.json').read_text())
    checks = {lock['protocol']['path']: lock['protocol']['sha256'], lock['data']['path']: lock['data']['sha256'],
              str(out / 'eligibility.json'): lock['eligibility_sha256'], **lock['code']}
    changed = [p for p, h in checks.items() if sha(p) != h]
    if changed:
        raise SystemExit(f'Locked inputs changed since Stage 1: {changed}')
    return lock


def daily(df, column):
    d = df.assign(day=df.start.str[:10])
    return d.groupby('day')[column].sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='results/holdout_24h')
    args = ap.parse_args()
    out = Path(args.out)
    lock = verify_lock(out)
    if (out / 'results.json').exists():
        raise SystemExit('Refusing to overwrite existing results')
    elig = json.loads((out / 'eligibility.json').read_text())
    processed = pd.read_csv(lock['data']['path'], index_col=0, parse_dates=True)

    per_day, summary, households = {}, {}, []
    for c in [c for c in elig['communities'] if c['included']]:
        raw = net_load(processed, c['households'])
        ridge = ridge_params(raw)
        realized = {m: fill(raw, m) for m in ('linear', 'slot_median')}
        for name, method, length, how in ARMS:
            periods = 96 if length == '24h' else 16
            starts = episode_starts(c['days'], length)
            if method == 'oracle':
                df, f = run_episodes(realized[how], starts, periods), None
            else:
                f = Forecaster(raw, method, ridge)
                df = run_episodes(realized[how], starts, periods, f)
            df.to_csv(out / f"{c['community']}_{name}.csv", index=False, lineterminator='\n')
            per_day[(c['community'], name, 'saving')] = daily(df, 'saving_eur')
            per_day[(c['community'], name, 'idle')] = daily(df, 'idle_eur')
            house = df.groupby('household').saving_eur.sum()
            households += [{'community': c['community'], 'arm': name, 'household': h, 'saving_eur': v}
                           for h, v in house.items()]
            summary[f"{c['community']}/{name}"] = {
                'saving_eur': float(df.saving_eur.sum()), 'idle_eur': float(df.idle_eur.sum()),
                'throughput_kwh': float(df.throughput_kwh.sum()), 'losing_households': int((house < -1e-9).sum()),
                'stale_previous_decisions': int(f.stale) if f else 0,
                'daily_fallback_slots': int(f.daily_fallback) if f else 0, 'ridge_training_rows': ridge['rows'],
            }
            print(c['community'], name, summary[f"{c['community']}/{name}"], flush=True)
    pd.DataFrame(households).to_csv(out / 'household_savings.csv', index=False, lineterminator='\n')

    def table(name, kind):
        # Dates x communities; zero where a community-day is not eligible.
        cols = {k[0]: v for k, v in per_day.items() if k[1] == name and k[2] == kind}
        return pd.DataFrame(cols).sort_index().fillna(0.0)

    idle = table('ridge_mpc_24h', 'idle')
    primary = {b: block_bootstrap(table('ridge_mpc_24h', 'saving'), idle, block=b) for b in BLOCKS}
    count = pd.DataFrame({k[0]: v * 0 + 1 for k, v in per_day.items() if k[1:] == ('ridge_mpc_24h', 'idle')})
    count = count.sort_index().fillna(0.0)
    secondary = {
        'ridge24_minus_ridge4_eur_per_community_day':
            block_bootstrap(table('ridge_mpc_24h', 'saving') - table('ridge_mpc_4h', 'saving'), count),
        'ridge24_minus_persistence24_eur_per_community_day':
            block_bootstrap(table('ridge_mpc_24h', 'saving') - table('persistence_mpc_24h', 'saving'), count),
        'ridge24_share_of_oracle24': float(table('ridge_mpc_24h', 'saving').to_numpy().sum()
                                           / table('oracle_24h', 'saving').to_numpy().sum()),
        'median_fill_relative_saving': block_bootstrap(table('ridge_mpc_24h_median_fill', 'saving'),
                                                       table('ridge_mpc_24h_median_fill', 'idle')),
        'losing_households_ridge24': int(sum(v['losing_households'] for k, v in summary.items()
                                            if k.endswith('/ridge_mpc_24h'))),
    }
    p = primary[BLOCKS[0]]
    result = {
        'dry_run': lock['dry_run'],
        'lock_sha256': sha(out / 'execution_lock.json'),
        'primary_relative_saving': p,
        'decision': decide(p['lower95'], p['upper95'], THRESHOLD),
        'threshold': THRESHOLD,
        'block_sensitivity': primary,
        'secondary': secondary,
        'arms': summary,
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps({k: result[k] for k in ('primary_relative_saving', 'decision', 'secondary')}, indent=2))


if __name__ == '__main__':
    main()
