"""Matched profit-versus-error selection on retained development outcomes.

All methods choose from the same four forecasts and use the same past dates.
These are retrospective exploratory analyses, not an independent test.
"""
import math
from datetime import date, timedelta
from statistics import fmean

import numpy as np

CANDIDATES = ('lear', 'gbm', 'naive_d1', 'naive_d7')
FIRST, LAST = date(2026, 1, 1), date(2026, 6, 30)
FREEZE = date(2026, 6, 1)


def validate(records):
    """Fail closed on incomplete panels, bad ordering, or non-development dates."""
    if not records:
        raise ValueError('No development records')
    previous = None
    for row in records:
        day = date.fromisoformat(row['day'])
        if not FIRST <= day <= LAST:
            raise ValueError('Only January-June 2026 development dates are allowed')
        if previous is not None and day <= previous:
            raise ValueError('Dates must be unique and strictly increasing')
        for candidate in CANDIDATES:
            for metric in ('eur', 'mae'):
                key = f'{candidate}_{metric}'
                if key not in row:
                    raise ValueError(f'Missing candidate metric: {key}')
                value = float(row[key])
                if not math.isfinite(value) or (metric == 'mae' and value < 0):
                    raise ValueError(f'Invalid candidate metric: {key}')
        previous = day


def select(records, day, objective, window_days=28, min_days=14):
    """Use only dates before day; None window means expanding history.

For day-ahead schedules, D-1 settlement prices are known at the D-1 gate.
This timing must not be reused for realized intraday returns.
"""
    if objective not in ('profit', 'mae'):
        raise ValueError('Objective must be profit or mae')
    if min_days < 1 or (window_days is not None and window_days < min_days):
        raise ValueError('Require a positive minimum no larger than the window')
    past = [row for row in records if date.fromisoformat(row['day']) < day
            and (window_days is None
                 or date.fromisoformat(row['day']) >= day - timedelta(days=window_days))]
    if len(past) < min_days:
        return None
    metric = 'eur' if objective == 'profit' else 'mae'
    scores = {k: fmean(float(r[f'{k}_{metric}']) for r in past) for k in CANDIDATES}
    # Python's max/min preserves the fixed candidate order for exact ties.
    chosen = (max if objective == 'profit' else min)(CANDIDATES, key=scores.__getitem__)
    return {'candidate': chosen, 'scores': scores, 'history_days': len(past),
            'history_first': past[0]['day'], 'history_last': past[-1]['day']}


def paired_interval(values, block=7, draws=10000, seed=20102026):
    """Circular blocks of observed rows; intervals condition on recorded choices."""
    values = np.asarray(values, dtype=float)
    if (values.ndim != 1 or not len(values) or not np.isfinite(values).all()
            or not 1 <= block <= len(values) or draws < 1):
        raise ValueError('Invalid bootstrap inputs')
    rng = np.random.default_rng(seed)
    n = len(values)
    starts = rng.integers(0, n, (draws, math.ceil(n / block)))
    indices = ((starts[:, :, None] + np.arange(block)) % n).reshape(draws, -1)[:, :n]
    lower, upper = np.percentile(values[indices].mean(axis=1), [2.5, 97.5])
    return {'mean_eur_per_day': float(values.mean()),
            'lower95': float(lower), 'upper95': float(upper),
            'block_observations': block, 'draws': draws, 'seed': seed,
            'interpretation': 'Exploratory conditional interval; selection is not refit in draws'}


def summarize(rows, arms):
    result = {'days': len(rows), 'methods': {}, 'comparisons': {}}
    if not rows:
        return result
    for arm in arms:
        result['methods'][arm] = {
            'eur_per_day': fmean(r[f'{arm}_eur'] for r in rows),
            'mae_eur_mwh': fmean(r[f'{arm}_mae'] for r in rows),
            'losing_days': sum(r[f'{arm}_eur'] < 0 for r in rows),
        }
    for left, right in [('rolling_profit', 'rolling_mae'),
                        ('rolling_profit', 'lear'), ('rolling_mae', 'lear'),
                        ('frozen_profit', 'frozen_mae')]:
        if left in arms and right in arms:
            result['comparisons'][f'{left}_minus_{right}'] = paired_interval(
                [r[f'{left}_eur'] - r[f'{right}_eur'] for r in rows],
                block=min(7, len(rows)))
    return result


def evaluate(records, window_days=28, min_days=14):
    validate(records)
    daily, decisions, skipped = [], [], []
    frozen = {objective: select(records, FREEZE, objective, None, min_days)
              for objective in ('profit', 'mae')}
    for record in records:
        day = date.fromisoformat(record['day'])
        choices = {f'rolling_{obj}': select(records, day, obj, window_days, min_days)
                   for obj in ('profit', 'mae')}
        if any(choice is None for choice in choices.values()):
            skipped.append(record['day'])
            continue
        if day >= FREEZE and all(frozen.values()):
            choices.update({f'frozen_{obj}': choice for obj, choice in frozen.items()})
        row = {'day': record['day']}
        for candidate in CANDIDATES:
            for metric in ('eur', 'mae'):
                row[f'{candidate}_{metric}'] = float(record[f'{candidate}_{metric}'])
        for arm, choice in choices.items():
            candidate = choice['candidate']
            row[f'{arm}_candidate'] = candidate
            for metric in ('eur', 'mae'):
                row[f'{arm}_{metric}'] = row[f'{candidate}_{metric}']
            decisions.append({'day': record['day'], 'arm': arm, **choice})
        daily.append(row)
    if not daily:
        raise ValueError('Insufficient history to evaluate any day')
    arms = ['rolling_profit', 'rolling_mae', *CANDIDATES]
    june = [r for r in daily if 'frozen_profit_candidate' in r]
    summary = {
        'status': 'Exploratory comparison on previously inspected development dates',
        'candidates': list(CANDIDATES),
        'window_calendar_days': window_days, 'min_observed_days': min_days,
        'excluded_warmup_dates': skipped,
        'missing_input_dates': [
            (FIRST + timedelta(days=i)).isoformat()
            for i in range((LAST - FIRST).days + 1)
            if (FIRST + timedelta(days=i)).isoformat() not in {r['day'] for r in records}],
        'all_scored_days': summarize(daily, arms),
        'june_validation': summarize(june, [*arms, 'frozen_profit', 'frozen_mae']),
        'frozen_choices_from_january_may': frozen,
        'rolling_disagreement_days': sum(r['rolling_profit_candidate']
                                         != r['rolling_mae_candidate'] for r in daily),
        'limits': [
            'Same candidate panel for both objectives; mean profiles lack retained daily MAE',
            'No new model training or dispatch execution; recorded counterfactual profits reused',
            'June is reused validation data, not an untouched test',
            'Bootstrap blocks count observations, bridging missing calendar dates',
            'Bootstrap conditions on recorded choices; no policy refitting or multiplicity adjustment',
        ],
    }
    return daily, decisions, summary
