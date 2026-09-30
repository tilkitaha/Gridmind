"""Recorded exploratory reward and action/budget comparisons, separate from original runs."""
import copy
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.distributions import Beta, Categorical

from .battery import ACTIONS, BatteryBatch, load_episodes

torch.set_num_threads(1)


def potential(cumulative):
    """Negative variance of signed cumulative EUR / fixed 1 EUR reference."""
    return -np.var(cumulative, axis=-1)


def observation(env, cumulative, fairness_state):
    x = env.obs()
    if not fairness_state:
        return x
    mean = np.broadcast_to(cumulative.mean(-1, keepdims=True), cumulative.shape)
    return np.concatenate([x, cumulative[..., None], mean[..., None]], -1).astype('float32')


class AblationPolicy(nn.Module):
    def __init__(self, kind, action='discrete', fairness_state=False):
        super().__init__()
        self.kind, self.action, self.fairness_state = kind, action, fairness_state
        n = 14 if fairness_state else 12
        self.actor = nn.Sequential(nn.Linear(n, 32), nn.Tanh(), nn.Linear(32, 32),
                                   nn.Tanh(), nn.Linear(32, 2 if action == 'continuous' else 5))
        self.critic = nn.Sequential(nn.Linear(n*6 if kind == 'MAPPO' else n, 32), nn.Tanh(),
                                    nn.Linear(32,32), nn.Tanh(), nn.Linear(32,1))

    def distribution(self, x):
        y = self.actor(x)
        if self.action == 'discrete':
            return Categorical(logits=y)
        ab = nn.functional.softplus(y) + 1
        return Beta(ab[..., 0], ab[..., 1])

    def value(self, x):
        return (self.critic(x.flatten(-2)).expand(*x.shape[:-1]) if self.kind == 'MAPPO'
                else self.critic(x).squeeze(-1))

    def request(self, a):
        a = a.detach().numpy()
        return a - .5 if self.action == 'continuous' else ACTIONS[a]

    def deterministic(self, x):
        dist = self.distribution(x)
        a = dist.mean if self.action == 'continuous' else dist.logits.argmax(-1)
        return self.request(a)


def evaluate(model, eps):
    env = BatteryBatch(eps)
    cost = np.zeros((len(eps), 6)); gain = cost.copy(); throughput = cost.copy()
    projection = 0; count = 0; residual = 0; requested_abs = 0
    for _ in range(16):
        with torch.no_grad():
            request = model.deterministic(torch.as_tensor(observation(env, gain, model.fairness_state)))
        _,_,_,d = env.step(request)
        cost += d['cost']; gain += d['benefit']; throughput += np.abs(d['ac'])
        projection += int((np.abs(request-d['ac']) > 1e-8).sum()); count += request.size
        requested_abs += float(np.abs(request).sum())
        residual = max(residual, float(np.abs(d['residual']).max()))
    return {'cost':cost,'gain':gain,'throughput':throughput,
            'energy_residual':residual,'terminal_residual':float(np.abs(env.soc-1).max()),
            'projection_fraction':projection/count,'requested_abs_kwh':requested_abs,
            'mean_episode_variance_eur2':float(np.var(gain,axis=1).mean())}


def train(kind, seed, action, updates, fairness_state, weight, eps, validation, path):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    m = AblationPolicy(kind, action, fairness_state)
    opt = torch.optim.Adam(m.parameters(), lr=.0003)
    best = -np.inf; logs=[]; start=time.perf_counter()
    for update in range(1, updates+1):
        env = BatteryBatch([eps[i] for i in rng.integers(0,len(eps),12)])
        cumulative=np.zeros((12,6)); xs=[]; acts=[]; lps=[]; vs=[]; rs=[]; ent=[]
        for _ in range(16):
            x=torch.as_tensor(observation(env,cumulative,fairness_state))
            with torch.no_grad():
                dist=m.distribution(x); a=dist.sample(); v=m.value(x); lp=dist.log_prob(a)
            before=potential(cumulative)
            _,r,_,d=env.step(m.request(a)); cumulative += d['benefit']
            # Same common reward for all agents. gamma=1; potential telescopes.
            shaped=r + weight*(potential(cumulative)-before)[:,None]
            xs.append(x);acts.append(a);lps.append(lp);vs.append(v)
            rs.append(torch.as_tensor(shaped,dtype=torch.float32));ent.append(float(dist.entropy().mean()))
        val=torch.stack(vs);rew=torch.stack(rs);adv=torch.zeros_like(rew)
        gae=torch.zeros_like(rew[0]);nextv=torch.zeros_like(val[0])
        for t in reversed(range(16)):
            gae=rew[t]+nextv-val[t]+.95*gae;adv[t]=gae;nextv=val[t]
        ret=adv+val;adv=(adv-adv.mean())/(adv.std()+1e-8)
        x=torch.stack(xs).flatten(0,1);a=torch.stack(acts).flatten(0,1)
        oldlp=torch.stack(lps).flatten(0,1);ad=adv.flatten(0,1);target=ret.flatten(0,1)
        for _ in range(4):
            dist=m.distribution(x);ratio=(dist.log_prob(a)-oldlp).exp()
            actor=-torch.minimum(ratio*ad,ratio.clamp(.8,1.2)*ad).mean()
            vl=(m.value(x)-target).square().mean()
            loss=actor+.5*vl-.01*dist.entropy().mean()
            if not torch.isfinite(loss):raise RuntimeError('Nonfinite training loss')
            opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(m.parameters(),.5);opt.step()
        if update%10==0:
            z=evaluate(m,validation);score=float(z['gain'].sum(1).mean())
            logs.append({'update':update,'validation_savings':score,
                         'validation_variance_eur2':z['mean_episode_variance_eur2'],
                         'mean_training_entropy':float(np.mean(ent)),
                         'actor_loss':float(actor.detach()),'value_loss':float(vl.detach())})
            # Common economic validation rule isolates the training-reward intervention.
            if score>best:
                best=score;state=copy.deepcopy(m.state_dict());selected=update
    m.load_state_dict(state)
    payload={'kind':kind,'seed':seed,'action':action,'fairness_state':fairness_state,
             'weight':weight,'updates':updates,'selected_update':selected,'state_dict':state}
    torch.save(payload,path)
    return m,{'seconds':time.perf_counter()-start,'selected_update':selected,
              'validation_best':best,'validation_checkpoints':logs,
              'checkpoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--evaluate-only',action='store_true');a=p.parse_args()
    root=Path('results/ablations');root.mkdir(exist_ok=True);(root/'models').mkdir(exist_ok=True)
    protocol=json.loads(Path('configs/ablation_protocol.json').read_text())
    eps={s:load_episodes(s) for s in ['train','validation','test']}
    rows=[];runs=[]
    for spec in protocol['variants']:
        for kind in protocol['algorithms']:
            for seed in protocol['seeds']:
                name=f"{spec['name']}_{kind}_seed{seed}";path=root/'models'/f'{name}.pt'
                if a.evaluate_only:
                    saved=torch.load(path,weights_only=True)
                    m=AblationPolicy(kind,spec['action'],spec['fairness_state']);m.load_state_dict(saved['state_dict']);log={}
                else:
                    m,log=train(kind,seed,spec['action'],spec['updates'],spec['fairness_state'],
                                spec['weight'],eps['train'],eps['validation'],path)
                z=evaluate(m,eps['test'])
                info={'variant':spec['name'],'kind':kind,'seed':seed,**spec,**log,
                      'cost_eur':float(z['cost'].sum()),'saving_eur':float(z['gain'].sum()),
                      'throughput_kwh':float(z['throughput'].sum()),
                      'losing_households':int((z['gain'].sum(0)<-1e-9).sum()),
                      'pooled_variance_eur2':float(np.var(z['gain'].sum(0))),
                      **{k:z[k] for k in ['projection_fraction','requested_abs_kwh','mean_episode_variance_eur2','energy_residual','terminal_residual']}}
                runs.append(info)
                for j,ep in enumerate(eps['test']):
                    for h in range(6):rows.append({'variant':spec['name'],'kind':kind,'seed':seed,'start':ep['start'],
                        'household':h,'cost_eur':z['cost'][j,h],'savings_eur':z['gain'][j,h],'throughput_kwh':z['throughput'][j,h]})
                print(name,round(info['cost_eur'],6),flush=True)
                if not a.evaluate_only:(root/'progress.json').write_text(json.dumps(runs,indent=2))
    suffix='replay' if a.evaluate_only else 'results'
    (root/f'{suffix}.json').write_text(json.dumps({'protocol_sha256':hashlib.sha256(Path('configs/ablation_protocol.json').read_bytes()).hexdigest(),
        'data_sha256':hashlib.sha256(Path('data/storenet_h1_h6_15min.csv').read_bytes()).hexdigest(),
        'episodes':{k:len(v) for k,v in eps.items()},'torch':torch.__version__,'runs':runs},indent=2))
    pd.DataFrame(rows).to_csv(root/f'household_{suffix}.csv',index=False)


if __name__=='__main__':main()
