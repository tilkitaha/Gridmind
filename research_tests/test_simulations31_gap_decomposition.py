"""Exact independent accounting tests for SIMULATIONS31 gap decomposition."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/simulations31_gap_decomposition.py"
SPEC = importlib.util.spec_from_file_location("sim31gap", SCRIPT)
GAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAP)


def frame():
    x = pd.DataFrame({
        "local_time": [f"2026-06-30T{i//4:02d}:{15*(i%4):02d}+02:00" for i in range(96)],
        "forecast_eur_per_mwh": np.linspace(20.0, 150.0, 96),
        "milp_power_mw_positive_charge": np.zeros(96),
        "milp_soc_mwh": np.ones(96),
    })
    for model in GAP.EXPECTED_MODELS:
        x[model + "_power_mw"] = np.zeros(96)
        x[model + "_requested_mw"] = np.zeros(96)
        x[model + "_soc_mwh"] = np.ones(96)
    return x


def test_identical_actions_have_exact_zero_gap():
    details, report = GAP.compare(frame())
    assert len(details) == 96
    assert report["forecast_milp_minus_ppo_eur"] == pytest.approx(0)
    assert report["clipped_model_intervals"] == 0


def test_price_and_wear_components_are_an_exact_identity():
    x = frame()
    x.loc[0, "forecast_eur_per_mwh"] = 50
    x.loc[0, "milp_power_mw_positive_charge"] = -0.5
    for name in GAP.EXPECTED_MODELS:
        x.loc[0, name + "_power_mw"] = -0.2
        x.loc[0, name + "_requested_mw"] = -0.5
    detailed, s = GAP.compare(x)
    # For the first quarter hour, MILP selling 0.5 MW vs PPO selling 0.2 MW.
    # Price-cashflow advantage = 50*(0.5-0.2)*0.25 = 3.75 EUR;
    # extra MILP wear = 10*(0.5-0.2)*0.25 = 0.75 EUR.
    assert detailed.loc[0, "price_cashflow_component_eur"] == pytest.approx(3.75)
    assert detailed.loc[0, "wear_component_eur"] == pytest.approx(-0.75)
    assert detailed.loc[0, "milp_minus_ppo_mean_eur"] == pytest.approx(3.0)
    assert s["forecast_milp_minus_ppo_eur"] == pytest.approx(3.0)
    assert s["clipped_model_intervals"] == 5


def test_negative_forecast_prices_preserve_decomposition():
    x = frame()
    x["forecast_eur_per_mwh"] = -100
    for name in GAP.EXPECTED_MODELS:
        x.loc[0, name + "_power_mw"] = 0.5
    details, result = GAP.compare(x)
    assert np.isclose(details["milp_minus_ppo_mean_eur"].sum(),
                      result["forecast_milp_minus_ppo_eur"])


def test_rejects_missing_corrupt_and_overlimit_data():
    x = frame()
    with pytest.raises(ValueError, match="Missing required"):
        GAP.compare(x.drop(columns=["milp_soc_mwh"]))
    with pytest.raises(ValueError, match="Exactly 96"):
        GAP.compare(x.iloc[:95])
    x.loc[1, "forecast_eur_per_mwh"] = np.nan
    with pytest.raises(ValueError, match="Non-finite"):
        GAP.compare(x)
    x = frame()
    x.loc[1, "milp_power_mw_positive_charge"] = 1.5
    with pytest.raises(ValueError, match="Power limit"):
        GAP.compare(x)
