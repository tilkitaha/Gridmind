"""Exploratory: do the retained IPPO/MAPPO learners use 24-hour episodes?

Same actor/critic architecture, PPO settings, reward and May checkpoint rule as
ablations.py; only the episode length changes from 16 to 96 steps. Training
uses January-April days, selection May days, evaluation the 164 July-December
days of the MPC comparison. All dates were inspected before. Days keep at least
80 of 96 observed slots; gaps are filled linearly for simulation, while the
policy's previous-interval input is the latest complete raw row, as for MPC.
Run from project root with PYTHONPATH=src. Units: kWh per 15 min, EUR.
"""
import copy
import hashlib
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from gridmind_research.ablations import AblationPolicy
from gridmind_research.battery import DEGR, TARGET, N, project, settlement, tariff
from gridmind_research.holdout import fill, net_load

OUT = Path('results/exploratory_rl_24h')
DATA = Path('data/later_period/storenet_h1_h6_2020_15min.csv')
MPC = Path('results/exploratory_mpc_24h/linear/results.json')
T = 96
SEEDS = [11, 22, 33, 44, 55]
VARIANTS = [(kind, action) for action in ('discrete', 'continuous') for kind in ('IPPO', 'MAPPO')]
UPDATES = 300


def days(raw, first, last):
    ok = raw.notna().all(axis=1)
    observed = ok.loc[first:last].groupby(ok.loc[first:last].index.normalize()).sum()
    # A day needs some complete row before it, so the first input never wraps to the year's end.
    first_ok = ok.idxmax()
    return [d for d, n in observed.items() if n >= 80 and d > first_ok]


def episodes(raw, realized, starts):
    ok = raw.notna().all(axis=1).to_numpy()
    last = np.maximum.accumulate(np.where(ok, np.arange(len(ok)), -1))
    x, pos = raw.to_numpy(), {t: i for i, t in enumerate(raw.index)}
    out = []
    for s in starts:
        k = pos[s]
        assert last[k - 1] >= 0
        idx = raw.index[k:k + T]
        out.append({'start': str(s), 'net': realized.loc[idx].to_numpy(),
                    # previous-interval input at each step: latest complete raw row before it
                    'prev': np.stack([x[last[k + t - 1]] for t in range(T)]),
                    'hours': idx.hour.to_numpy() + idx.minute.to_numpy() / 60})
    return out


class Day:
    """BatteryBatch with T steps; same observation layout, settlement and projection."""

    def __init__(self, eps):
        self.net = np.stack([e['net'] for e in eps])
        self.prev = np.stack([e['prev'] for e in eps])
        self.hours = np.stack([e['hours'] for e in eps])
        self.soc = np.full((len(eps), N), TARGET)
        self.t = 0

    def obs(self):
        b = len(self.net)
        t = min(self.t, T - 1)
        h = self.hours[:, t]
        time_ = np.stack([np.sin(h * np.pi / 12), np.cos(h * np.pi / 12), np.full(b, (T - self.t) / T), tariff(h)], -1)
        return np.concatenate([self.soc[..., None] / 2, self.prev[:, t, :, None] / 2,
                               np.broadcast_to(time_[:, None, :], (b, N, 4)),
                               np.broadcast_to(np.eye(N)[None], (b, N, N))], -1).astype('float32')

    def step(self, request):
        self.soc, ac = project(self.soc, np.asarray(request), T - self.t)
        net, buy = self.net[:, self.t, :], tariff(self.hours[:, self.t])
        cost, *_ = settlement(net + ac, buy)
        base, *_ = settlement(net, buy)
        cost = cost + DEGR * np.abs(ac)
        self.t += 1
        if self.t == T:
            assert np.abs(self.soc - TARGET).max() < 1e-8
        gain = base - cost
        return np.repeat(gain.sum(1, keepdims=True) / N, N, axis=1), {'cost': cost, 'gain': gain, 'base': base, 'ac': ac}


def evaluate(model, eps):
    env = Day(eps)
    cost, gain, base, throughput = (np.zeros((len(eps), N)) for _ in range(4))
    for _ in range(T):
        with torch.no_grad():
            _, d = env.step(model.deterministic(torch.as_tensor(env.obs())))
        cost += d['cost']
        gain += d['gain']
        base += d['base']
        throughput += np.abs(d['ac'])
    return {'cost': cost, 'gain': gain, 'base': base, 'throughput': throughput}


def train(job):
    """ablations.train with T steps, no fairness term."""
    kind, action, seed, train_eps, validation = job
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    m = AblationPolicy(kind, action, False)
    opt = torch.optim.Adam(m.parameters(), lr=.0003)
    best, logs, start = -np.inf, [], time.perf_counter()
    for update in range(1, UPDATES + 1):
        env = Day([train_eps[i] for i in rng.integers(0, len(train_eps), 12)])
        xs, acts, lps, vs, rs = [], [], [], [], []
        for _ in range(T):
            x = torch.as_tensor(env.obs())
            with torch.no_grad():
                dist = m.distribution(x)
                a = dist.sample()
                v, lp = m.value(x), dist.log_prob(a)
            r, _ = env.step(m.request(a))
            xs.append(x)
            acts.append(a)
            lps.append(lp)
            vs.append(v)
            rs.append(torch.as_tensor(r, dtype=torch.float32))
        val, rew = torch.stack(vs), torch.stack(rs)
        adv, gae, nextv = torch.zeros_like(rew), torch.zeros_like(rew[0]), torch.zeros_like(val[0])
        for t in reversed(range(T)):
            gae = rew[t] + nextv - val[t] + .95 * gae
            adv[t] = gae
            nextv = val[t]
        ret = adv + val
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        x, a = torch.stack(xs).flatten(0, 1), torch.stack(acts).flatten(0, 1)
        oldlp, ad, target = torch.stack(lps).flatten(0, 1), adv.flatten(0, 1), ret.flatten(0, 1)
        for _ in range(4):
            dist = m.distribution(x)
            ratio = (dist.log_prob(a) - oldlp).exp()
            actor = -torch.minimum(ratio * ad, ratio.clamp(.8, 1.2) * ad).mean()
            vl = (m.value(x) - target).square().mean()
            loss = actor + .5 * vl - .01 * dist.entropy().mean()
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite training loss')
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(), .5)
            opt.step()
        if update % 10 == 0:
            z = evaluate(m, validation)
            score = float(z['gain'].sum(1).mean())
            logs.append({'update': update, 'validation_saving_per_day': score,
                         'validation_throughput_kwh': float(z['throughput'].sum())})
            if score > best:
                best, state, selected = score, copy.deepcopy(m.state_dict()), update
    m.load_state_dict(state)
    return kind, action, seed, state, {'seconds': time.perf_counter() - start, 'selected_update': selected,
                                       'validation_best_per_day': best, 'checkpoints': logs}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', help='write a 10-update, one-seed check to this directory instead')
    args = ap.parse_args()
    global OUT, UPDATES, SEEDS, VARIANTS
    if args.smoke:
        OUT, UPDATES, SEEDS, VARIANTS = Path(args.smoke), 10, [11], [('IPPO', 'discrete'), ('MAPPO', 'continuous')]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'models').mkdir(exist_ok=True)
    houses = [f'H{i}' for i in range(1, 7)]
    raw = net_load(pd.read_csv(DATA, index_col=0, parse_dates=True), houses)
    realized = fill(raw, 'linear')
    split = {name: episodes(raw, realized, days(raw, a, b)) for name, (a, b) in
             {'train': ('2020-01-01', '2020-04-30'), 'validation': ('2020-05-01', '2020-05-31'),
              'test': ('2020-07-01', '2020-12-31')}.items()}
    assert len(split['test']) == 164

    jobs = [(kind, action, seed, split['train'], split['validation']) for kind, action in VARIANTS for seed in SEEDS]
    with Pool(8) as pool:
        trained = pool.map(train, jobs)

    runs, rows = [], []
    for kind, action, seed, state, log in trained:
        name = f'{action}_300_{kind}_seed{seed}_24h'
        path = OUT / 'models' / f'{name}.pt'
        torch.save({'kind': kind, 'action': action, 'seed': seed, 'episode_steps': T, 'training': log,
                    'state_dict': state}, path)
        m = AblationPolicy(kind, action, False)
        m.load_state_dict(state)
        z = evaluate(m, split['test'])
        house = z['gain'].sum(0)
        runs.append({'name': name, 'kind': kind, 'action': action, 'seed': seed,
                     'saving_eur': float(z['gain'].sum()), 'idle_eur': float(z['base'].sum()),
                     'throughput_kwh': float(z['throughput'].sum()), 'losing_households': int((house < -1e-9).sum()),
                     'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **log})
        rows += [{'name': name, 'start': e['start'], 'household': houses[h], 'saving_eur': z['gain'][j, h]}
                 for j, e in enumerate(split['test']) for h in range(N)]
        print(name, round(runs[-1]['saving_eur'], 4), flush=True)
    pd.DataFrame(rows).to_csv(OUT / 'household_episode.csv', index=False, lineterminator='\n')
    # Models and outcomes are saved above; the MPC reference is only needed from here on.
    mpc = json.loads(MPC.read_text())['arms']
    bound = mpc['ridge_mpc_24h']['oracle_saving_eur']
    for r in runs:
        r['captured_pct_of_24h_bound'] = 100 * r['saving_eur'] / bound
    np.testing.assert_allclose(runs[0]['idle_eur'], mpc['ridge_mpc_24h']['cost_eur'] + mpc['ridge_mpc_24h']['saving_eur'],
                               rtol=1e-12)
    df = pd.DataFrame(runs)
    families = df.groupby(['action', 'kind']).agg(mean_saving_eur=('saving_eur', 'mean'), min_saving_eur=('saving_eur', 'min'),
                                                  max_saving_eur=('saving_eur', 'max'),
                                                  mean_captured_pct=('captured_pct_of_24h_bound', 'mean'),
                                                  mean_throughput_kwh=('throughput_kwh', 'mean'),
                                                  idle_like_seeds=('throughput_kwh', lambda s: int((s < 1e-6).sum())))
    families.to_csv(OUT / 'families.csv', lineterminator='\n')
    result = {
        'status': 'Exploratory 24-hour learners on previously inspected data; not confirmatory',
        'inputs': {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA, MPC]},
        'episodes': {k: len(v) for k, v in split.items()}, 'updates': UPDATES, 'episodes_per_update': 12,
        'torch': torch.__version__,
        'reference_24h': {'ridge_mpc_saving_eur': mpc['ridge_mpc_24h']['saving_eur'], 'oracle_saving_eur': bound},
        'runs': runs,
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(families.round(3).to_string())


if __name__ == '__main__':
    main()
