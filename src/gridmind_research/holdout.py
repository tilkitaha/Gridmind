"""Held-out household study of 24-hour MPC; see docs/PROTOCOL_24H_HOLDOUT_DRAFT.md.

Household-count-agnostic versions of the exploratory pipeline in
scripts/explore_episode_length.py and scripts/explore_mpc_24h.py, plus data
preparation, Stage 1 eligibility and the paired block bootstrap. Battery,
tariff and settlement come unchanged from battery.py. Units: kWh per 15 min, EUR.
"""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from .battery import DEGR, ETA, FEE, LIMIT, MAX, MIN, TARGET, project, settlement, tariff
from .forecast_control import fit_model

COLLECTION = 6829134
FIGSHARE = 'https://api.figshare.com/v2'
DEVELOPMENT = [f'H{i}' for i in range(1, 7)]
YEAR = pd.date_range('2020-01-01', '2020-12-31 23:45', freq='15min')
TRAIN = ('2020-01-01', '2020-04-30 23:45')
TEST = ('2020-07-01', '2020-12-31 23:45')
RULES = {'test_coverage': 0.85, 'train_coverage': 0.70, 'community_size': 6,
         'min_observed_slots': 80, 'min_days': 60}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protocol_frozen(path):
    return bool(re.search(r'^\*\*Status: FROZEN', Path(path).read_text(encoding='utf-8'), re.MULTILINE))


# Data -------------------------------------------------------------------------

def figshare_files(households):
    """Resolve H*_W.csv download URLs from the collection listing."""
    with urllib.request.urlopen(f'{FIGSHARE}/collections/{COLLECTION}/articles?page_size=100', timeout=60) as r:
        articles = {a['title']: a['id'] for a in json.load(r)}
    out = []
    for h in households:
        with urllib.request.urlopen(f"{FIGSHARE}/articles/{articles[f'{h}_W']}", timeout=60) as r:
            meta = json.load(r)
        (f,) = [f for f in meta['files'] if f['name'] == f'{h}_W.csv']
        out.append({'household': h, 'article_id': meta['id'], 'file': f['name'], 'size': f['size'],
                    'url': f['download_url'], 'license': meta['license']['name']})
    return out


def prepare_households(raw_dir, households):
    """data.prepare's conversion for any household list, over calendar 2020."""
    frames, quality = [], []
    for h in households:
        path = Path(raw_dir) / f'{h}_W.csv'
        d = pd.read_csv(path)
        d.columns = d.columns.str.strip()
        d['date'] = pd.to_datetime(d['date'], errors='raise')
        if d.date.duplicated().any() or not d.date.is_monotonic_increasing:
            raise ValueError('Duplicate or unordered timestamps')
        if not d.date.dt.second.eq(0).all():
            raise ValueError('Expected minute-aligned readings')
        columns = ['Consumption(W)', 'Production(W)']
        valid = np.isfinite(d[columns]).all(axis=1) & d[columns].ge(0).all(axis=1)
        valid &= d[f'{h}_W'].eq(1)
        powers = d.set_index('date')[columns].copy()
        powers.loc[~valid.to_numpy(), :] = np.nan
        count = powers.resample('15min').count().min(axis=1)
        energy = powers.resample('15min').sum(min_count=15) / 60000.0
        energy.loc[count != 15] = np.nan
        energy.columns = [f'{h}_load_kwh', f'{h}_pv_kwh']
        frames.append(energy)
        quality.append({'household': h, 'source_rows': len(d), 'invalid_minutes': int((~valid).sum()),
                        'complete_15min_intervals': int(count.eq(15).sum()), 'source_sha256': sha(path)})
    aligned = pd.concat(frames, axis=1).sort_index()
    aligned.index.name = 'source_timestamp'
    return aligned.loc['2020-01-01':'2020-12-31 23:45'].copy(), quality


def net_load(processed, households):
    """Load minus PV per household on the dense 2020 grid; NaN where either is missing."""
    d = processed.reindex(YEAR)
    return pd.DataFrame({h: d[f'{h}_load_kwh'] - d[f'{h}_pv_kwh'] for h in households}, index=YEAR)


# Stage 1 ----------------------------------------------------------------------

def eligibility(processed, households, rules=RULES):
    """Quality-only selection: reads presence of values, never their size."""
    net = net_load(processed, households)
    ok = net.notna()
    cover = {h: {'test': float(ok.loc[TEST[0]:TEST[1], h].mean()), 'train': float(ok.loc[TRAIN[0]:TRAIN[1], h].mean())}
             for h in households}
    eligible = [h for h in sorted(households, key=lambda h: int(h[1:]))
                if cover[h]['test'] >= rules['test_coverage'] and cover[h]['train'] >= rules['train_coverage']]
    size = rules['community_size']
    groups = [eligible[i:i + size] for i in range(0, len(eligible) - size + 1, size)]
    communities = []
    for k, members in enumerate(groups, 1):
        joint = ok.loc[TEST[0]:TEST[1], members].all(axis=1)
        observed = joint.groupby(joint.index.normalize()).sum()
        days = [str(d.date()) for d, n in observed.items() if n >= rules['min_observed_slots']]
        communities.append({'community': f'C{k}', 'households': members, 'days': days,
                            'included': len(days) >= rules['min_days']})
    return {'rules': rules, 'coverage': cover, 'eligible': eligible,
            'excluded_remainder': eligible[len(groups) * size:], 'communities': communities}


def fill(net, method):
    """Realized-load gap fill for settlement only; forecasts never see it."""
    if method == 'linear':
        return net.interpolate(method='time', limit_direction='both')
    if method == 'slot_median':
        return net.fillna(net.groupby([net.index.strftime('%Y-%m'), net.index.strftime('%H:%M')]).transform('median'))
    raise ValueError(method)


# Control ----------------------------------------------------------------------

def lp_plan(net, hours, soc0=None):
    """battery.mpc_action's LP for any horizon and household count; returns AC requests."""
    H, N = net.shape
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


def ridge_params(raw_net):
    """forecast_control.fit_model on January-April raw values only."""
    model, rows = fit_model(raw_net.loc[:TRAIN[1]].dropna(how='all'))
    return {'mean': model[0].mean_, 'scale': model[0].scale_, 'coef': model[1].coef_,
            'intercept': model[1].intercept_, 'rows': rows}


class Forecaster:
    """forecast_control.predict on a dense array, reading only rows before the decision."""

    def __init__(self, raw_net, method, ridge=None):
        if method not in ('persistence', 'ridge'):
            raise ValueError(method)
        self.index = raw_net.index
        self.x = raw_net.to_numpy()
        self.ok = np.isfinite(self.x).all(1)
        self.last_ok = np.maximum.accumulate(np.where(self.ok, np.arange(len(self.ok)), -1))
        self.method, self.ridge = method, ridge
        self.stale = self.daily_fallback = 0

    def __call__(self, current, H):
        k = self.index.get_loc(current)
        j = self.last_ok[k - 1]
        if j < 0:
            raise ValueError('no observed history')
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
                r = self.ridge
                y = ((np.r_[previous, daily, np.sin(h), np.cos(h)] - r['mean']) / r['scale']) @ r['coef'].T + r['intercept']
            out.append(y)
            previous = y
        return np.asarray(out)


def run_episodes(realized, starts, periods, forecaster=None):
    """Receding-horizon MPC, or the open-loop perfect-foresight plan when forecaster is None."""
    rows = []
    for s in starts:
        idx = pd.date_range(s, periods=periods, freq='15min')
        net = realized.loc[idx].to_numpy()
        hours = idx.hour.to_numpy() + idx.minute.to_numpy() / 60
        if not np.isfinite(net).all():
            raise ValueError(f'unfilled realized load in {s}')
        N = net.shape[1]
        soc = np.full(N, TARGET)
        cost, base, throughput = np.zeros(N), np.zeros(N), np.zeros(N)
        plan = lp_plan(net, hours) if forecaster is None else None
        for t in range(periods):
            H = periods - t
            a = plan[t] if forecaster is None else lp_plan(forecaster(idx[t], H), hours[t:], soc)[0]
            soc, ac = project(soc, a, H)
            buy = tariff(hours[t])
            c, *_ = settlement((net[t] + ac)[None], buy)
            b, *_ = settlement(net[t][None], buy)
            cost += c[0] + DEGR * np.abs(ac)
            base += b[0]
            throughput += np.abs(ac)
        if np.abs(soc - TARGET).max() > 1e-6:
            raise RuntimeError('terminal state of charge violated')
        rows += [{'start': str(s), 'household': h, 'idle_eur': base[i], 'cost_eur': cost[i],
                  'throughput_kwh': throughput[i]} for i, h in enumerate(realized.columns)]
    df = pd.DataFrame(rows)
    df['saving_eur'] = df.idle_eur - df.cost_eur
    return df


def episode_starts(days, label):
    days = pd.to_datetime(days)
    if label == '24h':
        return list(days)
    return [d + pd.Timedelta(hours=4 * k) for d in days for k in range(6)]


# Statistics -------------------------------------------------------------------

def block_bootstrap(numerator, denominator, block=7, draws=10000, seed=14102026):
    """Ratio of sums with circular moving blocks over dates, all communities resampled jointly.

    numerator, denominator: DataFrames indexed by sorted date, one column per
    community, zero where a community-day is not eligible.
    """
    num = numerator.to_numpy().sum(1)
    den = denominator.to_numpy().sum(1)
    n = len(num)
    k = int(np.ceil(n / block))
    rng = np.random.default_rng(seed)
    idx = ((rng.integers(0, n, (draws, k))[:, :, None] + np.arange(block)) % n).reshape(draws, -1)[:, :n]
    ratios = num[idx].sum(1) / den[idx].sum(1)
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    return {'estimate': float(num.sum() / den.sum()), 'lower95': float(lo), 'upper95': float(hi),
            'block': block, 'draws': draws, 'seed': seed, 'dates': n}


def decide(lower, upper, threshold=0.01):
    """Protocol section 8, for the relative saving R."""
    if lower > threshold:
        return 'H1 supported: lower bound exceeds the threshold'
    if lower > 0:
        return 'Positive saving; economic margin not established'
    if upper < 0:
        return 'Ridge MPC 24 h raises cost'
    return 'Inconclusive: interval includes zero'
