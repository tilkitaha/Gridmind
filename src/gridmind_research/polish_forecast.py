"""Day-ahead price forecasts for the Polish study, evaluated walk-forward on development days.

Every forecast for delivery day D uses only prices of days before D: at the
D-1 12:00 gate, the prices of D-1 are already published (about 13:00 on D-2).
Clock-change days are mapped to 96 local quarter-hour slots for use as inputs
(a repeated hour is averaged, a skipped hour interpolated) and are never scored.
Units: EUR/MWh.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LassoLarsIC

from .polish_pilot import load_days

ZONE = 'Europe/Warsaw'
SLOTS = 96


def local_slots(frame):
    """Prices of one delivery day on 96 local slots (hour * 4 + minute // 15)."""
    t = pd.to_datetime(frame.timestamp_utc, utc=True).dt.tz_convert(ZONE)
    slot = t.dt.hour * 4 + t.dt.minute // 15
    s = pd.Series(frame.value_eur_mwh.to_numpy(float)).groupby(slot.to_numpy()).mean()
    return s.reindex(range(SLOTS)).interpolate(limit_direction='both').to_numpy()


def price_matrix(days_dir, first, last):
    """Dates x 96 slots, plus the number of market time units per day (92/96/100)."""
    prices, skipped = load_days(days_dir, first, last)
    rows, mtus = {}, {}
    for day in prices:
        frame = pd.read_csv(f'{days_dir}/{day}.csv')
        rows[pd.Timestamp(day)] = local_slots(frame)
        mtus[pd.Timestamp(day)] = len(frame)
    m = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return m, pd.Series(mtus).sort_index(), prices, skipped


def feature_matrices(features_dir, first, last):
    """Exogenous inputs on local days: load forecast and actual load (date x 96, MW) and daily
    mean solar and wind generation (date x 2, MW). Missing series are left out."""
    from .polish_pilot import refuse_test_window
    refuse_test_window(first, last)
    out = {}

    def slots(series):
        local = series.index.tz_convert(ZONE)
        frame = pd.DataFrame({'v': series.to_numpy(float), 'day': local.normalize().tz_localize(None),
                              'slot': local.hour * 4 + local.minute // 15})
        grid = frame.groupby(['day', 'slot']).v.mean().unstack().reindex(columns=range(SLOTS))
        grid = grid.interpolate(axis=1, limit_direction='both')
        return grid.loc[pd.Timestamp(first):pd.Timestamp(last)].dropna()

    for kind, name in (('load_forecast', 'load_fc'), ('load_actual', 'load_act')):
        path = Path(features_dir) / f'{kind}.csv'
        if path.exists():
            f = pd.read_csv(path, index_col=0)
            f.index = pd.to_datetime(f.index, utc=True)
            out[name] = slots(f['total'])
    path = Path(features_dir) / 'generation.csv'
    if path.exists():
        g = pd.read_csv(path, index_col=0)
        g.index = pd.to_datetime(g.index, utc=True)
        solar = g[[c for c in g.columns if c == 'B16']].sum(axis=1, min_count=1)
        wind = g[[c for c in g.columns if c in ('B18', 'B19')]].sum(axis=1, min_count=1)
        out['res'] = pd.DataFrame({'solar': slots(solar).mean(1), 'wind': slots(wind).mean(1)}).dropna()
    return out


def _exog_ok(exog, d):
    one = pd.Timedelta(days=1)
    return (all(d - k * one in exog['load_fc'].index for k in (0, 1, 7))
            and d - 2 * one in exog['res'].index and d - 2 * one in exog['load_act'].index)


def naive(m, day, lag):
    prev = day - pd.Timedelta(days=lag)
    return m.loc[prev].to_numpy() if prev in m.index else None


def profile(m, day, window):
    """Mean price per slot over the `window` calendar days before `day` (D-1 is known at the gate)."""
    hist = m.loc[(m.index < day) & (m.index >= day - pd.Timedelta(days=window))].dropna()
    return hist.mean(0).to_numpy() if len(hist) else None


def _lags(m, days, ks):
    """Array days x len(ks) x 96 of the prices k days earlier."""
    return np.stack([np.stack([m.loc[d - pd.Timedelta(days=k)].to_numpy() for k in ks]) for d in days])


def lear(m, day, min_days=56, exog=None):
    """96 LASSO models (LassoLarsIC, AIC) on asinh-normalised prices, refitted on all past days.

    Reduced LEAR lag set: the 24 hourly means of D-1, the same slot on D-1, D-2, D-3 and D-7,
    and weekday dummies. With exog: the day-ahead load forecast for the same slot on D, D-1 and
    D-7, and D-2 daily means of solar, wind and actual load, each scaled by median and MAD.
    """
    ks = (1, 2, 3, 7)
    lag_ok = lambda d: all(d - pd.Timedelta(days=k) in m.index for k in ks)
    ok = (lambda d: lag_ok(d) and _exog_ok(exog, d)) if exog else lag_ok
    hist = [d for d in m.index if d < day and ok(d)]
    if len(hist) < min_days or not ok(day):
        return None
    past = m.loc[:day - pd.Timedelta(days=1)].to_numpy()
    med = np.median(past)
    mad = np.median(np.abs(past - med)) * 1.4826 or 1.0
    z = lambda p: np.arcsinh((np.asarray(p) - med) / mad)
    L, L0 = z(_lags(m, hist, ks)), z(_lags(m, [day], ks))
    hourly, hourly0 = L[:, 0, :].reshape(len(hist), 24, 4).mean(2), L0[:, 0, :].reshape(1, 24, 4).mean(2)
    W, W0 = np.eye(7)[[d.weekday() for d in hist]], np.eye(7)[[day.weekday()]]
    Y = z(m.loc[hist].to_numpy())
    E, E0, R, R0 = (np.zeros((len(hist), 0, SLOTS)), np.zeros((1, 0, SLOTS)), np.zeros((len(hist), 0)), np.zeros((1, 0)))
    if exog:
        E, E0, R, R0 = _exog_arrays(exog, hist, day)
    out = np.empty(SLOTS)
    for h in range(SLOTS):
        X = np.c_[hourly, L[:, :, h], E[:, :, h], R, W]
        model = LassoLarsIC(criterion='aic').fit(X, Y[:, h])
        out[h] = model.predict(np.c_[hourly0, L0[:, :, h], E0[:, :, h], R0, W0])[0]
    return med + mad * np.sinh(out)


def _exog_arrays(exog, hist, day):
    """Scaled exogenous arrays for training days and the target day, scaled with data known at the gate."""
    one = pd.Timedelta(days=1)
    fc, act, res = exog['load_fc'], exog['load_act'], exog['res']
    past_fc = fc.loc[:day - one].to_numpy()
    mf, sf = np.median(past_fc), np.median(np.abs(past_fc - np.median(past_fc))) * 1.4826 or 1.0
    # Actual load and generation are complete only up to D-2 at the D-1 gate.
    daily = pd.concat([res, act.mean(1).rename('load')], axis=1).loc[:day - 2 * one]
    md, sd = daily.median(), (daily - daily.median()).abs().median() * 1.4826
    sd = sd.replace(0, 1.0)

    def build(days):
        e = np.stack([np.stack([fc.loc[d - k * one].to_numpy() for k in (0, 1, 7)]) for d in days])
        r = np.stack([((pd.Series({'solar': res.loc[d - 2 * one, 'solar'], 'wind': res.loc[d - 2 * one, 'wind'],
                                   'load': act.loc[d - 2 * one].mean()}) - md) / sd).to_numpy() for d in days])
        return (e - mf) / sf, r

    E, R = build(hist)
    E0, R0 = build([day])
    return E, E0, R, R0


def _gbm_rows(m, days, exog=None):
    X, y = [], []
    for d in days:
        p1, p2, p7 = (m.loc[d - pd.Timedelta(days=k)].to_numpy() for k in (1, 2, 7))
        for h in range(SLOTS):
            row = [h, d.weekday(), p1[h], p2[h], p7[h], p1.mean(), p1.min(), p1.max(), p1[h] - p7[h]]
            if exog:
                fc = exog['load_fc'].loc[d].to_numpy()
                two = d - pd.Timedelta(days=2)
                row += [fc[h], fc.mean(), fc[h] - exog['load_fc'].loc[d - pd.Timedelta(days=7)].to_numpy()[h],
                        exog['res'].loc[two, 'solar'], exog['res'].loc[two, 'wind'], exog['load_act'].loc[two].mean()]
            X.append(row)
            y.append(m.loc[d, h] if d in m.index else np.nan)
    return np.array(X), np.array(y)


# Fixed in advance, not tuned.
GBM_PARAMS = {'max_iter': 300, 'learning_rate': 0.05, 'max_leaf_nodes': 31, 'l2_regularization': 1.0, 'random_state': 0}


class GBM:
    """One gradient-boosting model over (day, slot) rows; fixed settings, refitted weekly."""

    def __init__(self, refit_days=7, min_days=56, exog=None):
        self.refit_days, self.min_days, self.model, self.fitted_on = refit_days, min_days, None, None
        self.exog = exog

    def __call__(self, m, day):
        lag_ok = lambda d: all(d - pd.Timedelta(days=k) in m.index for k in (1, 2, 7))
        ok = (lambda d: lag_ok(d) and _exog_ok(self.exog, d)) if self.exog else lag_ok
        hist = [d for d in m.index if d < day and ok(d)]
        if len(hist) < self.min_days or not ok(day):
            return None
        if self.model is None or (day - self.fitted_on).days >= self.refit_days:
            X, y = _gbm_rows(m, hist, self.exog)
            self.model = HistGradientBoostingRegressor(**GBM_PARAMS).fit(X, y)
            self.fitted_on = day
        X, _ = _gbm_rows(m, [day], self.exog)
        return self.model.predict(X)


def diebold_mariano(loss_a, loss_b):
    """DM statistic on daily loss differentials with a Newey–West variance; two-sided normal p."""
    from scipy.stats import norm
    d = np.asarray(loss_a) - np.asarray(loss_b)
    n = len(d)
    lag = int(np.floor(n ** (1 / 3)))
    dc = d - d.mean()
    var = dc @ dc / n + 2 * sum((1 - k / (lag + 1)) * (dc[k:] @ dc[:-k]) / n for k in range(1, lag + 1))
    stat = d.mean() / np.sqrt(var / n)
    return float(stat), float(2 * norm.sf(abs(stat)))
