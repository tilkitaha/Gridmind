"""PPO for the Polish battery trader: one delivery day per episode, forecast-only observations.

The schedule for day D is fixed at the D-1 gate, so the policy observes the forecast
prices, never the realized ones; the reward is the realized profit of each step, used
only to train. Physics and costs follow polish_market.BESS. Lessons from the Irish study
are fixed in advance: a whole day per episode and GAE lambda 1.0. Units: MW, MWh, EUR.
"""
import copy

import numpy as np
import torch
from torch import nn
from torch.distributions import Beta

from .polish_market import BESS

SPEC = BESS()
T = 96
DT = SPEC.dt_hours
E_MIN, E_MAX = SPEC.energy_mwh * SPEC.min_fraction, SPEC.energy_mwh * SPEC.max_fraction
E0 = SPEC.energy_mwh * SPEC.target_fraction
P = min(SPEC.power_mw, SPEC.grid_mw)
PPO = {'updates': 300, 'days_per_update': 16, 'epochs': 4, 'lr': 3e-4, 'clip': 0.2, 'entropy': 0.01,
       'gamma': 1.0, 'gae_lambda': 1.0, 'grad_clip': 0.5, 'hidden': 64, 'reward_scale': 0.01}


def project(energy, power, steps_left):
    """Clip requested AC power (+ charge, - discharge) to power, energy bounds and end-of-day reachability."""
    up = P * SPEC.eta_ch * DT          # most energy one step can add
    down = P * DT / SPEC.eta_dis       # most energy one step can remove
    low = np.maximum(E_MIN, E0 - (steps_left - 1) * up)
    high = np.minimum(E_MAX, E0 + (steps_left - 1) * down)
    delta = np.where(power >= 0, power * SPEC.eta_ch * DT, power * DT / SPEC.eta_dis)
    delta = np.clip(delta, np.maximum(-down, low - energy), np.minimum(up, high - energy))
    ac = np.where(delta >= 0, delta / (SPEC.eta_ch * DT), delta * SPEC.eta_dis / DT)
    return energy + delta, ac


def step_profit(ac, price):
    """Realized EUR of one step: sell on discharge, buy on charge, wear on both."""
    return (-price * ac - SPEC.degradation_eur_mwh * np.abs(ac)) * DT


def observe(forecast, energy, t):
    """Battery state, time left and the forecast from now to the end of the day, scaled per day."""
    f = np.asarray(forecast)
    mu, sd = f.mean(1, keepdims=True), f.std(1, keepdims=True) + 1.0
    z = (f - mu) / sd
    ahead = np.concatenate([z[:, t:], np.repeat(z[:, -1:], t, axis=1)], axis=1)
    return np.concatenate([((energy - E_MIN) / (E_MAX - E_MIN))[:, None], np.full((len(f), 1), (T - t) / T),
                           mu / 100.0, sd / 100.0, ahead], axis=1).astype('float32')


class Policy(nn.Module):
    def __init__(self, hidden=PPO['hidden']):
        super().__init__()
        n = 4 + T
        self.actor = nn.Sequential(nn.Linear(n, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 2))
        self.critic = nn.Sequential(nn.Linear(n, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def distribution(self, x):
        ab = nn.functional.softplus(self.actor(x)) + 1
        return Beta(ab[..., 0], ab[..., 1])

    def power(self, a):
        return (2 * a - 1) * P   # Beta sample in (0, 1) -> MW in (-P, P)


def run_days(policy, forecasts, prices, deterministic=True):
    """Play whole days; returns realized EUR per day and throughput in MWh."""
    energy = np.full(len(forecasts), E0)
    profit, through = np.zeros(len(forecasts)), np.zeros(len(forecasts))
    for t in range(T):
        x = torch.as_tensor(observe(forecasts, energy, t))
        with torch.no_grad():
            dist = policy.distribution(x)
            a = dist.mean if deterministic else dist.sample()
        energy, ac = project(energy, policy.power(a).numpy(), T - t)
        profit += step_profit(ac, prices[:, t])
        through += np.abs(ac) * DT
    assert np.abs(energy - E0).max() < 1e-9
    return profit, through


def train(seed, train_f, train_p, val_f, val_p, cfg=PPO, log=None):
    """PPO on whole days; the checkpoint with the best mean validation profit is kept."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    m = Policy(cfg['hidden'])
    opt = torch.optim.Adam(m.parameters(), lr=cfg['lr'])
    best, state, selected, history = -np.inf, None, 0, []
    for update in range(1, cfg['updates'] + 1):
        idx = rng.integers(0, len(train_f), cfg['days_per_update'])
        f, p = train_f[idx], train_p[idx]
        energy = np.full(len(idx), E0)
        xs, acts, lps, vs, rs = [], [], [], [], []
        for t in range(T):
            x = torch.as_tensor(observe(f, energy, t))
            with torch.no_grad():
                dist = m.distribution(x)
                a = dist.sample().clamp(1e-4, 1 - 1e-4)
                v, lp = m.critic(x).squeeze(-1), dist.log_prob(a)
            energy, ac = project(energy, m.power(a).numpy(), T - t)
            xs.append(x), acts.append(a), lps.append(lp), vs.append(v)
            rs.append(torch.as_tensor(step_profit(ac, p[:, t]) * cfg['reward_scale'], dtype=torch.float32))
        val, rew = torch.stack(vs), torch.stack(rs)
        adv, gae, nextv = torch.zeros_like(rew), torch.zeros_like(rew[0]), torch.zeros_like(val[0])
        for t in reversed(range(T)):
            gae = rew[t] + cfg['gamma'] * nextv - val[t] + cfg['gamma'] * cfg['gae_lambda'] * gae
            adv[t], nextv = gae, val[t]
        ret = adv + val
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        x, a = torch.stack(xs).flatten(0, 1), torch.stack(acts).flatten(0, 1)
        oldlp, ad, target = torch.stack(lps).flatten(0, 1), adv.flatten(0, 1), ret.flatten(0, 1)
        for _ in range(cfg['epochs']):
            dist = m.distribution(x)
            ratio = (dist.log_prob(a) - oldlp).exp()
            actor = -torch.minimum(ratio * ad, ratio.clamp(1 - cfg['clip'], 1 + cfg['clip']) * ad).mean()
            critic = (m.critic(x).squeeze(-1) - target).square().mean()
            loss = actor + 0.5 * critic - cfg['entropy'] * dist.entropy().mean()
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite training loss')
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(), cfg['grad_clip'])
            opt.step()
        if update % 10 == 0:
            score = float(run_days(m, val_f, val_p)[0].mean())
            history.append({'update': update, 'validation_eur_per_day': score})
            if log:
                log(update, score)
            if score > best:
                best, state, selected = score, copy.deepcopy(m.state_dict()), update
    m.load_state_dict(state)
    return m, {'selected_update': selected, 'validation_best_eur_per_day': best, 'history': history}
