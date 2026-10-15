import unittest

import numpy as np
import torch

from gridmind_research.polish_market import optimize_schedule, realized_profit
from gridmind_research.polish_rl import (
    E0,
    PPO,
    Policy,
    T,
    observe,
    project,
    rule_profit,
    run_days,
    step_profit,
    train,
)


def prices(seed=0):
    rng = np.random.default_rng(seed)
    return 80 + 60 * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, T)) + rng.normal(0, 15, T)


class PolishRLTests(unittest.TestCase):
    def test_environment_reproduces_the_milp_schedule_profit(self):
        for seed in range(3):
            p = prices(seed)
            s = optimize_schedule(p)
            energy, total = np.array([E0]), 0.0
            for t in range(T):
                energy, ac = project(energy, np.array([s['charge_mw'][t] - s['discharge_mw'][t]]), T - t)
                total += step_profit(ac, p[t])[0]
                np.testing.assert_allclose(energy[0], s['energy_mwh'][t], atol=1e-6)
            np.testing.assert_allclose(total, realized_profit(s, p), atol=1e-6)

    def test_projection_always_returns_to_the_start_level(self):
        rng = np.random.default_rng(1)
        energy = np.full(64, E0)
        for t in range(T):
            energy, _ = project(energy, rng.uniform(-3, 3, 64), T - t)
            self.assertTrue((energy >= 0.2 - 1e-9).all() and (energy <= 1.8 + 1e-9).all())
        np.testing.assert_allclose(energy, E0, atol=1e-9)

    def test_observation_has_no_realized_prices(self):
        f = np.stack([prices(2), prices(3)])
        x = observe(f, np.full(2, E0), 10)
        self.assertEqual(x.shape, (2, 4 + T))
        # Same forecast, different realized prices: the same actions (so the same throughput), different profit.
        torch.manual_seed(0)
        m = Policy()
        a, ta = run_days(m, f, np.stack([prices(4), prices(5)]))
        b, tb = run_days(m, f, np.stack([prices(6), prices(7)]))
        np.testing.assert_array_equal(ta, tb)
        self.assertFalse(np.allclose(a, b))

    def test_threshold_rule_is_bounded_by_the_milp_and_idles_with_no_slots(self):
        for seed in range(3):
            p = prices(seed)
            best = realized_profit(optimize_schedule(p), p)
            self.assertEqual(rule_profit(p, p, 0), 0.0)
            for k in (4, 10, 24):
                self.assertLessEqual(rule_profit(p, p, k), best + 1e-6)
            self.assertGreater(rule_profit(p, p, 10), 0.0)

    def test_short_training_runs_and_selects_a_checkpoint(self):
        f = np.stack([prices(s) for s in range(12)])
        cfg = dict(PPO, updates=10, days_per_update=4)
        m, info = train(0, f[:8], f[:8], f[8:], f[8:], cfg)
        self.assertEqual(info['selected_update'], 10)
        profit, through = run_days(m, f[8:], f[8:])
        self.assertTrue(np.isfinite(profit).all() and (through >= 0).all())


if __name__ == '__main__':
    unittest.main()
