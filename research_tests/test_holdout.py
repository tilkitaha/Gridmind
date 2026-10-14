import unittest

import numpy as np
import pandas as pd

from gridmind_research.battery import BatteryBatch, load_episodes, mpc_action
from gridmind_research.holdout import (
    YEAR,
    Forecaster,
    block_bootstrap,
    decide,
    eligibility,
    lp_plan,
    net_load,
    ridge_params,
    run_episodes,
)


def synthetic(households, missing=None):
    d = pd.DataFrame(index=YEAR)
    for h in households:
        d[f'{h}_load_kwh'] = 0.1
        d[f'{h}_pv_kwh'] = 0.0
    for h, idx in (missing or {}).items():
        d.loc[idx, [f'{h}_load_kwh', f'{h}_pv_kwh']] = np.nan
    return d


class HoldoutTests(unittest.TestCase):
    def test_general_lp_matches_mpc_action(self):
        episode = load_episodes('test')[0]
        env = BatteryBatch([episode])
        expected = mpc_action(env, episode['net'])[0]
        np.testing.assert_allclose(lp_plan(episode['net'], episode['hours'])[0], expected, atol=1e-9)

    def test_ridge_refit_reproduces_saved_coefficients(self):
        processed = pd.read_csv('data/storenet_h1_h6_15min.csv', index_col=0, parse_dates=True)
        params = ridge_params(net_load(processed, [f'H{i}' for i in range(1, 7)]))
        saved = np.load('results/forecast_control/ridge_coefficients.npz')
        for k in ['mean', 'scale', 'coef', 'intercept']:
            np.testing.assert_allclose(params[k], saved[k], rtol=1e-12, atol=1e-12)

    def test_forecaster_reads_only_the_past_and_counts_stale_inputs(self):
        raw = net_load(synthetic(['H1', 'H2']), ['H1', 'H2'])
        raw.iloc[:, :] = np.random.default_rng(0).random(raw.shape)
        now = pd.Timestamp('2020-07-10 08:00')
        before = Forecaster(raw, 'persistence')(now, 96)
        changed = raw.copy()
        changed.loc[now:] = 99.0
        np.testing.assert_array_equal(Forecaster(changed, 'persistence')(now, 96), before)
        gap = raw.copy()
        gap.loc[now - pd.Timedelta(minutes=15)] = np.nan
        f = Forecaster(gap, 'persistence')
        np.testing.assert_array_equal(f(now, 4)[0], raw.loc[now - pd.Timedelta(minutes=30)].to_numpy())
        self.assertEqual(f.stale, 1)

    def test_eligibility_uses_coverage_groups_and_day_rules(self):
        houses = [f'H{i}' for i in range(7, 21)]
        july = pd.date_range('2020-07-01', '2020-07-31 23:45', freq='15min')
        sparse_days = pd.date_range('2020-08-01', '2020-12-31 23:45', freq='15min')
        missing = {
            'H9': pd.date_range('2020-07-01', '2020-08-31 23:45', freq='15min'),  # test coverage < 85%
            'H14': july[(july.hour < 4) | ((july.hour == 4) & (july.minute == 0))],  # 79 of 96 observed
        }
        e = eligibility(synthetic(houses, missing), houses)
        edge = eligibility(synthetic(houses, {'H14': july[july.hour < 4]}), houses)  # exactly 80 observed
        self.assertEqual(len(edge['communities'][1]['days']), 184)
        self.assertNotIn('H9', e['eligible'])
        self.assertEqual(len(e['eligible']), 13)
        self.assertEqual([c['households'] for c in e['communities']],
                         [['H7', 'H8', 'H10', 'H11', 'H12', 'H13'], ['H14', 'H15', 'H16', 'H17', 'H18', 'H19']])
        self.assertEqual(e['excluded_remainder'], ['H20'])
        self.assertEqual(len(e['communities'][0]['days']), 184)
        self.assertEqual(len(e['communities'][1]['days']), len(set(sparse_days.date)))
        self.assertTrue(all(c['included'] for c in e['communities']))

    def test_oracle_episode_is_feasible_and_not_worse_than_idle(self):
        raw = net_load(synthetic(['H1', 'H2']), ['H1', 'H2'])
        df = run_episodes(raw, [pd.Timestamp('2020-07-01')], 96)
        self.assertTrue((df.saving_eur >= -1e-9).all())
        self.assertGreater(df.saving_eur.sum(), 0)  # flat load still gains from the time-of-use spread

    def test_block_bootstrap_ratio_and_joint_dates(self):
        dates = pd.date_range('2020-07-01', periods=50).strftime('%Y-%m-%d')
        den = pd.DataFrame({'C1': 20.0, 'C2': 10.0}, index=dates)
        den.loc[dates[:10], 'C2'] = 0.0  # ineligible community-days contribute nothing
        num = den * 0.03
        r = block_bootstrap(num, den, draws=500)
        self.assertAlmostEqual(r['estimate'], 0.03)
        self.assertAlmostEqual(r['lower95'], 0.03)
        self.assertAlmostEqual(r['upper95'], 0.03)
        noisy = num + pd.DataFrame(np.random.default_rng(1).normal(0, 0.2, num.shape), index=dates, columns=num.columns)
        r = block_bootstrap(noisy, den, draws=500)
        self.assertLess(r['lower95'], r['estimate'])
        self.assertLess(r['estimate'], r['upper95'])

    def test_decision_table(self):
        self.assertTrue(decide(0.02, 0.05).startswith('H1 supported'))
        self.assertTrue(decide(0.005, 0.05).startswith('Positive saving'))
        self.assertTrue(decide(-0.01, 0.05).startswith('Inconclusive'))
        self.assertTrue(decide(-0.05, -0.01).startswith('Ridge MPC 24 h raises cost'))


if __name__ == '__main__':
    unittest.main()
