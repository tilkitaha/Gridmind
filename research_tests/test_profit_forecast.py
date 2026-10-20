import unittest
from datetime import date, timedelta

from gridmind_research.profit_forecast import CANDIDATES, choose_forecast, evaluate


def records(n=40):
    return [{'day': (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
             **{k: float(j) for j, k in enumerate(CANDIDATES)}} for i in range(n)]


class ProfitForecastTests(unittest.TestCase):
    def test_selection_uses_profit_and_excludes_oracle(self):
        rows = records()
        for r in rows:
            r['oracle'] = 100000
        daily, report = evaluate(rows)
        self.assertEqual(daily[0]['selected_forecast'], 'profile_28d')
        self.assertEqual(report['evaluated_days'], 26)
        self.assertEqual(report['methods_on_identical_days']['selected_profit']['eur_per_day'], 4)

    def test_same_day_and_future_returns_cannot_change_choice(self):
        rows = records()
        day = date(2026, 1, 20)
        before = choose_forecast(rows, day)
        for r in rows:
            if r['day'] >= day.isoformat():
                r['lear'] = 1e12
        self.assertEqual(before, choose_forecast(rows, day))

    def test_calendar_window_and_missing_days(self):
        self.assertIsNone(choose_forecast(records(14), date(2026, 3, 1)))
        self.assertIsNone(choose_forecast(records(13), date(2026, 1, 20)))

    def test_tie_order_is_deterministic(self):
        rows = records(14)
        for r in rows:
            r.update({k: 0 for k in CANDIDATES})
        self.assertEqual(choose_forecast(rows, date(2026, 1, 15))[0], 'lear')

    def test_reject_invalid_and_test_dates(self):
        for bad in ('2026-07-01', '2025-12-31'):
            rows = records()
            rows[-1]['day'] = bad
            with self.assertRaises(ValueError):
                evaluate(rows)
        for mutation in ('nan', 'duplicate', 'unsorted'):
            rows = records()
            if mutation == 'nan':
                rows[0]['lear'] = float('nan')
            elif mutation == 'duplicate':
                rows[1]['day'] = rows[0]['day']
            else:
                rows.reverse()
            with self.assertRaises(ValueError):
                evaluate(rows)

    def test_all_baselines_share_scored_dates(self):
        daily, report = evaluate(records())
        self.assertEqual(daily[0]['day'], '2026-01-15')
        for k in CANDIDATES:
            self.assertEqual(report['methods_on_identical_days'][k]['total_eur'],
                             sum(r[k] for r in daily))


if __name__ == '__main__':
    unittest.main()
