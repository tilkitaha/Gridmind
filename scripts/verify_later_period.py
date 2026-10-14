"""Read-only numerical and provenance audit of the temporal extension."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

root=Path('results/later_period');lock=json.loads((root/'execution_lock.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# The lock was written with the executing machine's absolute path; resolve it inside this checkout.
def rel(p):return p.split('/gridmind/',1)[1] if p.startswith('/') and '/gridmind/' in p else p
assert sha('configs/later_period_protocol.json')==lock['protocol_sha256']
assert sha('data/later_period/storenet_h1_h6_2020_15min.csv')==lock['data_sha256']
for group in ['code','models']:
 for p,h in lock[group].items():assert sha(rel(p))==h,p
assert len(lock['models'])==60
keys=[Path(p).stem for p in lock['models']]+['idle','rule','persistence_mpc','daily_mpc','ridge_mpc']
base=pd.read_csv(root/'idle.csv').set_index(['start','household'])
assert len(base)==501*6
for k in keys:
 d=pd.read_csv(root/f'{k}.csv').set_index(['start','household']);s=json.loads((root/f'{k}.json').read_text())
 assert d.index.is_unique and set(d.index)==set(base.index),k
 np.testing.assert_allclose(d.cost_eur+d.saving_eur,base.cost_eur.reindex(d.index),rtol=1e-12,atol=1e-12)
 for key,col in [('cost_eur','cost_eur'),('saving_eur','saving_eur'),('throughput_kwh','throughput_kwh')]:np.testing.assert_allclose(d[col].sum(),s[key],rtol=1e-12,atol=1e-9)
 assert s['energy_residual']<1e-8 and s['terminal_residual']<1e-8
 if k.startswith('discrete_300_'):assert d.throughput_kwh.abs().max()==0
e=pd.read_csv(root/'eligibility.csv');assert len(e)==1104 and e.eligible.sum()==501
assert e.eligible.equals(e.complete_block & e.complete_lag)
stats=json.loads((root/'results.json').read_text());assert stats['eligible_days']==168
print(json.dumps({'status': 'pass','arms': len(keys),'household_episode_rows': len(keys)*len(base),'source_and_model_hashes': True,'cost_counterfactual_identity': True,'all_discrete_300_idle': True,'eligibility': True},indent=2))
