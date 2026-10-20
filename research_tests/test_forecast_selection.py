import copy
import unittest
from datetime import date, timedelta

from gridmind_research.forecast_selection import (
    CANDIDATES,
    FREEZE,
    evaluate,
    paired_interval,
    select,
    validate,
)


def records(n=40, first=date(2026, 1, 1)):
    return [{'day': (first + timedelta(days=i)).isoformat(),
             **{f'{k}_{metric}': float(j + 1) for j, k in enumerate(CANDIDATES)
                for metric in ('eur', 'mae')}} for i in range(n)]


class ForecastSelectionTests(unittest.TestCase):
    def test_matched_panel_selects_different_objectives(self):
        daily, decisions, summary = evaluate(records())
        self.assertEqual(len(daily), 26)
        self.assertEqual(daily[0]['rolling_profit_candidate'], 'naive_d7')
        self.assertEqual(daily[0]['rolling_mae_candidate'], 'lear')
        self.assertEqual(daily[0]['rolling_profit_eur'], 4)
        self.assertEqual(summary['rolling_disagreement_days'], 26)
        self.assertEqual(decisions[0]['history_days'], decisions[1]['history_days'])
        self.assertEqual(summary['all_scored_days']['comparisons']
                         ['rolling_profit_minus_rolling_mae']['mean_eur_per_day'], 3)

    def test_target_and_future_cannot_affect_any_selection_scores(self):
        rows = records()
        day = date(2026, 1, 20)
        before = [select(rows, day, obj) for obj in ('profit', 'mae')]
        for row in rows:
            if row['day'] >= day.isoformat():
                row.update({f'{k}_eur': 1e9 for k in CANDIDATES})
                row.update({f'{k}_mae': 0 for k in CANDIDATES})
        self.assertEqual(before, [select(rows, day, obj) for obj in ('profit', 'mae')])

    def test_frozen_choice_ignores_all_june_outcomes(self):
        rows = records(61, date(2026, 5, 1))
        before = evaluate(rows)[2]['frozen_choices_from_january_may']
        for row in rows:
            if row['day'] >= FREEZE.isoformat():
                row['lear_eur'], row['naive_d7_mae'] = 1000, 0
        daily, _, after = evaluate(rows)
        self.assertEqual(before, after['frozen_choices_from_january_may'])
        june = [r for r in daily if r['day'] >= FREEZE.isoformat()]
        self.assertTrue(all(r['frozen_profit_candidate'] == 'naive_d7' for r in june))
        self.assertTrue(all(r['frozen_mae_candidate'] == 'lear' for r in june))
        self.assertTrue(any(r['rolling_profit_candidate'] == 'lear' for r in june))

    def test_missing_dates_are_not_rows_or_zero_returns(self):
        rows = records(30)
        rows.pop(10)
        decision = select(rows, date(2026, 1, 16), 'profit')
        self.assertEqual(decision['history_days'], 14)
        self.assertIsNone(select(rows, date(2026, 3, 1), 'profit'))

    def test_ties_follow_candidate_order(self):
        rows = records(14)
        for row in rows:
            row.update({f'{k}_{m}': 1 for k in CANDIDATES for m in ('eur', 'mae')})
        for obj in ('profit', 'mae'):
            self.assertEqual(select(rows, date(2026, 1, 15), obj)['candidate'], 'lear')

    def test_rejects_bad_panel_and_heldout_dates(self):
        mutations = [
            lambda r: r[0].update(day='2026-07-01'),
            lambda r: r[0].update(lear_mae=-1),
            lambda r: r[0].update(lear_eur=float('inf')),
            lambda r: r[0].pop('gbm_mae'),
            lambda r: r[1].update(day=r[0]['day']),
            lambda r: r.reverse(),
        ]
        for mutate in mutations:
            rows = copy.deepcopy(records())
            mutate(rows)
            with self.assertRaises(ValueError):
                validate(rows)

    def test_bootstrap_constant_paired_difference(self):
        result = paired_interval([3.0] * 20)
        self.assertEqual(result['lower95'], 3)
        self.assertEqual(result['upper95'], 3)
        self.assertEqual(result, paired_interval([3.0] * 20))
        with self.assertRaises(ValueError):
            paired_interval([float('nan')] * 20)

    def test_invalid_objective_and_history_settings(self):
        for obj, window, minimum in [('oracle', 28, 14), ('profit', 7, 14),
                                     ('mae', 28, 0)]:
            with self.assertRaises(ValueError):
                select(records(), date(2026, 2, 1), obj, window, minimum)


if __name__ == '__main__':
    unittest.main()
