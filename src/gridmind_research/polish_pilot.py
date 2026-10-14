"""Descriptive pilot on Polish day-ahead prices for the proposed BESS-trader study.

Uses only the development period of configs/polish_market_protocol.json; the
candidate test window stays closed until that protocol is frozen. Schedules come
from polish_market.optimize_schedule; profits from polish_market.realized_profit.
Units: EUR/MWh prices, MW power, MWh energy, EUR profit.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .polish_market import BESS, optimize_schedule, realized_profit, validate_day

PROTOCOL = Path('configs/polish_market_protocol.json')


def candidate_test_window(protocol=PROTOCOL):
    p = json.loads(Path(protocol).read_text(encoding='utf-8'))
    start, end = p['candidate_test']
    return pd.Timestamp(start), pd.Timestamp(end), str(p['status']).startswith('FROZEN')


def refuse_test_window(first, last, protocol=PROTOCOL):
    """Raise when [first, last] touches the candidate test window of an unfrozen protocol."""
    start, end, frozen = candidate_test_window(protocol)
    if pd.Timestamp(first) <= end and pd.Timestamp(last) >= start and not frozen:
        raise PermissionError(f'{start.date()} to {end.date()} is the candidate test window; '
                              'freeze the protocol before reading it')


def load_days(days_dir, first, last):
    """Validated realized prices per local delivery day, and the days skipped with reasons."""
    refuse_test_window(first, last)
    out, skipped = {}, {}
    for day in pd.date_range(first, last, freq='D'):
        key, path = str(day.date()), Path(days_dir) / f'{day.date()}.csv'
        if not path.exists():
            skipped[key] = 'missing'
            continue
        try:
            out[key] = validate_day(pd.read_csv(path), key)
        except (ValueError, TypeError) as e:  # an empty file fails as TypeError inside validate_day
            skipped[key] = str(e) or type(e).__name__
    return out, skipped


def naive_forecast(prices, day, lag_days):
    """Same quarter-hours lag_days earlier; only days of equal length (clock changes differ)."""
    previous = str((pd.Timestamp(day) - pd.Timedelta(days=lag_days)).date())
    if previous in prices and len(prices[previous]) == len(prices[day]):
        return prices[previous]
    return None


def pilot(prices, spec=None):
    """Per-day spread statistics and MILP profits under perfect foresight and naive forecasts.

    Both naive forecasts use prices published before the D-1 12:00 gate: D-1 prices
    are known from about 13:00 on D-2, and D-7 earlier still.
    """
    spec = spec or BESS()
    rows = []
    for day, realized in sorted(prices.items()):
        row = {'day': day, 'mtus': len(realized), 'mean_eur_mwh': float(realized.mean()),
               'min_eur_mwh': float(realized.min()), 'max_eur_mwh': float(realized.max()),
               'spread_eur_mwh': float(realized.max() - realized.min()),
               'negative_mtus': int((realized < 0).sum()),
               'oracle_eur': realized_profit(optimize_schedule(realized, spec), realized, spec)}
        for name, lag in [('naive_d1', 1), ('naive_d7', 7)]:
            forecast = naive_forecast(prices, day, lag)
            if forecast is None:
                row[f'{name}_eur'] = row[f'{name}_mae'] = np.nan
                continue
            row[f'{name}_eur'] = realized_profit(optimize_schedule(forecast, spec), realized, spec)
            row[f'{name}_mae'] = float(np.abs(forecast - realized).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(daily):
    both = daily.dropna(subset=['naive_d1_eur', 'naive_d7_eur'])
    summary = {
        'days': len(daily), 'days_with_both_forecasts': len(both),
        'mean_daily_spread_eur_mwh': float(daily.spread_eur_mwh.mean()),
        'negative_price_mtus': int(daily.negative_mtus.sum()),
        'oracle_eur_per_day': float(daily.oracle_eur.mean()),
    }
    for name in ['naive_d1', 'naive_d7']:
        summary[f'{name}_eur_per_day'] = float(both[f'{name}_eur'].mean())
        summary[f'{name}_captured_pct_of_oracle'] = float(100 * both[f'{name}_eur'].sum() / both.oracle_eur.sum())
        summary[f'{name}_mae_eur_mwh'] = float(both[f'{name}_mae'].mean())
        summary[f'{name}_losing_days'] = int((both[f'{name}_eur'] < 0).sum())
    return summary
