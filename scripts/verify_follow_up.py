"""Audit retained follow-up evidence without training or market-data claims."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

def verify():
    original=read("results/extension/control_results.json")
    result=read("results/ablations/results.json")
    replay=read("results/ablations/replay.json")
    runs=result["runs"]
    keys=lambda r:(r["variant"],r["kind"],r["seed"])
    lookup={keys(r):r for r in replay["runs"]}
    checkpoints=ROOT/"results/ablations/models"
    check={"sixty_unique_runs":len(runs)==60 and len({keys(r) for r in runs})==60,
    "fixed_protocol_hash":result["protocol_sha256"]==sha("configs/ablation_protocol.json"),
    "same_input_hash":result["data_sha256"]==original["data_sha256"]==sha("data/storenet_h1_h6_15min.csv"),
    "all_checkpoint_hashes":all(hashlib.sha256((checkpoints/f'{r["variant"]}_{r["kind"]}_seed{r["seed"]}.pt').read_bytes()).hexdigest()==r["checkpoint_sha256"] for r in runs),
    "same_replay_inputs":replay["data_sha256"]==result["data_sha256"] and replay["protocol_sha256"]==result["protocol_sha256"]}
    replay_delta=max(abs(r["cost_eur"]-lookup[keys(r)]["cost_eur"]) for r in runs)
    check["saved_model_replay_costs"]=replay_delta<1e-9
    source={(r["method"],r["seed"]):r["cost_eur"] for r in original["seed_totals"] if r["method"] in ["IPPO","MAPPO"]}
    original_delta=max(abs(r["cost_eur"]-source[r["kind"],r["seed"]]) for r in runs if r["variant"]=="discrete_60")
    check["original_reference_reproduced"]=original_delta<1e-9
    rows=pd.read_csv(ROOT/"results/ablations/household_results.csv")
    groups=rows.groupby(["variant","kind","seed"])
    check["household_rows"]=len(rows)==15840 and len(groups)==60 and groups.size().eq(264).all()
    cost=groups.cost_eur.sum()
    check["household_aggregation"]=all(abs(cost.loc[keys(r)]-r["cost_eur"])<1e-8 for r in runs)
    check["physical_residuals"]=all(r["energy_residual"]<1e-8 and r["terminal_residual"]<1e-8 for r in runs)
    fc=read("results/forecast_control/results.json")
    check["forecast_control_protocol"]=fc["protocol_sha256"]==sha("configs/forecast_control_protocol.json") and fc["data_sha256"]==result["data_sha256"]
    fr=pd.read_csv(ROOT/"results/forecast_control/household_results.csv")
    check["forecast_control_rows"]=len(fr)==1056 and fr.groupby("method").size().eq(264).all()
    origmpc=next(r["cost_eur"] for r in original["seed_totals"] if r["method"]=="MPC")
    persistence=next(r for r in fc["summaries"] if r["method"]=="persistence")
    check["mpc_default_unchanged"]=abs(persistence["cost_eur"]-origmpc)<1e-8
    check["forecast_control_aggregation"]=all(abs(fr[fr.method==r["method"]].cost_eur.sum()-r["cost_eur"])<1e-8 for r in fc["summaries"])
    report={"checks":{k:bool(v) for k,v in check.items()},"all_passed":bool(all(check.values())),"max_replay_cost_difference_eur":replay_delta,"max_original_cost_difference_eur":original_delta,"scope":"Existing exploratory data, saved checkpoint hashes and actual replay records. No independent test or Polish-market performance."}
    print(json.dumps(report,indent=2))
    return report["all_passed"]

if __name__=="__main__":raise SystemExit(0 if verify() else 1)
