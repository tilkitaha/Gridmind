"""Single-bus P2P allocation with explicit outside options and monetary accounting.

Inputs are interval energy (kWh) and tariffs (EUR/kWh). No future values,
batteries, network power flow, wholesale orders or learned agents are assumed.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog, minimize


@dataclass
class Clearing:
    trades: list
    benefit_eur: np.ndarray
    grid_import_kwh: np.ndarray
    grid_export_kwh: np.ndarray
    community_benefit_eur: float
    welfare_bound_eur: float
    fee_eur: float
    solver_status: str


def clear(
    net_kwh,
    buy,
    sell,
    policy="proportional",
    fee=0.0,
    cumulative=None,
    scale=None,
    welfare_tolerance=0.05,
    epsilon=0.01,
):
    """Positive net_kwh is deficit. Fees are external cost, split equally per edge.

    nash_guarded maximizes a regularized log utility of cumulative normalized
    savings, retaining at least (1-welfare_tolerance) of the interval LP optimum.
    The normalizing scale is fixed using training data. SLSQP failure uses an
    explicitly reported feasible LP fallback; it is never presented as Nash success.
    """
    net = np.asarray(net_kwh, dtype=float)
    b, s = np.asarray(buy, dtype=float), np.asarray(sell, dtype=float)
    if net.ndim != 1 or len(net) < 1 or b.shape != net.shape or s.shape != net.shape:
        raise ValueError("Expected equally sized one-dimensional vectors")
    if not all(np.isfinite(v).all() for v in (net, b, s)):
        raise ValueError("Non-finite energy or tariff")
    if not np.isfinite(fee) or fee < 0 or not 0 <= welfare_tolerance <= 1:
        raise ValueError("Invalid fee or welfare tolerance")
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if policy not in {"grid_only", "proportional", "welfare_lp", "nash_guarded"}:
        raise ValueError("Unknown policy")
    n = len(net)
    cumulative = np.zeros(n) if cumulative is None else np.asarray(cumulative, float)
    scale = np.ones(n) if scale is None else np.asarray(scale, float)
    if cumulative.shape != net.shape or scale.shape != net.shape:
        raise ValueError("Invalid cumulative savings or scale shape")
    if (
        not np.isfinite(cumulative).all()
        or (cumulative < -1e-8).any()
        or not np.isfinite(scale).all()
        or (scale <= 0).any()
    ):
        raise ValueError("Cumulative benefits must be nonnegative; scale strictly positive")
    deficit, surplus = np.maximum(net, 0), np.maximum(-net, 0)
    buyers, sellers = np.flatnonzero(deficit > 1e-10), np.flatnonzero(surplus > 1e-10)
    edges = [(i, j) for i in sellers for j in buyers if b[j] - s[i] - fee > 1e-10]
    if not edges or policy == "grid_only":
        return Clearing([], np.zeros(n), deficit, surplus, 0.0, 0.0, 0.0, "no_trade")
    m = len(edges)
    A = np.zeros((n, m))
    gain = np.zeros((n, m))
    spread = np.zeros(m)
    for k, (i, j) in enumerate(edges):
        A[i, k] = A[j, k] = 1
        spread[k] = b[j] - s[i] - fee
        gain[i, k] = gain[j, k] = spread[k] / 2
    capacity = np.abs(net)
    lp = linprog(-spread, A_ub=A, b_ub=capacity, bounds=(0, None), method="highs")
    if not lp.success:
        raise RuntimeError("Welfare LP failed: " + lp.message)
    bound = float(spread @ lp.x)
    if policy == "proportional":
        volume = min(surplus.sum(), deficit.sum())
        x = np.array(
            [volume * surplus[i] / surplus.sum() * deficit[j] / deficit.sum() for i, j in edges]
        )
        status = "proportional"
    elif policy == "welfare_lp":
        x, status = lp.x, "optimal_lp"
    else:
        normal_gain = gain / scale[:, None]
        initial = np.maximum(cumulative, 0) / scale
        floor = (1 - welfare_tolerance) * bound

        def objective(x):
            return -np.log(epsilon + initial + normal_gain @ x).mean()

        def gradient(x):
            return -(normal_gain / (epsilon + initial + normal_gain @ x)[:, None]).mean(axis=0)

        opt = minimize(
            objective,
            lp.x,
            jac=gradient,
            method="SLSQP",
            bounds=[(0, None)] * m,
            constraints=[
                {"type": "ineq", "fun": lambda x: capacity - A @ x, "jac": lambda x: -A},
                {"type": "ineq", "fun": lambda x: spread @ x - floor, "jac": lambda x: spread},
            ],
            options={"ftol": 1e-10, "maxiter": 150},
        )
        candidate = np.maximum(opt.x, 0)
        feasible = (
            (A @ candidate <= capacity + 1e-7).all()
            and spread @ candidate >= floor - 1e-7
            and np.isfinite(candidate).all()
        )
        if opt.success and feasible:
            x, status = candidate, "converged_nash"
        else:
            x, status = lp.x, "fallback_lp_after_nash_failure"
    if (x < -1e-8).any() or (A @ x > capacity + 1e-7).any():
        raise RuntimeError("Allocation violates a physical energy capacity")
    gi, ge = deficit.copy(), surplus.copy()
    trades = []
    for k, (i, j) in enumerate(edges):
        q = float(x[k])
        ge[i] -= q
        gi[j] -= q
        if q > 1e-10:
            trades.append(
                {
                    "seller": int(i),
                    "buyer": int(j),
                    "kwh": q,
                    "price_eur_kwh": float((b[j] + s[i]) / 2),
                    "fee_eur": q * fee,
                }
            )
    benefits = gain @ x
    fees = float(x.sum() * fee)
    outside_cost = float(b @ deficit - s @ surplus)
    community_cost = float(b @ gi - s @ ge + fees)
    if not np.isclose(outside_cost - community_cost, benefits.sum(), atol=1e-7):
        raise RuntimeError("Payments failed to cancel in community accounting")
    if not np.isclose(gi.sum() - ge.sum(), net.sum(), atol=1e-7):
        raise RuntimeError("Energy balance failed")
    return Clearing(trades, benefits, gi, ge, float(benefits.sum()), bound, fees, status)
