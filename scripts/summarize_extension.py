import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gridmind_research.metrics import benefit_metrics, cvar

r = Path("results/extension")
d = pd.read_csv(r / "household_episode_results.csv")
tot = pd.read_csv(r / "seed_totals.csv")
summary = []
for method, g in tot.groupby("method"):
    summary.append(
        {
            "method": method,
            "cost_mean": float(g.cost_eur.mean()),
            "cost_sd": float(g.cost_eur.std()) if len(g) > 1 else 0.0,
            "savings_mean": float(g.savings_vs_idle_eur.mean()),
        }
    )
diag = []
for (m, s), g in d.groupby(["method", "seed"]):
    h = g.groupby("household").savings_vs_idle_eur.sum().to_numpy()
    diag.append(
        {
            "method": m,
            "seed": int(s),
            "benefit_metrics": benefit_metrics(h),
            "episode_cost_cvar95": float(cvar(g.groupby("start").cost_eur.sum().to_numpy())),
        }
    )
(r / "summary.json").write_text(json.dumps({"methods": summary, "diagnostics": diag}, indent=2))
fig, ax = plt.subplots(figsize=(8, 4))
order = ["idle", "self_consumption", "MPC", "IPPO", "MAPPO"]
for i, m in enumerate(order):
    v = tot[tot.method == m].cost_eur.to_numpy()
    ax.scatter(i + np.linspace(-0.07, 0.07, len(v)), v, s=40)
    ax.plot([i - 0.17, i + 0.17], [v.mean(), v.mean()], color="black", lw=2)
ax.set_xticks(range(5), ["Idle", "Self-consumption", "MPC", "IPPO", "MAPPO"])
ax.set_ylabel("Community cost over 44 test episodes (EUR)")
ax.set_title("Battery control with assumed tariffs")
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig("results/figures/control_costs.png", dpi=180)
plt.close(fig)
