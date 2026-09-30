import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from gridmind_research.clearing import clear
from gridmind_research.data import prepare
from gridmind_research.forecast import build_features
from gridmind_research.metrics import benefit_metrics, cvar, paired_block_ci


class ResearchTests(unittest.TestCase):
    def test_energy_and_money_conservation(self):
        r = clear([-2, 1, 3], [0.3] * 3, [0.1] * 3, fee=0.02)
        self.assertAlmostEqual(sum(t["kwh"] for t in r.trades), 2)
        self.assertAlmostEqual(r.community_benefit_eur, 0.36)
        self.assertAlmostEqual(r.grid_import_kwh.sum() - r.grid_export_kwh.sum(), 2)
        self.assertTrue((r.benefit_eur >= 0).all())

    def test_homogeneous_tariff_invariance(self):
        args = ([-3, 1, 4], [0.3] * 3, [0.1] * 3)
        a, b = clear(*args), clear(*args, policy="welfare_lp")
        self.assertAlmostEqual(a.community_benefit_eur, b.community_benefit_eur)

    def test_fairness_floor_and_improvement(self):
        args = ([-1, 1, 1], [0.3, 0.4, 0.2], [0.1] * 3)
        r = clear(*args, policy="nash_guarded", welfare_tolerance=0.2)
        self.assertGreaterEqual(r.community_benefit_eur + 1e-7, 0.8 * r.welfare_bound_eur)
        self.assertGreater(r.benefit_eur[2], 0)
        self.assertEqual(r.solver_status, "converged_nash")

    def test_no_profitable_pair(self):
        r = clear([-1, 1], [0.1, 0.05], [0.1, 0.1])
        self.assertEqual(len(r.trades), 0)

    def test_negative_prices_are_allowed(self):
        r = clear([-1, 1], [-0.1, -0.1], [-0.2, -0.2])
        self.assertAlmostEqual(r.community_benefit_eur, 0.1)

    def test_zero_is_not_perfect_fairness(self):
        self.assertIsNone(benefit_metrics([0, 0])["jain"])
        self.assertIsNone(benefit_metrics([0, 0])["gini"])

    def test_losses_not_hidden(self):
        m = benefit_metrics([-1, 3])
        self.assertIsNone(m["jain"])
        self.assertEqual(m["negative_fraction"], 0.5)

    def test_fractional_cvar(self):
        self.assertAlmostEqual(cvar([0, 10, 20], 0.5), 50 / 3)
        self.assertAlmostEqual(cvar([0, 10, 20], 0.95), 20)

    def test_paired_bootstrap_identical(self):
        r = paired_block_ci(np.arange(14), np.arange(14))
        self.assertEqual(r["ci95_low"], 0)
        self.assertEqual(r["ci95_high"], 0)

    def test_invalid_input_rejected(self):
        for args in [([-1, np.nan], [0.3] * 2, [0.1] * 2), ([-1, 1], [0.3], [0.1] * 2)]:
            with self.assertRaises(ValueError):
                clear(*args)
        with self.assertRaises(ValueError):
            clear([-1, 1], [0.3] * 2, [0.1] * 2, scale=[0, 1])

    def test_empty_side_grid_only(self):
        r = clear([1, 2], [0.3] * 2, [0.1] * 2)
        np.testing.assert_allclose(r.grid_import_kwh, [1, 2])

    def test_permutation_preserves_welfare(self):
        net = np.array([-2.0, -1, 1, 2, 4])
        buy = np.array([0.3, 0.3, 0.2, 0.4, 0.3])
        sell = np.array([0.08, 0.1, 0.08, 0.08, 0.08])
        r = clear(net, buy, sell, policy="welfare_lp")
        p = [3, 1, 4, 0, 2]
        s = clear(net[p], buy[p], sell[p], policy="welfare_lp")
        self.assertAlmostEqual(r.community_benefit_eur, s.community_benefit_eur)

    def test_power_conversion_and_missing_interval(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for i in range(1, 7):
                d = pd.DataFrame(
                    {
                        "date": pd.date_range("2020-06-01", periods=30, freq="min"),
                        "Consumption(W)": 1000.0,
                        "Production(W)": 0.0,
                        f"H{i}_W": 1.0,
                    }
                )
                if i == 1:
                    d.loc[29, "Consumption(W)"] = np.nan
                d.to_csv(root / f"H{i}_W.csv", index=False)
            data, _ = prepare(root, root / "out")
            self.assertAlmostEqual(data.iloc[0]["H1_load_kwh"], 0.25)
            self.assertTrue(np.isnan(data.iloc[1]["H1_load_kwh"]))

    def test_future_measurements_cannot_change_current_features(self):
        idx = pd.date_range("2020-01-01", periods=800, freq="15min")
        d = pd.DataFrame(
            {
                **{f"H{i}_load_kwh": np.arange(800) * 0.001 for i in range(1, 7)},
                **{f"H{i}_pv_kwh": np.zeros(800) for i in range(1, 7)},
            },
            index=idx,
        )
        original, _ = build_features(d)
        d.iloc[750:, :] = 1000000
        changed, _ = build_features(d)
        # Includes t=750: its unknown target cannot enter its own features.
        pd.testing.assert_frame_equal(original.iloc[:751], changed.iloc[:751])


if __name__ == "__main__":
    unittest.main()
