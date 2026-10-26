import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from gridmind_research.polish_forecast import (
    GBM,
    diebold_mariano,
    lear,
    local_slots,
    naive,
    price_matrix,
    profile,
)
from gridmind_research.polish_market import delivery_index


def frame(day, values):
    idx = delivery_index(day)
    return pd.DataFrame({'timestamp_utc': [t.isoformat() for t in idx], 'value_eur_mwh': values(len(idx))})


def synthetic_matrix(days=90, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2025-10-01', periods=days)
    shape = 80 + 60 * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, 96))
    return pd.DataFrame([shape * (1 + 0.1 * d.weekday() / 6) + rng.normal(0, 5, 96) for d in idx], index=idx)


class PolishForecastTests(unittest.TestCase):
    def test_clock_change_days_map_to_96_local_slots(self):
        long_day = local_slots(frame('2025-10-26', lambda n: np.arange(n, dtype=float)))
        self.assertEqual(len(long_day), 96)
        # 02:00-02:45 occurs twice (positions 8-11 and 12-15); the slot holds their mean.
        np.testing.assert_allclose(long_day[8:12], (np.arange(8, 12) + np.arange(12, 16)) / 2)
        self.assertEqual(long_day[12], 16)
        short_day = local_slots(frame('2026-03-29', lambda n: np.arange(n, dtype=float)))
        self.assertEqual(len(short_day), 96)
        self.assertTrue(np.isfinite(short_day).all())  # skipped 02:00-02:45 interpolated
        self.assertEqual(short_day[12], 8)  # 03:00 is the ninth market time unit

    def test_forecasts_do_not_read_the_target_day_or_later(self):
        m = synthetic_matrix()
        day = m.index[80]
        changed = m.copy()
        changed.loc[day:] = 9999.0
        np.testing.assert_array_equal(naive(m, day, 1), naive(changed, day, 1))
        np.testing.assert_allclose(lear(m, day), lear(changed, day))
        np.testing.assert_allclose(GBM()(m, day), GBM()(changed, day))
        np.testing.assert_array_equal(profile(m, day, 7), profile(changed, day, 7))
        np.testing.assert_allclose(profile(m, day, 2), m.iloc[78:80].mean(0).to_numpy())

    def test_exogenous_models_use_only_inputs_available_at_the_gate(self):
        m = synthetic_matrix()
        rng = np.random.default_rng(3)
        idx = m.index
        exog = {'load_fc': pd.DataFrame(rng.normal(19000, 800, (len(idx), 96)), index=idx),
                'load_act': pd.DataFrame(rng.normal(19000, 800, (len(idx), 96)), index=idx),
                'res': pd.DataFrame({'solar': rng.normal(2000, 300, len(idx)), 'wind': rng.normal(2500, 400, len(idx))}, index=idx)}
        day = idx[80]
        changed = {k: v.copy() for k, v in exog.items()}
        # Actual load and generation of D-1 and later are not yet complete at the D-1 gate.
        changed['load_act'].loc[day - pd.Timedelta(days=1):] = -1.0
        changed['res'].loc[day - pd.Timedelta(days=1):] = -1.0
        changed['load_fc'].loc[day + pd.Timedelta(days=1):] = -1.0
        m2 = m.copy()
        m2.loc[day:] = 9999.0
        np.testing.assert_allclose(lear(m, day, exog=exog), lear(m2, day, exog=changed))
        np.testing.assert_allclose(GBM(exog=exog)(m, day), GBM(exog=changed)(m2, day))

    def test_lear_learns_a_stable_daily_shape(self):
        m = synthetic_matrix(seed=1)
        f = lear(m, m.index[85])
        self.assertEqual(f.shape, (96,))
        self.assertLess(np.abs(f - m.loc[m.index[85]].to_numpy()).mean(), np.abs(m.loc[m.index[85]].to_numpy() - m.values.mean()).mean())

    def test_price_matrix_refuses_the_test_window(self):
        # Independent of the repository protocol's status: a draft protocol keeps July-August closed.
        draft = (pd.Timestamp('2026-07-01'), pd.Timestamp('2026-08-31'), False)
        with tempfile.TemporaryDirectory() as d, self.assertRaises(PermissionError), \
                mock.patch('gridmind_research.polish_pilot.candidate_test_window', return_value=draft):
            price_matrix(Path(d), '2026-06-01', '2026-07-10')

    def test_diebold_mariano_signs(self):
        rng = np.random.default_rng(2)
        a = rng.normal(1.0, 0.2, 200)
        better = a - 0.3 + rng.normal(0, 0.1, 200)
        stat, p = diebold_mariano(better, a)  # lower loss first: negative statistic
        self.assertLess(stat, 0)
        self.assertLess(p, 1e-6)
        stat, p = diebold_mariano(a + rng.normal(0, 0.1, 200), a + rng.normal(0, 0.1, 200))
        self.assertGreater(p, 0.01)


if __name__ == '__main__':
    unittest.main()
