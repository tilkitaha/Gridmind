"""Exploratory: causal MPC with four-hour versus 24-hour episodes on identical days.

Follows explore_episode_length.py, whose perfect-foresight bounds it uses as the
denominator. Forecasts see only raw meter history strictly before the decision
time; the gap-filled series is used only as the realized load that is settled.
Previously inspected July-December 2020 data; nothing is trained or selected.
Run from project root with PYTHONPATH=src. Units: kWh per 15 min, EUR.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from explore_episode_length import LATER, impute, kept_days, load, oracle_plan, sha

from gridmind_research.battery import DEGR, TARGET, N, project, settlement, tariff

OUT = Path('results/exploratory_mpc_24h')
BOUNDS = Path('results/exploratory_episode_length/results.json')
RIDGE = Path('results/forecast_control/ridge_coefficients.npz')
# Retained later-period MPC costs; the causal forecaster must reproduce them on the 501 episodes.
REFERENCE = {'persistence': 1946.6753833810676, 'ridge': 1939.3432126943549}
STEP = pd.Timedelta(minutes=15)


class Forecaster:
    """battery/forecast_control.predict on a dense array, reading only rows before the decision."""

    def __init__(self, raw, method):
        self.index = pd.date_range('2020-01-01', '2020-12-31 23:45', freq='15min')
        self.x = raw.reindex(self.index).to_numpy()
        ok = np.isfinite(self.x).all(1)
        pos = np.where(ok, np.arange(len(ok)), -1)
        self.last_ok = np.maximum.accumulate(pos)  # most recent complete row at or before k
        self.ok = ok
        self.method = method
        r = np.load(RIDGE)
        self.mean, self.scale, self.coef, self.intercept = r['mean'], r['scale'], r['coef'], r['intercept']
        self.stale = self.daily_fallback = 0

    def __call__(self, current, H):
        k = self.index.get_loc(current)
        j = self.last_ok[k - 1]
        if j < 0:
            raise ValueError('no observed history')
        # The retained pipeline required the previous interval; inside a night gap
        # this uses the latest complete observation instead and counts it.
        self.stale += j != k - 1
        last = self.x[j]
        out, previous = [], last
        for t in range(k, k + H):
            daily = self.x[t - 96] if self.ok[t - 96] else last
            self.daily_fallback += not self.ok[t - 96]
            if self.method == 'persistence':
                y = last
            else:
                h = (self.index[t].hour + self.index[t].minute / 60) * np.pi / 12
                z = (np.r_[previous, daily, np.sin(h), np.cos(h)] - self.mean) / self.scale
                y = z @ self.coef.T + self.intercept
            out.append(y)
            previous = y
        return np.asarray(out)


def run_mpc(realized, starts, periods, forecaster):
    """Receding-horizon MPC: replan every step, apply the first action, settle the realized load."""
    rows = []
    for s in starts:
        idx = pd.date_range(s, periods=periods, freq='15min')
        net = realized.reindex(idx).to_numpy()
        hours = idx.hour.to_numpy() + idx.minute.to_numpy() / 60
        assert np.isfinite(net).all()
        soc = np.full(N, TARGET)
        cost, base, throughput = np.zeros(N), np.zeros(N), np.zeros(N)
        for t in range(periods):
            H = periods - t
            plan = oracle_plan(forecaster(idx[t], H), hours[t:], soc)
            soc, ac = project(soc, plan[0], H)
            buy = tariff(hours[t])
            c, *_ = settlement((net[t] + ac)[None], buy)
            b, *_ = settlement(net[t][None], buy)
            cost += c[0] + DEGR * np.abs(ac)
            base += b[0]
            throughput += np.abs(ac)
        assert np.abs(soc - TARGET).max() < 1e-6
        rows += [{'start': str(s), 'household': f'H{i + 1}', 'idle_eur': base[i], 'cost_eur': cost[i],
                  'throughput_kwh': throughput[i]} for i in range(N)]
    df = pd.DataFrame(rows)
    df['saving_eur'] = df.idle_eur - df.cost_eur
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fill', choices=['linear', 'slot_median'], default='linear')
    args = ap.parse_args()
    out = OUT / args.fill
    out.mkdir(parents=True, exist_ok=True)
    raw = load(LATER)
    bounds = json.loads(BOUNDS.read_text())['episode_length_later'][args.fill]

    # 1. The forecaster and MPC loop must reproduce the retained 501-episode results.
    elig = pd.read_csv('results/later_period/eligibility.csv')
    retained = pd.to_datetime(elig.loc[elig.eligible, 'start']).tolist()
    reproduction = {}
    for method, ref in REFERENCE.items():
        f = Forecaster(raw, method)
        cost = run_mpc(raw, retained, 16, f).cost_eur.sum()
        np.testing.assert_allclose(cost, ref, rtol=1e-9)
        assert f.stale == 0
        reproduction[method] = {'cost_eur': float(cost), 'reference_eur': ref}
        print('reproduced', method, cost, flush=True)

    # 2. Same days and filled realized load as the perfect-foresight comparison.
    days, full = kept_days(raw, '2020-07-01', '2020-12-31')
    realized = impute(full, args.fill)
    summary, households = {}, []
    for method in REFERENCE:
        for label, periods, starts in [('4h', 16, [d + pd.Timedelta(hours=4 * k) for d in days for k in range(6)]),
                                       ('24h', 96, days)]:
            f = Forecaster(raw, method)
            df = run_mpc(realized, starts, periods, f)
            np.testing.assert_allclose(df.idle_eur.sum(), bounds['idle_eur'], rtol=1e-12)
            bound = bounds[f'oracle_saving_{label}_eur']
            house = df.groupby('household').saving_eur.sum()
            key = f'{method}_mpc_{label}'
            summary[key] = {
                'cost_eur': float(df.cost_eur.sum()), 'saving_eur': float(df.saving_eur.sum()),
                'saving_pct_of_idle': float(100 * df.saving_eur.sum() / df.idle_eur.sum()),
                'oracle_saving_eur': bound, 'captured_pct_of_same_length_bound': float(100 * df.saving_eur.sum() / bound),
                'throughput_kwh': float(df.throughput_kwh.sum()), 'losing_households': int((house < -1e-9).sum()),
                'stale_previous_decisions': int(f.stale), 'daily_fallback_slots': int(f.daily_fallback),
            }
            households += [{'arm': key, 'household': h, 'saving_eur': v} for h, v in house.items()]
            df.to_csv(out / f'{key}_household_episode.csv', index=False, lineterminator='\n')
            print(key, json.dumps(summary[key]), flush=True)
    pd.DataFrame(households).to_csv(out / 'household_savings.csv', index=False, lineterminator='\n')

    result = {
        'status': 'Exploratory causal MPC on previously inspected data; not a confirmatory comparison',
        'fill': args.fill,
        'days': len(days),
        'inputs': {Path(p).as_posix(): sha(p) for p in [LATER, BOUNDS, RIDGE, 'results/later_period/eligibility.csv']},
        'reproduction_501_episodes': reproduction,
        'idle_eur': bounds['idle_eur'],
        'arms': summary,
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')


if __name__ == '__main__':
    main()
