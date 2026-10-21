"""Safety and selection tests for isolated self-improvement research workflow."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/simulations31_self_improvement.py"
SPEC = importlib.util.spec_from_file_location("sim31self", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_chronological_split_excludes_june():
    dates = pd.date_range("2026-01-01", "2026-05-31", freq="D")
    train, val = M.split_dates(dates)
    assert train.sum() == 120 and val.sum() == 31
    with pytest.raises(ValueError, match="June or test"):
        M.split_dates(pd.date_range("2026-01-01", "2026-06-01", freq="D"))


def test_gate_accepts_dominant_candidate_but_never_auto_promotes():
    x = np.array([1., 2., 3., 4., 5.])
    d = M.gate(x + 1, x)
    assert d["recommendation"] == "eligible_for_human_review"
    assert d["automatic_promotion"] is False


def test_gate_rejects_mean_gain_with_tail_loss():
    baseline = np.full(10, 10.)
    candidate = np.array([-100.] + [30.] * 9)
    d = M.gate(candidate, baseline)
    assert d["candidate"]["mean_profit"] > d["baseline"]["mean_profit"]
    assert d["recommendation"] == "reject"


def test_gate_rejects_misaligned_and_nonfinite_data():
    with pytest.raises(ValueError, match="paired"):
        M.gate([1, 2], [1])
    with pytest.raises(ValueError, match="finite"):
        M.gate([float("nan")], [1])


def test_date_validation_refuses_duplicates_and_invalid_periods():
    with pytest.raises(ValueError, match="unique"):
        M.split_dates(["2026-05-01", "2026-05-01"])
    with pytest.raises(ValueError, match="development"):
        M.split_dates(["2025-12-31", "2026-05-01"])


def test_loss_count_penalty_is_enforced():
    baseline = np.array([2., 2., 2., 2., 2.])
    candidate = np.array([-1., 4., 4., 4., 4.])
    decision = M.gate(candidate, baseline)
    assert decision["recommendation"] == "reject"
