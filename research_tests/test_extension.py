import unittest

import numpy as np

from gridmind_research.battery import ETA, BatteryBatch, mpc_action, project, settlement


class BatteryTests(unittest.TestCase):
    def ep(self):
        return {
            "start": "unit",
            "net": np.ones((16, 6)) * 0.2,
            "lag": np.ones(6) * 0.1,
            "hours": np.arange(16) / 4 + 16,
        }

    def test_random_constraints_terminal(self):
        rng = np.random.default_rng(9)
        soc = np.ones((30, 6))
        for t in range(16):
            old = soc.copy()
            soc, ac = project(soc, rng.uniform(-2, 2, soc.shape), 16 - t)
            self.assertTrue(np.all(soc >= 0.2 - 1e-9) & np.all(soc <= 1.8 + 1e-9))
            self.assertLessEqual(np.abs(ac).max(), 0.5 + 1e-9)
            np.testing.assert_allclose(soc - old, np.where(ac >= 0, ac * ETA, ac / ETA), atol=1e-12)
        np.testing.assert_allclose(soc, 1, atol=1e-9)

    def test_current_target_hidden(self):
        e = self.ep()
        a = BatteryBatch([e])
        b = BatteryBatch([{**e, "net": e["net"] * 99}])
        np.testing.assert_array_equal(a.obs(), b.obs())

    def test_idle_zero_increment(self):
        e = BatteryBatch([self.ep()])
        for t in range(16):
            _, r, _, _ = e.step(np.zeros((1, 6)))
            np.testing.assert_allclose(r, 0, atol=1e-10)

    def test_cash_energy_identity(self):
        n = np.array([[-0.7, -0.2, 0.1, 0.4, 0.6, 0.2]])
        cost, pin, pout, res = settlement(n, np.array([0.3]))
        gi = np.maximum(n, 0) - pin
        ge = np.maximum(-n, 0) - pout
        self.assertAlmostEqual(cost.sum(), 0.3 * gi.sum() - 0.08 * ge.sum() + 0.02 * pin.sum())
        self.assertAlmostEqual(res[0], 0)

    def test_terminal_recharge_cost(self):
        soc, ac = project(np.array([[0.6]]), np.array([[0.0]]), 1)
        self.assertAlmostEqual(soc.item(), 1)
        self.assertGreater(ac.item(), 0)

    def test_mpc_future_hidden(self):
        e = self.ep()
        a = BatteryBatch([e])
        b = BatteryBatch([{**e, "net": e["net"] * 99}])
        np.testing.assert_allclose(mpc_action(a), mpc_action(b))

    def test_mpc_episode_feasible(self):
        e = BatteryBatch([self.ep()])
        for t in range(16):
            e.step(mpc_action(e))
        np.testing.assert_allclose(e.soc, 1, atol=1e-9)


try:
    import torch

    from gridmind_research.battery import load_episodes
    from gridmind_research.learned_control import Policy, rollout
except ImportError:
    torch = None


@unittest.skipIf(torch is None, "Install extension dependencies")
class LearningTests(unittest.TestCase):
    def test_actor_locality(self):
        for kind in ["IPPO", "MAPPO"]:
            m = Policy(kind)
            x = torch.zeros(1, 6, 12)
            before = m.actor(x)[0, 0].detach()
            x[0, 1:] = 99
            torch.testing.assert_close(before, m.actor(x)[0, 0])

    def test_gradient_both_networks(self):
        for kind in ["IPPO", "MAPPO"]:
            m = Policy(kind)
            x = torch.randn(3, 6, 12)
            loss = (
                -m.distribution(x).log_prob(torch.zeros(3, 6, dtype=torch.long)).mean()
                + m.value(x).square().mean()
            )
            loss.backward()
            for part in [m.actor, m.critic]:
                self.assertGreater(sum(float(p.grad.abs().sum()) for p in part.parameters()), 0)

    def test_checkpoint_replay(self):
        from pathlib import Path

        import pandas as pd

        path = Path("results/extension/models/MAPPO_seed11.pt")
        if not path.exists():
            self.skipTest("Train first")
        s = torch.load(path, weights_only=True)
        m = Policy("MAPPO")
        m.load_state_dict(s["state_dict"])
        e = load_episodes("test")[0]
        r, _ = rollout(m, [e])
        d = pd.read_csv("results/extension/household_episode_results.csv")
        d = d[(d.method == "MAPPO") & (d.seed == 11) & (d.start == e["start"])].sort_values(
            "household"
        )
        np.testing.assert_allclose(r["cost"][0], d.cost_eur.to_numpy(), atol=1e-9)
