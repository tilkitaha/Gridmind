"""Action trace of the exploratory 24-hour learners: requested versus applied energy by time of day.

Read-only on results/exploratory_rl_24h/models. Run from project root with
PYTHONPATH=src:scripts (src;scripts on Windows).
"""
import json

import numpy as np
import pandas as pd
import torch
from explore_rl_24h import DATA, OUT, Day, T, days, episodes

from gridmind_research.ablations import AblationPolicy
from gridmind_research.battery import tariff
from gridmind_research.holdout import fill, net_load


def main():
    houses = [f'H{i}' for i in range(1, 7)]
    raw = net_load(pd.read_csv(DATA, index_col=0, parse_dates=True), houses)
    test = episodes(raw, fill(raw, 'linear'), days(raw, '2020-07-01', '2020-12-31'))
    hours = np.arange(T) / 4
    out = {}
    for path in sorted((OUT / 'models').glob('*.pt')):
        s = torch.load(path, weights_only=False)
        m = AblationPolicy(s['kind'], s['action'], False)
        m.load_state_dict(s['state_dict'])
        m.eval()
        env = Day(test)
        req, ac, soc = [], [], []
        for _ in range(T):
            with torch.no_grad():
                r = m.deterministic(torch.as_tensor(env.obs()))
            _, d = env.step(r)
            req.append(r)
            ac.append(d['ac'])
            soc.append(env.soc.mean())
        req, ac = np.array(req), np.array(ac)
        applied = ac.mean(axis=(1, 2))
        out[path.stem] = {
            'share_of_steps_requesting_charge': float((req > 1e-9).mean()),
            'mean_request_kwh': float(req.mean()),
            'discharge_kwh_00_07': float(-applied[hours < 7].clip(max=0).sum()),
            'charge_kwh_last_hour': float(applied[hours >= 23].clip(min=0).sum()),
            'mean_soc_16_20': float(np.mean([soc[t] for t in range(T) if 16 <= hours[t] < 20])),
            'daily_throughput_per_battery_kwh': float(np.abs(ac).sum(0).mean()),
            'applied_by_hour_kwh': [float(applied[h * 4:(h + 1) * 4].sum()) for h in range(24)],
        }
    out['_tariff_by_hour_eur'] = [float(tariff(h)) for h in range(24)]
    (OUT / 'action_trace.json').write_text(json.dumps(out, indent=2), newline='\n')
    for k, v in out.items():
        if not k.startswith('_'):
            print(k, {x: round(y, 3) for x, y in v.items() if not isinstance(y, list)})


if __name__ == '__main__':
    main()
