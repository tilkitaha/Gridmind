"""Exploratory: how much battery value does the four-hour episode boundary remove?

Non-causal perfect-foresight bound only. Same battery constants, tariff, community
settlement and LP as battery.mpc_action; only the horizon length changes. No
controller is trained or selected here, and all dates were previously inspected.
Run from project root with PYTHONPATH=src. Units: kWh per 15 min, EUR.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from gridmind_research.battery import (
    DEGR,
    ETA,
    FEE,
    LIMIT,
    MAX,
    MIN,
    TARGET,
    N,
    project,
    settlement,
    tariff,
)

OUT = Path('results/exploratory_episode_length')
JUNE = Path('data/storenet_h1_h6_15min.csv')
LATER = Path('data/later_period/storenet_h1_h6_2020_15min.csv')
# Reference values from the retained evidence; the 4 h reimplementation must reproduce them.
JUNE_ORACLE_4H = 153.76137853250805
LATER_IDLE_4H = 1947.4997183354426


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def oracle_plan(net, hours, soc0=None):
    """Battery.mpc_action's LP over the whole horizon; `net` is realized load or a forecast."""
    H = len(net)
    n = N * H

    def ix(v, t, i):
        return v * n + t * N + i

    A = lil_matrix((2 * n + H, 7 * n))
    rhs = np.zeros(2 * n + H)
    obj = np.zeros(7 * n)
    bounds = []
    for v in range(7):
        for t in range(H):
            for _ in range(N):
                if v < 2:
                    bounds.append((0, LIMIT))
                elif v == 6:
                    bounds.append((TARGET, TARGET) if t == H - 1 else (MIN, MAX))
                else:
                    bounds.append((0, None))
    for t in range(H):
        b = float(tariff(hours[t]))
        for i in range(N):
            r = t * N + i
            for v, coef in [(2, 1), (3, -1), (4, 1), (5, -1), (0, -1), (1, 1)]:
                A[r, ix(v, t, i)] = coef
            rhs[r] = net[t, i]
            A[n + r, ix(6, t, i)] = 1
            A[n + r, ix(0, t, i)] = -ETA
            A[n + r, ix(1, t, i)] = 1 / ETA
            if t:
                A[n + r, ix(6, t - 1, i)] = -1
            else:
                rhs[n + r] = TARGET if soc0 is None else soc0[i]
            A[2 * n + t, ix(4, t, i)] = 1
            A[2 * n + t, ix(5, t, i)] = -1
            for v, c in [(0, DEGR), (1, DEGR), (2, b), (3, -0.08), (4, FEE / 2), (5, FEE / 2)]:
                obj[ix(v, t, i)] = c
    sol = linprog(obj, A_eq=A.tocsr(), b_eq=rhs, bounds=bounds, method='highs')
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.x[:n].reshape(H, N) - sol.x[n:2 * n].reshape(H, N)


def simulate(net, hours, plan):
    """Apply a plan through battery.project and battery.settlement, as BatteryBatch.step does."""
    H = len(net)
    soc = np.full(N, TARGET)
    cost = np.zeros(N)
    base = np.zeros(N)
    throughput = np.zeros(N)
    residual = 0.0
    for t in range(H):
        soc, ac = project(soc, plan[t], H - t)
        buy = tariff(hours[t])
        c, _, _, res = settlement((net[t] + ac)[None], buy)
        b, *_ = settlement(net[t][None], buy)
        cost += c[0] + DEGR * np.abs(ac)
        base += b[0]
        throughput += np.abs(ac)
        residual = max(residual, float(np.abs(res).max()))
    terminal = float(np.abs(soc - TARGET).max())
    assert terminal < 1e-6, terminal
    return {'cost': cost, 'idle': base, 'throughput': throughput, 'residual': residual, 'terminal': terminal}


def load(path):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    return d.iloc[:, ::2].set_axis(range(N), axis=1) - d.iloc[:, 1::2].set_axis(range(N), axis=1)


def window(net, start, periods):
    idx = pd.date_range(start, periods=periods, freq='15min')
    g = net.reindex(idx)
    if not g.notna().all().all():
        return None
    return g.to_numpy(), idx.hour.to_numpy() + idx.minute.to_numpy() / 60


def run_oracle(net, starts, periods):
    rows = []
    for s in starts:
        w = window(net, s, periods)
        if w is None:
            raise ValueError(f'incomplete window {s}')
        r = simulate(*w, oracle_plan(*w))
        rows += [{'start': str(s), 'household': f'H{i + 1}', 'idle_eur': r['idle'][i], 'oracle_eur': r['cost'][i],
                  'throughput_kwh': r['throughput'][i], 'residual': r['residual']} for i in range(N)]
    df = pd.DataFrame(rows)
    df['saving_eur'] = df.idle_eur - df.oracle_eur
    return df


MIN_OBSERVED = 80  # of 96 slots; missing slots concentrate between 00:00 and 05:00


def kept_days(net, first, last):
    """No 2020 day has all 96 slots, so keep days with at least MIN_OBSERVED complete slots."""
    days = pd.date_range(first, last, freq='D')
    full = net.reindex(pd.date_range(first, pd.Timestamp(last) + pd.Timedelta('23:45:00'), freq='15min'))
    observed = full.notna().all(axis=1).groupby(full.index.normalize()).sum()
    return [d for d in days if observed.get(d, 0) >= MIN_OBSERVED], full


def impute(full, method):
    """Two deliberately different fills; agreement between them is the robustness check."""
    if method == 'linear':
        return full.interpolate(method='time', limit_direction='both')
    if method == 'slot_median':
        key = [full.index.strftime('%Y-%m'), full.index.strftime('%H:%M')]
        return full.fillna(full.groupby(key).transform('median'))
    raise ValueError(method)


def compare(net, days):
    """Same days and same filled data: six independent 4 h episodes versus one 24 h episode."""
    four = run_oracle(net, [d + pd.Timedelta(hours=4 * k) for d in days for k in range(6)], 16)
    four['day'] = four.start.str[:10]
    full = run_oracle(net, days, 96)
    full['day'] = full.start.str[:10]
    daily = pd.DataFrame({
        'idle_eur': full.groupby('day').idle_eur.sum(),
        'saving_4h_eur': four.groupby('day').saving_eur.sum(),
        'saving_24h_eur': full.groupby('day').saving_eur.sum(),
    })
    house = pd.DataFrame({
        'saving_4h_eur': four.groupby('household').saving_eur.sum(),
        'saving_24h_eur': full.groupby('household').saving_eur.sum(),
    })
    # Identical days and meter data, so idle cost must agree to rounding.
    np.testing.assert_allclose(four.idle_eur.sum(), full.idle_eur.sum(), rtol=1e-12)
    summary = {
        'idle_eur': float(full.idle_eur.sum()),
        'oracle_saving_4h_eur': float(four.saving_eur.sum()),
        'oracle_saving_24h_eur': float(full.saving_eur.sum()),
        'oracle_saving_4h_pct_of_idle': float(100 * four.saving_eur.sum() / full.idle_eur.sum()),
        'oracle_saving_24h_pct_of_idle': float(100 * full.saving_eur.sum() / full.idle_eur.sum()),
        'ratio_24h_over_4h': float(full.saving_eur.sum() / four.saving_eur.sum()),
        'days_24h_not_better': int((daily.saving_24h_eur < daily.saving_4h_eur - 1e-9).sum()),
        'households_losing_24h': int((house.saving_24h_eur < -1e-9).sum()),
        'per_household': house.round(4).to_dict('index'),
        'max_energy_residual': float(max(four.residual.max(), full.residual.max())),
    }
    return summary, daily


def capture(oracle_saving):
    """Item 2: share of the 4 h perfect-foresight bound captured by each retained arm."""
    s = pd.read_csv('results/later_period/summary.csv')
    s['captured_pct'] = 100 * s.saving_eur / oracle_saving
    s['family'] = s.method.str.replace(r'_seed\d+$', '', regex=True)
    fam = s.groupby('family').agg(seeds=('method', 'size'), mean_saving_eur=('saving_eur', 'mean'),
                                  mean_captured_pct=('captured_pct', 'mean'),
                                  min_captured_pct=('captured_pct', 'min'),
                                  max_captured_pct=('captured_pct', 'max'))
    return s[['method', 'saving_eur', 'captured_pct']], fam.sort_values('mean_captured_pct', ascending=False)


def main():
    OUT.mkdir(exist_ok=True)
    june, later = load(JUNE), load(LATER)

    # 1. Reproduce the retained 4 h evidence before trusting the reimplementation.
    june_eps = [s for s in pd.date_range('2020-06-01', '2020-06-14 20:00', freq='4h')
                if window(june, s, 16) is not None and june.reindex([s - pd.Timedelta(minutes=15)]).notna().all().all()]
    j = run_oracle(june, june_eps, 16)
    np.testing.assert_allclose(j.oracle_eur.sum(), JUNE_ORACLE_4H, rtol=1e-9)
    elig = pd.read_csv('results/later_period/eligibility.csv')
    later_eps = pd.to_datetime(elig.loc[elig.eligible, 'start']).tolist()
    assert len(later_eps) == 501
    lp = run_oracle(later, later_eps, 16)
    np.testing.assert_allclose(lp.idle_eur.sum(), LATER_IDLE_4H, rtol=1e-12)
    lp.to_csv(OUT / 'later_oracle_4h_household.csv', index=False, lineterminator='\n')

    # 2. Captured share of the 4 h bound on the exact 501 retained episodes.
    later_oracle_saving = float(lp.saving_eur.sum())
    arms, families = capture(later_oracle_saving)
    arms.to_csv(OUT / 'later_captured_share_by_arm.csv', index=False, lineterminator='\n')
    families.to_csv(OUT / 'later_captured_share_by_family.csv', lineterminator='\n')

    # 3. Episode length on identical days, under two gap fills.
    days, raw = kept_days(later, '2020-07-01', '2020-12-31')
    observed_share = float(raw[raw.index.normalize().isin(days)].notna().all(axis=1).mean())
    length = {}
    for method in ['linear', 'slot_median']:
        filled = impute(raw, method)
        assert filled[filled.index.normalize().isin(days)].notna().all().all()
        length[method], daily = compare(filled, days)
        daily.to_csv(OUT / f'later_daily_4h_vs_24h_{method}.csv', lineterminator='\n')
        monthly = daily.groupby(daily.index.str[:7]).sum()
        monthly['ratio_24h_over_4h'] = monthly.saving_24h_eur / monthly.saving_4h_eur
        monthly.to_csv(OUT / f'later_monthly_4h_vs_24h_{method}.csv', lineterminator='\n')
        print(method, monthly.round(3).to_string(), sep='\n')

    result = {
        'status': 'Exploratory perfect-foresight bound on previously inspected data; not a controller result',
        'inputs': {str(p): sha(p) for p in [JUNE, LATER, 'results/later_period/summary.csv',
                                            'results/later_period/eligibility.csv']},
        'reproduction': {'june_oracle_4h_eur': float(j.oracle_eur.sum()), 'june_reference_eur': JUNE_ORACLE_4H,
                         'later_idle_4h_eur': float(lp.idle_eur.sum()), 'later_reference_eur': LATER_IDLE_4H},
        'later_501_episodes': {
            'idle_eur': float(lp.idle_eur.sum()),
            'oracle_4h_eur': float(lp.oracle_eur.sum()),
            'oracle_4h_saving_eur': later_oracle_saving,
            'oracle_4h_saving_pct_of_idle': float(100 * later_oracle_saving / lp.idle_eur.sum()),
            'captured_pct': {k: float(v) for k, v in arms.set_index('method').captured_pct.items()
                             if not k[-1].isdigit()},
        },
        'episode_length_later': {
            'days': len(days), 'min_observed_slots': MIN_OBSERVED, 'observed_slot_share': observed_share,
            'complete_96_slot_days_in_2020': 0, **length,
        },
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, indent=2))
    print(families.round(2).to_string())


if __name__ == '__main__':
    main()
