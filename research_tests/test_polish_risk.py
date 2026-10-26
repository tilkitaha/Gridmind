import unittest

import numpy as np

from gridmind_research.polish_market import BESS, check_schedule, optimize_schedule, realized_profit
from gridmind_research.polish_risk import (
    cvar,
    error_scenarios,
    optimize_cvar_schedule,
    scenario_profits,
)


def day(seed, n=96):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return 80 + 60 * np.sin(2 * np.pi * (t - 30) / n) + rng.normal(0, 15, n)


class PolishRiskTests(unittest.TestCase):
    def test_risk_neutral_single_scenario_matches_deterministic_milp(self):
        p = day(1)
        a = realized_profit(optimize_cvar_schedule(p[None, :], weight=0.0), p)
        b = realized_profit(optimize_schedule(p), p)
        self.assertAlmostEqual(a, b, places=4)

    def test_scenarios_add_past_errors_to_the_forecast(self):
        f = np.array([10., 20.])
        s = error_scenarios(f, [[9., 21.], [10., 18.]], [[11., 20.], [10., 22.]])
        np.testing.assert_allclose(s, [[12., 19.], [10., 24.]])
        with self.assertRaises(ValueError):
            error_scenarios(f, [[1., 2., 3.]], [[1., 2., 3.]])

    def test_weight_trades_mean_for_tail(self):
        f = day(2)
        S = np.stack([f + np.random.default_rng(k).normal(0, 60, 96) * (k % 3 == 0) for k in range(24)])
        neutral, averse = optimize_cvar_schedule(S, 0.0), optimize_cvar_schedule(S, 1.0)
        for sched in (neutral, averse):
            self.assertTrue(check_schedule(sched))
        pn, pa = scenario_profits(neutral, S), scenario_profits(averse, S)
        self.assertGreaterEqual(pn.mean(), pa.mean() - 1e-6)
        self.assertGreaterEqual(cvar(pa, 0.2), cvar(pn, 0.2) - 1e-6)

    def test_scenario_profit_matches_realized_profit(self):
        p = day(3)
        s = optimize_schedule(p)
        self.assertAlmostEqual(scenario_profits(s, p[None, :])[0], realized_profit(s, p), places=8)

    def test_rejects_bad_parameters(self):
        S = day(4)[None, :]
        for kw in ({'weight': -0.1}, {'weight': 1.1}, {'weight': 0.5, 'alpha': 0.0}):
            with self.assertRaises(ValueError):
                optimize_cvar_schedule(S, **kw)
        with self.assertRaises(ValueError):
            optimize_cvar_schedule(day(4), 0.5)
        self.assertEqual(BESS().degradation_eur_mwh, 10.0)


if __name__ == '__main__':
    unittest.main()
