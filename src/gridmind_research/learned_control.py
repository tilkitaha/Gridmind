"""Shared-actor IPPO/MAPPO; matched local observations, team reward and budgets."""

import copy
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.distributions import Categorical

from .battery import ACTIONS, BatteryBatch, load_episodes, mpc_action

torch.set_num_threads(1)


class Policy(nn.Module):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.actor = nn.Sequential(
            nn.Linear(12, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 5)
        )
        self.critic = nn.Sequential(
            nn.Linear(72 if kind == "MAPPO" else 12, 32),
            nn.Tanh(),
            nn.Linear(32, 32),
            nn.Tanh(),
            nn.Linear(32, 1),
        )

    def distribution(self, x):
        return Categorical(logits=self.actor(x))

    def value(self, x):
        return (
            self.critic(x.flatten(-2)).expand(*x.shape[:-1])
            if self.kind == "MAPPO"
            else self.critic(x).squeeze(-1)
        )


def rollout(model, eps):
    env = BatteryBatch(eps)
    cost = np.zeros((len(eps), 6))
    gain = cost.copy()
    throughput = cost.copy()
    res = 0
    records = []
    for t in range(16):
        if isinstance(model, Policy):
            with torch.no_grad():
                request = ACTIONS[model.actor(torch.as_tensor(env.obs())).argmax(-1).numpy()]
        elif model == "idle":
            request = np.zeros_like(env.soc)
        elif model == "self_consumption":
            request = np.clip(-env.prev, -0.5, 0.5)
        elif model == "MPC":
            request = mpc_action(env)
        else:
            raise ValueError(model)
        _, _, _, d = env.step(request)
        cost += d["cost"]
        gain += d["benefit"]
        throughput += np.abs(d["ac"])
        res = max(res, float(np.abs(d["residual"]).max()))
        records.append(d)
    return {
        "cost": cost,
        "gain": gain,
        "throughput": throughput,
        "energy_residual": res,
        "terminal_residual": float(np.abs(env.soc - 1).max()),
    }, records


def train(kind, seed, train_eps, val_eps, out):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    m = Policy(kind)
    initial = copy.deepcopy(m.state_dict())
    opt = torch.optim.Adam(m.parameters(), lr=0.0003)
    best = -np.inf
    logs = []
    started = time.perf_counter()
    for update in range(1, 61):
        env = BatteryBatch([train_eps[i] for i in rng.integers(0, len(train_eps), 12)])
        xs = []
        acts = []
        lps = []
        vs = []
        rs = []
        for t in range(16):
            x = torch.as_tensor(env.obs())
            with torch.no_grad():
                dist = m.distribution(x)
                a = dist.sample()
                v = m.value(x)
                lp = dist.log_prob(a)
            _, r, _, _ = env.step(ACTIONS[a.numpy()])
            xs.append(x)
            acts.append(a)
            lps.append(lp)
            vs.append(v)
            rs.append(torch.as_tensor(r, dtype=torch.float32))
        val = torch.stack(vs)
        rew = torch.stack(rs)
        adv = torch.zeros_like(rew)
        gae = torch.zeros_like(rew[0])
        nextv = torch.zeros_like(val[0])
        for t in reversed(range(16)):
            delta = rew[t] + nextv - val[t]
            gae = delta + 0.95 * gae
            adv[t] = gae
            nextv = val[t]
        ret = adv + val
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        x = torch.stack(xs).flatten(0, 1)
        a = torch.stack(acts).flatten(0, 1)
        oldlp = torch.stack(lps).flatten(0, 1)
        ad = adv.flatten(0, 1)
        target = ret.flatten(0, 1)
        for epoch in range(4):
            dist = m.distribution(x)
            ratio = (dist.log_prob(a) - oldlp).exp()
            actor = -torch.minimum(ratio * ad, ratio.clamp(0.8, 1.2) * ad).mean()
            vl = (m.value(x) - target).square().mean()
            loss = actor + 0.5 * vl - 0.01 * dist.entropy().mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(), 0.5)
            opt.step()
        if update % 10 == 0:
            score = float(rollout(m, val_eps)[0]["gain"].sum(1).mean())
            logs.append(
                {
                    "update": update,
                    "validation_savings": score,
                    "actor_loss": float(actor.detach()),
                    "value_loss": float(vl.detach()),
                }
            )
            if score > best:
                best = score
                state = copy.deepcopy(m.state_dict())
                bestupdate = update
    m.load_state_dict(state)
    p = out / f"{kind}_seed{seed}.pt"
    torch.save({"kind": kind, "state_dict": state, "seed": seed, "selected_update": bestupdate}, p)
    return m, {
        "kind": kind,
        "seed": seed,
        "selected_update": bestupdate,
        "validation_best": best,
        "parameter_squared_change": sum(
            float((state[k] - initial[k]).square().sum()) for k in initial
        ),
        "seconds": time.perf_counter() - started,
        "checkpoint_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "validation_checkpoints": logs,
    }


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--evaluate-only", action="store_true")
    a = p.parse_args()
    out = Path("results/extension")
    models = out / "models"
    models.mkdir(parents=True, exist_ok=True)
    eps = {s: load_episodes(s) for s in ["train", "validation", "test"]}
    print("Episodes", {k: len(v) for k, v in eps.items()}, flush=True)
    logs = []
    rows = []
    checks = []

    def record(kind, seed, batch, result):
        checks.append((result["energy_residual"], result["terminal_residual"]))
        for k, ep in enumerate(batch):
            for h in range(6):
                rows.append(
                    {
                        "method": kind,
                        "seed": seed,
                        "start": ep["start"],
                        "household": h,
                        "cost_eur": result["cost"][k, h],
                        "savings_vs_idle_eur": result["gain"][k, h],
                        "throughput_kwh": result["throughput"][k, h],
                    }
                )

    for kind in ["IPPO", "MAPPO"]:
        for seed in [11, 22, 33, 44, 55]:
            if a.evaluate_only:
                state = torch.load(models / f"{kind}_seed{seed}.pt", weights_only=True)
                m = Policy(kind)
                m.load_state_dict(state["state_dict"])
            else:
                m, log = train(kind, seed, eps["train"], eps["validation"], models)
                logs.append(log)
            result, _ = rollout(m, eps["test"])
            record(kind, seed, eps["test"], result)
            print(kind, seed, "complete", flush=True)
    for kind in ["idle", "self_consumption", "MPC"]:
        for batch in [[e] for e in eps["test"]] if kind == "MPC" else [eps["test"]]:
            result, _ = rollout(kind, batch)
            record(kind, -1, batch, result)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "household_episode_results.csv", index=False)
    totals = (
        frame.groupby(["method", "seed"])[["cost_eur", "savings_vs_idle_eur", "throughput_kwh"]]
        .sum()
        .reset_index()
    )
    totals.to_csv(out / "seed_totals.csv", index=False)
    result = {
        "episodes": {s: len(v) for s, v in eps.items()},
        "torch_version": torch.__version__,
        "max_energy_residual": max(x[0] for x in checks),
        "max_terminal_residual": max(x[1] for x in checks),
        "seed_totals": totals.to_dict("records"),
        "training": logs,
        "data_sha256": hashlib.sha256(
            Path("data/storenet_h1_h6_15min.csv").read_bytes()
        ).hexdigest(),
    }
    filename = "evaluation_results.json" if a.evaluate_only else "control_results.json"
    (out / filename).write_text(json.dumps(result, indent=2))
    print(totals.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
