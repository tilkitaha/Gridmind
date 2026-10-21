"""Isolated safety and end-to-end tests for the additive SIMULATIONS31 audit."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pytest
import torch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/simulations31_ppo_audit.py"
SPEC = importlib.util.spec_from_file_location("simulations31_ppo_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
forecast_for_day = AUDIT.forecast_for_day
validate_paths = AUDIT.validate_paths

MOCK_MARKET = """import numpy as np
import pandas as pd

def delivery_index(day):
    return pd.date_range(day, periods=96, freq='15min', tz='Europe/Warsaw').tz_convert('UTC')

def optimize_schedule(forecast):
    return {'charge_mw':np.zeros(96), 'discharge_mw':np.zeros(96), 'energy_mwh':np.ones(96)}

def check_schedule(schedule):
    assert len(schedule['charge_mw']) == 96

def realized_profit(schedule, forecast):
    power=schedule['charge_mw']-schedule['discharge_mw']
    return float(np.sum((-forecast*power-10*np.abs(power))*.25))
"""

MOCK_RL = """import numpy as np
import torch
from torch import nn
from torch.distributions import Beta
T=96; DT=.25; E0=1.; P=1.

def observe(f, energy, t):
    return np.array([[float(energy[0]), float((T-t)/T)]],dtype='float32')

def project(energy, power, steps_left):
    up=P*.95*DT; down=P*DT/.95
    low=max(.2,E0-(steps_left-1)*up)
    high=min(1.8,E0+(steps_left-1)*down)
    delta=np.where(power>=0,power*.95*DT,power*DT/.95)
    delta=np.clip(delta,max(-down,low-energy),min(up,high-energy))
    ac=np.where(delta>=0,delta/(.95*DT),delta*.95/DT)
    return energy+delta,ac

def step_profit(ac, price):
    return (-price*ac-10*np.abs(ac))*DT

class Policy(nn.Module):
    def __init__(self,hidden=2):
        super().__init__()
        self.actor=nn.Linear(2,2)
    def distribution(self,x):
        z=torch.nn.functional.softplus(self.actor(x))+1
        return Beta(z[...,0],z[...,1])
    def power(self,a):return 2*a-1

def run_days(pol,f,p,deterministic=True):
    energy=np.array([E0]); profit=np.zeros(len(f)); th=np.zeros(len(f))
    for t in range(T):
        with torch.no_grad():
            a=pol.distribution(torch.as_tensor(observe(f,energy,t))).mean
            request=pol.power(a).numpy()
        energy,ac=project(energy,request,T-t)
        profit+=step_profit(ac,p[:,t]); th+=np.abs(ac)*DT
    return profit,th
"""


def fixture(repo):
    src = repo / "src/gridmind_research"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "polish_market.py").write_text(MOCK_MARKET)
    (src / "polish_rl.py").write_text(MOCK_RL)
    (repo / "configs").mkdir()
    (repo / "results/polish_rl").mkdir(parents=True)
    (repo / "results/polish_rl_ablation/models").mkdir(parents=True)
    pd.DataFrame([np.full(96, 100.0)], index=["2026-06-30"]).to_csv(
        repo / "results/polish_rl/lear_forecasts.csv"
    )
    expected = {}
    for seed in (11, 22, 33, 44, 55):
        torch.manual_seed(seed)
        layer = torch.nn.Linear(2, 2)
        path = f"results/polish_rl_ablation/models/forecast_2000_seed{seed}.pt"
        target = repo / path
        torch.save({
            "seed": seed,
            "arm": "forecast_2000",
            "config": {"hidden": 2},
            "state_dict": {
                "actor.weight": layer.weight.detach(),
                "actor.bias": layer.bias.detach(),
            },
        }, target)
        expected[path] = hashlib.sha256(target.read_bytes()).hexdigest()
    (repo / "configs/polish_test_protocol.json").write_text(
        json.dumps({"treatment_checkpoints": expected})
    )


def files_hashes(repo):
    return {
        str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.rglob("*") if p.is_file()
    }


def invoke(repo, out, day="2026-06-30"):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--day", day, "--out", str(out)],
        capture_output=True, text=True, timeout=80, check=False,
    )


def test_read_only_real_execution_on_five_mock_checkpoints():
    with TemporaryDirectory() as root:
        repo = Path(root) / "repo"
        fixture(repo)
        before = files_hashes(repo)
        out = Path(root) / "result"
        completed = invoke(repo, out)
        assert completed.returncode == 0, completed.stderr
        assert files_hashes(repo) == before
        assert len(pd.read_csv(out / "96_interval_actions.csv")) == 96
        summary = json.loads((out / "summary.json").read_text())
        assert summary["checkpoint_count"] == 5
        assert summary["observed_price_data_used"] is False
        assert all(x["original_run_days_reconciled"] for x in summary["models"].values())
        assert all(x["checkpoint_verified"] for x in summary["models"].values())
        assert (out / "dispatch_comparison.png").is_file()
        assert (out / "battery_soc.png").is_file()
        assert invoke(repo, out).returncode != 0
        assert files_hashes(repo) == before


def test_refuses_tampered_checkpoint_without_writing_output():
    with TemporaryDirectory() as root:
        repo = Path(root) / "repo"
        fixture(repo)
        with (repo / "results/polish_rl_ablation/models/forecast_2000_seed11.pt").open("ab") as f:
            f.write(b"tampered")
        out = Path(root) / "bad"
        response = invoke(repo, out)
        assert response.returncode != 0
        assert "SHA-256 mismatch" in response.stderr
        assert not out.exists()


def test_rejects_reserved_dates_and_output_within_repo():
    with TemporaryDirectory() as root:
        repo = Path(root) / "repo"
        fixture(repo)
        with pytest.raises(ValueError, match="development dates"):
            validate_paths(repo, Path(root) / "never", date(2026, 7, 1))
        with pytest.raises(ValueError, match="outside the repository"):
            validate_paths(repo, repo / "output", date(2026, 6, 30))
        output = Path(root) / "blocked"
        assert invoke(repo, output, "2026-07-01").returncode != 0
        assert not output.exists()


def test_rejects_missing_forecast_interval():
    with TemporaryDirectory() as root:
        repo = Path(root) / "repo"
        fixture(repo)
        pd.DataFrame([np.arange(95)], index=["2026-06-30"]).to_csv(
            repo / "results/polish_rl/lear_forecasts.csv"
        )
        with pytest.raises(ValueError, match="96 finite"):
            forecast_for_day(repo, date(2026, 6, 30))
        output = Path(root) / "bad"
        assert invoke(repo, output).returncode != 0
        assert not output.exists()


def test_refuses_protocol_with_different_model_panel():
    with TemporaryDirectory() as root:
        repo = Path(root) / "repo"
        fixture(repo)
        spec_file = repo / "configs/polish_test_protocol.json"
        spec = json.loads(spec_file.read_text())
        spec["treatment_checkpoints"].pop(next(iter(spec["treatment_checkpoints"])))
        spec_file.write_text(json.dumps(spec))
        output = Path(root) / "bad"
        response = invoke(repo, output)
        assert response.returncode != 0
        assert "expected five PPO checkpoints" in response.stderr
        assert not output.exists()
