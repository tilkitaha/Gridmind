"""Risk-averse battery scheduling for the Polish study: a scenario-based mean-CVaR MILP.

The deterministic MILP (polish_market.optimize_schedule) maximizes the profit expected from
one forecast and is risk-neutral. This model fixes one schedule for the delivery day that
maximizes

    (1 - weight) * mean_s profit_s + weight * CVaR_alpha(profit_s)

over price scenarios s, where CVaR_alpha is the mean profit of the worst alpha share of the
scenarios, linearized as in Rockafellar and Uryasev (2000):

    CVaR_alpha = max_eta  eta - 1 / (alpha S) * sum_s max(eta - profit_s, 0).

Each scenario is the day's forecast plus the forecast error of one recent day
(realized minus forecast prices), so the scenarios carry the size and the intraday shape of
the errors the forecast has actually made. The battery constraints and the wear cost are
those of polish_market.BESS.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .polish_market import BESS, check_schedule

SPEC = BESS()


def error_scenarios(forecast, past_forecasts, past_realized):
    """Scenarios = forecast + (realized - forecast) of each past day; arrays of shape (K, 96)."""
    f = np.asarray(forecast, dtype=float)
    err = np.asarray(past_realized, dtype=float) - np.asarray(past_forecasts, dtype=float)
    if err.ndim != 2 or err.shape[1] != len(f) or not len(err) or not np.isfinite(np.r_[f, err.ravel()]).all():
        raise ValueError('Expected finite past errors of shape (K, n) for a forecast of length n')
    return f + err


def optimize_cvar_schedule(scenarios, weight, alpha=0.2, spec=SPEC):
    """One schedule for all scenarios, maximizing (1 - weight) mean + weight CVaR_alpha of profit."""
    spec.validate()
    p = np.asarray(scenarios, dtype=float)
    if p.ndim != 2 or not p.size or not np.isfinite(p).all():
        raise ValueError('Expected a finite (S, n) scenario array')
    if not 0 <= weight <= 1 or not 0 < alpha <= 1:
        raise ValueError('weight must lie in [0, 1] and alpha in (0, 1]')
    S, n = p.shape
    dt, power, w = spec.dt_hours, min(spec.power_mw, spec.grid_mw), spec.degradation_eur_mwh
    target = spec.energy_mwh * spec.target_fraction
    nx = 4 * n + 1 + S                                   # charge, discharge, energy, mode, eta, shortfalls
    pbar = p.mean(0)
    c = np.zeros(nx)
    c[:n] = (1 - weight) * (pbar + w) * dt               # minimize minus the objective
    c[n:2 * n] = (1 - weight) * (-pbar + w) * dt
    c[4 * n] = -weight
    c[4 * n + 1:] = weight / (alpha * S)
    lo = np.r_[np.zeros(2 * n), np.full(n, spec.energy_mwh * spec.min_fraction), np.zeros(n), -np.inf, np.zeros(S)]
    hi = np.r_[np.full(2 * n, power), np.full(n, spec.energy_mwh * spec.max_fraction), np.ones(n), np.inf, np.full(S, np.inf)]
    lo[3 * n - 1] = hi[3 * n - 1] = target
    A = lil_matrix((3 * n + S, nx))
    lower = np.full(3 * n + S, -np.inf)
    upper = np.zeros(3 * n + S)
    for t in range(n):
        A[t, 2 * n + t] = 1
        A[t, t] = -spec.eta_ch * dt
        A[t, n + t] = dt / spec.eta_dis
        if t:
            A[t, 2 * n + t - 1] = -1
        lower[t] = upper[t] = target if t == 0 else 0
        A[n + t, t] = 1
        A[n + t, 3 * n + t] = -power
        A[2 * n + t, n + t] = 1
        A[2 * n + t, 3 * n + t] = power
        upper[2 * n + t] = power
    for s in range(S):                                   # eta - profit_s - shortfall_s <= 0
        r = 3 * n + s
        A[r, :n] = (p[s] + w) * dt
        A[r, n:2 * n] = (-p[s] + w) * dt
        A[r, 4 * n] = 1
        A[r, 4 * n + 1 + s] = -1
    integrality = np.r_[np.zeros(3 * n), np.ones(n), np.zeros(1 + S)]
    result = milp(c, integrality=integrality, bounds=Bounds(lo, hi), constraints=LinearConstraint(A.tocsr(), lower, upper),
                  options={'mip_rel_gap': 1e-9, 'time_limit': 120})
    if not result.success:
        raise RuntimeError('Risk-averse schedule optimization did not establish optimality')
    charge, discharge, energy = np.split(result.x[:3 * n], 3)
    schedule = {'charge_mw': charge, 'discharge_mw': discharge, 'energy_mwh': energy}
    check_schedule(schedule, spec)
    return schedule


def scenario_profits(schedule, scenarios, spec=SPEC):
    """Profit of one schedule under each scenario (EUR), wear included."""
    ch, dis = np.asarray(schedule['charge_mw']), np.asarray(schedule['discharge_mw'])
    p = np.asarray(scenarios, dtype=float)
    return ((p * (dis - ch) - spec.degradation_eur_mwh * (ch + dis)) * spec.dt_hours).sum(1)


def cvar(values, alpha):
    """Mean of the worst ceil(alpha n) values."""
    x = np.sort(np.asarray(values, dtype=float))
    return float(x[:int(np.ceil(alpha * len(x)))].mean())
