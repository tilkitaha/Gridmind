import unittest

import numpy as np
import pandas as pd

from gridmind_research.forecast_control import predict
from gridmind_research.polish_market import (
    BESS,
    check_schedule,
    delivery_index,
    gate_closure,
    optimize_schedule,
    realized_profit,
    validate_day,
)


class MarketExtensionTests(unittest.TestCase):
    def test_dst_delivery_periods_and_gate(self):
        for day,n in [("2026-03-29",92),("2026-10-25",100),("2026-07-01",96)]:
            idx=delivery_index(day)
            self.assertEqual(len(idx),n)
            self.assertTrue(idx.is_unique)
            self.assertEqual(gate_closure(day).tz_convert("Europe/Warsaw").hour,12)

    def frame(self):
        return pd.DataFrame({"timestamp_utc":delivery_index("2026-07-01").astype(str),"value_eur_mwh":np.ones(96),"issued_at":"2026-06-30T09:00:00Z"})

    def test_data_contract_rejects_bad_clock_and_leakage(self):
        f=self.frame()
        self.assertEqual(len(validate_day(f,"2026-07-01",True)),96)
        for bad in [f.iloc[:-1],f.iloc[::-1],f.assign(timestamp_utc="2026-07-01 00:00:00"),f.assign(value_eur_mwh=np.nan),f.assign(issued_at=gate_closure("2026-07-01").isoformat())]:
            with self.assertRaises(ValueError):validate_day(bad,"2026-07-01",True)

    def test_flat_positive_prices_leave_battery_idle(self):
        s=optimize_schedule(np.full(96,100.))
        self.assertLess(abs(realized_profit(s,np.full(96,100.))),1e-7)
        self.assertLess(np.sum(s["charge_mw"]+s["discharge_mw"]),1e-7)

    def test_two_slot_arbitrage_matches_analytic_solution(self):
        spec=BESS(eta_ch=1.,eta_dis=1.,degradation_eur_mwh=0.)
        s=optimize_schedule([0.,100.],spec)
        self.assertAlmostEqual(realized_profit(s,[0.,100.],spec),25.,places=6)
        np.testing.assert_allclose(s["energy_mwh"],[1.25,1.],atol=1e-7)

    def test_negative_prices_cannot_simultaneously_cycle(self):
        p=np.array([-500.,-500.,-400.,-400.,30.,50.,70.,100.])
        s=optimize_schedule(p)
        self.assertTrue(check_schedule(s))
        self.assertLess(np.minimum(s["charge_mw"],s["discharge_mw"]).max(),1e-7)

    def test_wrong_forecast_changes_realized_profit(self):
        spec=BESS(eta_ch=1.,eta_dis=1.,degradation_eur_mwh=0.)
        actual=np.array([0.,100.])
        correct=optimize_schedule(actual,spec)
        wrong=optimize_schedule(actual[::-1],spec)
        self.assertAlmostEqual(realized_profit(correct,actual,spec),25.,places=6)
        self.assertAlmostEqual(realized_profit(wrong,actual,spec),-25.,places=6)

    def test_grid_limit_and_terminal_inventory_are_enforced(self):
        spec=BESS(grid_mw=.1)
        s=optimize_schedule([0.,200.],spec)
        self.assertLess(max(s["charge_mw"].max(),s["discharge_mw"].max()),.1+1e-7)
        corrupt={k:v.copy() for k,v in s.items()}
        corrupt["energy_mwh"][-1]+=.01
        with self.assertRaises(ValueError):check_schedule(corrupt,spec)

    def test_causal_load_forecasts_ignore_future_measurements(self):
        class FakeRidge:
            def predict(self,x):return x[:,:6]*.9+x[:,6:12]*.1
        idx=pd.date_range("2020-06-01",periods=300,freq="15min")
        h=pd.DataFrame(np.arange(1800).reshape(300,6)/1000,index=idx)
        current=idx[200]
        altered=h.copy();altered.loc[current:]=9999.
        for method in ["persistence","daily","ridge"]:
            a,_=predict(h,current,16,method,FakeRidge())
            b,_=predict(altered,current,16,method,FakeRidge())
            np.testing.assert_array_equal(a,b)

    def test_daily_missing_rule_is_fixed_and_finite(self):
        idx=pd.date_range("2020-06-01",periods=110,freq="15min")
        h=pd.DataFrame(np.ones((110,6)),index=idx)
        h.loc[idx[4],0]=np.nan
        p,count=predict(h,idx[100],3,"daily")
        self.assertEqual(count,1)
        self.assertTrue(np.isfinite(p).all())


if __name__=="__main__":unittest.main()
