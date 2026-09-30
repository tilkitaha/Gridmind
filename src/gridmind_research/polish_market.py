"""Verified components for the proposed Polish BESS study, not market results.

No exchange connection, bid acceptance, imbalance settlement or live trading.
Prices must be supplied from an audited source. Fixed-schedule price-taking
evaluation assumes the submitted volumes are fully accepted.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

ZONE = "Europe/Warsaw"


def delivery_index(day):
    start = pd.Timestamp(day).normalize()
    if start.tzinfo is not None:
        raise ValueError("Supply a local delivery date, not a zoned instant")
    end = start + pd.Timedelta(days=1)
    return pd.date_range(start.tz_localize(ZONE), end.tz_localize(ZONE), freq="15min", inclusive="left").tz_convert("UTC")


def gate_closure(day):
    return (pd.Timestamp(day).normalize() - pd.Timedelta(days=1) + pd.Timedelta(hours=12)).tz_localize(ZONE).tz_convert("UTC")


def validate_day(frame, day, forecast=False):
    required = {"timestamp_utc", "value_eur_mwh"} | ({"issued_at"} if forecast else set())
    if not required.issubset(frame.columns):
        raise ValueError("Missing required fields")
    times = [pd.Timestamp(x) for x in frame.timestamp_utc]
    if any(x.tzinfo is None for x in times):
        raise ValueError("All timestamps require explicit UTC offsets")
    idx = pd.DatetimeIndex(times).tz_convert("UTC")
    if not idx.equals(delivery_index(day)):
        raise ValueError("Missing, duplicate, unordered or wrong-resolution MTUs")
    values = pd.to_numeric(frame.value_eur_mwh, errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Non-finite price")
    if forecast:
        issues = [pd.Timestamp(x) for x in frame.issued_at]
        if any(x.tzinfo is None for x in issues):
            raise ValueError("Issue timestamps require explicit UTC offsets")
        if any(x.tz_convert("UTC") >= gate_closure(day) for x in issues):
            raise ValueError("Forecast not available strictly before gate closure")
    return values


@dataclass(frozen=True)
class BESS:
    energy_mwh: float = 2.0
    power_mw: float = 1.0
    grid_mw: float = 1.0
    eta_ch: float = 0.95
    eta_dis: float = 0.95
    min_fraction: float = 0.10
    max_fraction: float = 0.90
    target_fraction: float = 0.50
    degradation_eur_mwh: float = 10.0
    dt_hours: float = 0.25

    def validate(self):
        values = np.asarray(list(self.__dict__.values()), dtype=float)
        if not np.isfinite(values).all() or min(self.energy_mwh, self.power_mw, self.grid_mw, self.dt_hours) <= 0:
            raise ValueError("Invalid physical scale")
        if not 0 < self.eta_ch <= 1 or not 0 < self.eta_dis <= 1:
            raise ValueError("Invalid efficiency")
        if not 0 <= self.min_fraction <= self.target_fraction <= self.max_fraction <= 1 or self.degradation_eur_mwh < 0:
            raise ValueError("Invalid inventory or degradation parameter")


def optimize_schedule(forecast_eur_mwh, spec=BESS()):
    """Deterministic MILP; binary mode prevents negative-price loss cycling."""
    spec.validate()
    price = np.asarray(forecast_eur_mwh, dtype=float)
    if price.ndim != 1 or not len(price) or not np.isfinite(price).all():
        raise ValueError("Expected finite 1-D prices")
    n = len(price)
    dt, power = spec.dt_hours, min(spec.power_mw, spec.grid_mw)
    c = np.r_[(price + spec.degradation_eur_mwh)*dt, (-price + spec.degradation_eur_mwh)*dt, np.zeros(2*n)]
    lo = np.r_[np.zeros(2*n), np.full(n, spec.energy_mwh*spec.min_fraction), np.zeros(n)]
    hi = np.r_[np.full(2*n, power), np.full(n, spec.energy_mwh*spec.max_fraction), np.ones(n)]
    target = spec.energy_mwh * spec.target_fraction
    lo[3*n-1] = hi[3*n-1] = target
    A = lil_matrix((3*n, 4*n))
    lower = np.full(3*n, -np.inf)
    upper = np.zeros(3*n)
    for t in range(n):
        A[t, 2*n+t] = 1
        A[t, t] = -spec.eta_ch*dt
        A[t, n+t] = dt/spec.eta_dis
        if t:
            A[t, 2*n+t-1] = -1
        lower[t] = upper[t] = target if t == 0 else 0
        A[n+t, t] = 1
        A[n+t, 3*n+t] = -power
        A[2*n+t, n+t] = 1
        A[2*n+t, 3*n+t] = power
        upper[2*n+t] = power
    result = milp(c, integrality=np.r_[np.zeros(3*n), np.ones(n)], bounds=Bounds(lo, hi), constraints=LinearConstraint(A.tocsr(), lower, upper), options={"mip_rel_gap":1e-9,"time_limit":60})
    if not result.success:
        raise RuntimeError("Schedule optimization did not establish optimality")
    charge, discharge, energy = np.split(result.x[:3*n], 3)
    schedule = dict(charge_mw=charge, discharge_mw=discharge, energy_mwh=energy)
    check_schedule(schedule, spec)
    return schedule


def check_schedule(schedule, spec=BESS(), tol=1e-7):
    spec.validate()
    ch, dis, e = [np.asarray(schedule[k], dtype=float) for k in ["charge_mw","discharge_mw","energy_mwh"]]
    if ch.ndim != 1 or not len(ch) or ch.shape != dis.shape or ch.shape != e.shape or not np.isfinite(np.r_[ch,dis,e]).all():
        raise ValueError("Invalid schedule dimensions")
    target = spec.energy_mwh*spec.target_fraction
    expected = np.r_[target,e[:-1]] + spec.eta_ch*ch*spec.dt_hours - dis*spec.dt_hours/spec.eta_dis
    power = min(spec.power_mw,spec.grid_mw)
    valid = min(ch.min(),dis.min()) >= -tol and max(ch.max(),dis.max()) <= power+tol and np.minimum(ch,dis).max() <= tol and e.min() >= spec.energy_mwh*spec.min_fraction-tol and e.max() <= spec.energy_mwh*spec.max_fraction+tol and abs(e[-1]-target) <= tol and np.max(abs(e-expected)) <= tol
    if not valid:
        raise ValueError("Physical or terminal constraint violated")
    return True


def realized_profit(schedule, realized_eur_mwh, spec=BESS(), settlement_eur=0.0):
    check_schedule(schedule,spec)
    price = np.asarray(realized_eur_mwh,dtype=float)
    ch,dis = schedule["charge_mw"],schedule["discharge_mw"]
    if price.shape != np.asarray(ch).shape or not np.isfinite(price).all() or not np.isfinite(settlement_eur) or settlement_eur < 0:
        raise ValueError("Invalid settlement inputs")
    return float(np.sum((price*(dis-ch)-spec.degradation_eur_mwh*(ch+dis))*spec.dt_hours)-settlement_eur)
