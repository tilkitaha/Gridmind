"""Exploratory forecast selection by past MILP profit, using retained development records.

This selects among existing forecasts; it does not retrain them or recompute dispatch.
The oracle is never eligible. No independent-test dates are accepted.
"""
import math
from datetime import date, timedelta
from statistics import fmean

CANDIDATES = ('lear', 'naive_d1', 'profile_7d', 'profile_14d', 'profile_28d')
FIRST = date(2026, 1, 1)
LAST = date(2026, 6, 30)


def validate_records(records):
    if not records:
        raise ValueError('No development records')
    previous = None
    for row in records:
        day = date.fromisoformat(row['day'])
        if not FIRST <= day <= LAST:
            raise ValueError('Only January-June 2026 development dates are allowed')
        if previous is not None and day <= previous:
            raise ValueError('Dates must be unique and strictly increasing')
        if any(not math.isfinite(float(row[k])) for k in CANDIDATES):
            raise ValueError('Candidate profits must be finite')
        previous = day


def choose_forecast(history, day, window_days=28, min_days=14):
    """Choose before observing day D; ties follow the fixed CANDIDATES order.

History is realized *day-ahead* settlement profit: D-1 prices are already known
at the D-1 gate. This timing does not generalize to intraday settlement returns.
Missing dates are not filled; the minimum counts observed eligible days.
"""
    if not 1 <= min_days <= window_days:
        raise ValueError('Require 1 <= min_days <= window_days')
    past = [r for r in history
            if day - timedelta(days=window_days) <= date.fromisoformat(r['day']) < day]
    if len(past) < min_days:
        return None
    scores = {k: fmean(float(r[k]) for r in past) for k in CANDIDATES}
    selected = max(CANDIDATES, key=scores.__getitem__)
    return selected, len(past), scores[selected]


def evaluate(records, window_days=28, min_days=14):
    validate_records(records)
    daily, skipped = [], []
    for i, row in enumerate(records):
        decision = choose_forecast(records[:i], date.fromisoformat(row['day']),
                                   window_days, min_days)
        if decision is None:
            skipped.append(row['day'])
            continue
        selected, count, score = decision
        daily.append({'day': row['day'], 'selected_forecast': selected,
                      'history_days': count, 'selection_score_eur_per_day': score,
                      'selected_profit': float(row[selected]),
                      **{k: float(row[k]) for k in CANDIDATES}})
    if not daily:
        raise ValueError('Insufficient history to evaluate any day')
    methods = {}
    for k in ('selected_profit', *CANDIDATES):
        values = [r[k] for r in daily]
        methods[k] = {'eur_per_day': fmean(values), 'total_eur': sum(values),
                      'losing_days': sum(v < 0 for v in values)}
    summary = {
        'status': 'Exploratory retrospective selection on reused development dates; not a test',
        'window_calendar_days': window_days, 'minimum_observed_days': min_days,
        'candidate_order': list(CANDIDATES), 'evaluated_days': len(daily),
        'warmup_or_insufficient_history_days': skipped,
        'methods_on_identical_days': methods,
        'selected_minus_baseline_eur_per_day': {
            k: fmean(r['selected_profit'] - r[k] for r in daily) for k in CANDIDATES},
        'selection_counts': {k: sum(r['selected_forecast'] == k for r in daily)
                             for k in CANDIDATES},
        'limits': ['No new forecast training or dispatch execution',
                   'No independent test or statistical superiority claim',
                   'Input profits inherit the original battery and market assumptions'],
    }
    return daily, summary
