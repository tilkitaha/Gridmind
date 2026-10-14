import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from gridmind_research.polish_market import delivery_index
from gridmind_research.polish_pilot import load_days, pilot, refuse_test_window, summarize


def write_day(folder, day, values):
    idx = delivery_index(day)
    pd.DataFrame({'timestamp_utc': [t.isoformat() for t in idx], 'value_eur_mwh': values(len(idx))}).to_csv(
        Path(folder) / f'{day}.csv', index=False)


def daily_shape(n):
    # Cheap night, expensive evening, as a smooth daily curve.
    return 80 + 60 * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, n))


class PolishPilotTests(unittest.TestCase):
    def test_test_window_is_closed_until_frozen(self):
        with self.assertRaises(PermissionError):
            refuse_test_window('2026-06-20', '2026-07-02')
        refuse_test_window('2025-10-01', '2026-06-30')
        with tempfile.TemporaryDirectory() as d:
            p = json.loads(Path('configs/polish_market_protocol.json').read_text(encoding='utf-8'))
            p['status'] = 'FROZEN_2026-11-01'
            frozen = Path(d) / 'protocol.json'
            frozen.write_text(json.dumps(p))
            refuse_test_window('2026-07-01', '2026-08-31', frozen)

    def test_pilot_profits_and_clock_change_days(self):
        with tempfile.TemporaryDirectory() as d:
            for day in pd.date_range('2025-10-20', '2025-10-28').strftime('%Y-%m-%d'):
                write_day(d, day, daily_shape)
            (Path(d) / '2025-10-23.csv').write_text('timestamp_utc,value_eur_mwh\n')
            prices, skipped = load_days(d, '2025-10-20', '2025-10-29')
            self.assertEqual(set(skipped), {'2025-10-23', '2025-10-29'})
            daily = pilot(prices)
        by_day = daily.set_index('day')
        self.assertEqual(by_day.loc['2025-10-26', 'mtus'], 100)  # clock change
        self.assertTrue(np.isnan(by_day.loc['2025-10-26', 'naive_d1_eur']))  # 96 versus 100 MTUs
        self.assertTrue((daily.oracle_eur > 0).all())
        both = daily.dropna(subset=['naive_d1_eur'])
        self.assertTrue((both.oracle_eur + 1e-6 >= both.naive_d1_eur).all())
        # An identical previous day is a perfect forecast.
        np.testing.assert_allclose(both.naive_d1_eur, both.oracle_eur, rtol=1e-6)
        s = summarize(daily)
        self.assertEqual(s['days'], 8)
        self.assertGreater(s['oracle_eur_per_day'], 0)


if __name__ == '__main__':
    unittest.main()
