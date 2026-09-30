"""Metrics with explicit domains; a zero vector is not reported as perfect fairness."""

import numpy as np


def benefit_metrics(values):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all():
        raise ValueError("Finite nonempty vector required")
    result = {
        "total": float(x.sum()),
        "minimum": float(x.min()),
        "negative_fraction": float((x < -1e-8).mean()),
        "jain": None,
        "gini": None,
        "nash_geometric": None,
    }
    if (x < -1e-8).any():
        result["domain"] = "negative_benefits_fairness_undefined"
        return result
    x = np.maximum(x, 0)  # numeric noise only; material losses rejected above
    result["nash_geometric"] = 0.0 if (x == 0).any() else float(np.exp(np.log(x).mean()))
    if x.sum() <= 1e-12:
        result["domain"] = "zero_benefits_fairness_undefined"
        return result
    result.update(
        jain=float(x.sum() ** 2 / (len(x) * (x * x).sum())),
        gini=float(np.abs(x[:, None] - x).sum() / (2 * len(x) * x.sum())),
        domain="nonnegative_benefits",
    )
    return result


def cvar(losses, alpha=0.95):
    """Exact empirical upper-tail CVaR, including fractional mass at the quantile."""
    x = np.asarray(losses, dtype=float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or not 0 <= alpha < 1:
        raise ValueError("Finite losses and alpha in [0,1) required")
    tail = len(x) * (1 - alpha)
    whole = int(np.floor(tail))
    fraction = tail - whole
    ordered = np.sort(x)[::-1]
    return float(
        (ordered[:whole].sum() + (fraction * ordered[whole] if whole < len(x) else 0)) / tail
    )


def paired_block_ci(a, b, block=7, repeats=2000, seed=731):
    """Circular moving-block bootstrap CI for paired daily mean differences."""
    difference = np.asarray(a, float) - np.asarray(b, float)
    if difference.ndim != 1 or len(difference) < block or not np.isfinite(difference).all():
        raise ValueError("Need aligned finite daily values and at least one block")
    if block < 1 or repeats < 100:
        raise ValueError("Invalid bootstrap configuration")
    rng = np.random.default_rng(seed)
    n = len(difference)
    starts = rng.integers(0, n, size=(repeats, int(np.ceil(n / block))))
    idx = (starts[..., None] + np.arange(block)) % n
    estimates = difference[idx.reshape(repeats, -1)[:, :n]].mean(axis=1)
    return {
        "mean_difference": float(difference.mean()),
        "ci95_low": float(np.quantile(estimates, 0.025)),
        "ci95_high": float(np.quantile(estimates, 0.975)),
        "block_days": block,
        "n_days": n,
        "interpretation": "exploratory_interval_not_confirmatory",
    }
