"""Causal four-hour community battery simulation, kWh and EUR units."""

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

N = 6
ETA = 0.95
MIN = 0.2
MAX = 1.8
TARGET = 1.0
LIMIT = 0.5
DEGR = 0.01
FEE = 0.02
ACTIONS = np.array([-0.5, -0.25, 0, 0.25, 0.5])


def tariff(h):
    h = np.asarray(h)
    return np.where((h >= 16) & (h < 20), 0.42, np.where(h < 7, 0.20, 0.30))


def project(soc, request, remaining):
    low = np.maximum(MIN, TARGET - (remaining - 1) * LIMIT * ETA)
    high = np.minimum(MAX, TARGET + (remaining - 1) * LIMIT / ETA)
    delta = np.where(request >= 0, request * ETA, request / ETA)
    delta = np.clip(delta, np.maximum(-LIMIT / ETA, low - soc), np.minimum(LIMIT * ETA, high - soc))
    return soc + delta, np.where(delta >= 0, delta / ETA, delta * ETA)


def settlement(net, buy):
    deficit = np.maximum(net, 0)
    surplus = np.maximum(-net, 0)
    ds = deficit.sum(-1, keepdims=True)
    ss = surplus.sum(-1, keepdims=True)
    v = np.minimum(ds, ss)
    pin = v * np.divide(deficit, ds, out=np.zeros_like(deficit), where=ds > 0)
    pout = v * np.divide(surplus, ss, out=np.zeros_like(surplus), where=ss > 0)
    b = np.asarray(buy)[..., None]
    benefit = 0.5 * (b - 0.08 - FEE) * (pin + pout)
    cost = b * deficit - 0.08 * surplus - benefit
    res = (deficit - pin - surplus + pout).sum(-1) - net.sum(-1)
    assert np.max(np.abs(res)) < 1e-8
    return cost, pin, pout, res


def load_episodes(split):
    d = pd.read_csv("data/storenet_h1_h6_15min.csv", index_col=0, parse_dates=True)
    dates = {
        "train": ("2020-01-01", "2020-04-30"),
        "validation": ("2020-05-01", "2020-05-31"),
        "test": ("2020-06-01", "2020-06-14"),
    }
    start, end = dates[split]
    x = d.loc[start:end]
    out = []
    for _, g in x.groupby([x.index.normalize(), x.index.hour // 4]):
        if len(g) != 16 or not g.notna().all().all():
            continue
        prev = d.reindex([g.index[0] - pd.Timedelta(minutes=15)])
        if prev.isna().any().any():
            continue
        out.append(
            {
                "start": str(g.index[0]),
                "net": g.iloc[:, ::2].to_numpy() - g.iloc[:, 1::2].to_numpy(),
                "lag": prev.iloc[:, ::2].to_numpy()[0] - prev.iloc[:, 1::2].to_numpy()[0],
                "hours": g.index.hour.to_numpy() + g.index.minute.to_numpy() / 60,
            }
        )
    return out


class BatteryBatch:
    def __init__(self, episodes):
        self.episodes = episodes
        self.net = np.stack([e["net"] for e in episodes])
        self.hours = np.stack([e["hours"] for e in episodes])
        self.prev = np.stack([e["lag"] for e in episodes])
        self.soc = np.ones((len(episodes), N))
        self.t = 0

    def obs(self):
        b = len(self.episodes)
        h = self.hours[:, min(self.t, 15)]
        time = np.stack(
            [
                np.sin(h * np.pi / 12),
                np.cos(h * np.pi / 12),
                np.full(b, (16 - self.t) / 16),
                tariff(h),
            ],
            axis=-1,
        )
        return np.concatenate(
            [
                self.soc[..., None] / 2,
                self.prev[..., None] / 2,
                np.broadcast_to(time[:, None, :], (b, N, 4)),
                np.broadcast_to(np.eye(N)[None, :, :], (b, N, N)),
            ],
            axis=-1,
        ).astype("float32")

    def step(self, request):
        self.soc, ac = project(self.soc, np.asarray(request), 16 - self.t)
        net = self.net[:, self.t, :]
        buy = tariff(self.hours[:, self.t])
        cost, pin, pout, res = settlement(net + ac, buy)
        base, *_ = settlement(net, buy)
        cost += DEGR * np.abs(ac)
        gain = base - cost
        d = {
            "cost": cost,
            "benefit": gain,
            "ac": ac,
            "soc": self.soc.copy(),
            "pin": pin,
            "pout": pout,
            "residual": res,
            "buy": buy,
        }
        self.prev = net.copy()
        self.t += 1
        if self.t == 16:
            assert np.max(np.abs(self.soc - 1)) < 1e-8
        return self.obs(), np.repeat(gain.sum(1, keepdims=True) / N, N, axis=1), self.t == 16, d


def mpc_action(env, net_forecast=None):
    assert len(env.episodes) == 1
    H = 16 - env.t
    # Optional causal H x N forecast. The original persistence default is retained.
    forecast = np.broadcast_to(env.prev[0], (H, N)) if net_forecast is None else np.asarray(net_forecast, dtype=float)
    if forecast.shape != (H, N) or not np.isfinite(forecast).all():
        raise ValueError("Expected a finite remaining-horizon by household forecast")
    n = N * H
    nv = 7 * n

    def ix(v, t, i):
        return v * n + t * N + i

    A = lil_matrix((2 * n + H, nv))
    rhs = np.zeros(2 * n + H)
    obj = np.zeros(nv)
    bounds = []
    for v in range(7):
        for t in range(H):
            for i in range(N):
                bounds.append(
                    (0, LIMIT)
                    if v < 2
                    else ((TARGET, TARGET) if t == H - 1 else (MIN, MAX))
                    if v == 6
                    else (0, None)
                )
    for t in range(H):
        b = float(tariff(env.hours[0, env.t + t]))
        for i in range(N):
            r = t * N + i
            for v, coef in [(2, 1), (3, -1), (4, 1), (5, -1), (0, -1), (1, 1)]:
                A[r, ix(v, t, i)] = coef
            rhs[r] = forecast[t, i]
            A[n + r, ix(6, t, i)] = 1
            A[n + r, ix(0, t, i)] = -ETA
            A[n + r, ix(1, t, i)] = 1 / ETA
            if t:
                A[n + r, ix(6, t - 1, i)] = -1
            else:
                rhs[n + r] = env.soc[0, i]
            A[2 * n + t, ix(4, t, i)] = 1
            A[2 * n + t, ix(5, t, i)] = -1
            for v, c in [(0, DEGR), (1, DEGR), (2, b), (3, -0.08), (4, FEE / 2), (5, FEE / 2)]:
                obj[ix(v, t, i)] = c
    sol = linprog(obj, A_eq=A.tocsr(), b_eq=rhs, bounds=bounds, method="highs")
    if not sol.success:
        raise RuntimeError(sol.message)
    ch = sol.x[:n].reshape(H, N)
    di = sol.x[n : 2 * n].reshape(H, N)
    if np.minimum(ch, di).max() > 1e-7:
        raise RuntimeError("Simultaneous cycling")
    return (ch[0] - di[0])[None, :]
