"""AI-assisted frozen-model temporal extension. See protocol for prior-access history.
Run from project root with PYTHONPATH=src. Outputs never replace original runs.
"""
from pathlib import Path
import argparse, json, hashlib, sys, platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
from gridmind_research.data import prepare
from gridmind_research.battery import BatteryBatch, mpc_action
from gridmind_research.ablations import AblationPolicy, evaluate
from gridmind_research.forecast_control import load_net, fit_model, predict

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False))

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--raw-dir',required=True); ap.add_argument('--method'); args=ap.parse_args()
 out=Path('results/later_period');out.mkdir(parents=True,exist_ok=True)
 data=Path('data/later_period/storenet_h1_h6_2020_15min.csv')
 lock=out/'execution_lock.json'
 if args.method is None:
  if lock.exists(): raise RuntimeError('Refusing overwrite of existing execution lock')
  prepare(args.raw_dir,data.parent,'2020-12-31 23:45',data.name)
  d=pd.read_csv(data,index_col=0,parse_dates=True)
  old=pd.read_csv('data/storenet_h1_h6_15min.csv',index_col=0,parse_dates=True)
  np.testing.assert_allclose(d.reindex(old.index),old,rtol=0,atol=0,equal_nan=True)
  net=load_net(data);model,n=fit_model(net); saved=np.load('results/forecast_control/ridge_coefficients.npz')
  for k,v in dict(mean=model[0].mean_,scale=model[0].scale_,coef=model[1].coef_,intercept=model[1].intercept_).items():
   np.testing.assert_allclose(v,saved[k],atol=1e-12,rtol=1e-12)
  eps,elig=episodes(d)
  pd.DataFrame(elig).to_csv(out/'eligibility.csv',index=False)
  models=sorted(Path('results/ablations/models').glob('*.pt')); assert len(models)==60
  payload=dict(executed_utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha('configs/later_period_protocol.json'),data_sha256=sha(data),models={str(p):sha(p) for p in models},code={str(p):sha(p) for p in [Path(__file__),*Path('src/gridmind_research').glob('*.py')]},eligible_episodes=len(eps),training_prefix_exact=True,ridge_coefficients_match=True,training_rows=n,torch=torch.__version__,python=platform.python_version())
  with lock.open('x') as f:json.dump(payload,f,indent=2)
  print('LOCKED',len(eps),flush=True)
  for p in models:
   key=p.stem
   state=torch.load(p,weights_only=True);m=AblationPolicy(state['kind'],state['action'],state['fairness_state']);m.load_state_dict(state['state_dict']);m.eval()
   z=evaluate(m,eps);record(out,key,eps,z)
 else:
  saved=json.loads(lock.read_text());assert saved['protocol_sha256']==sha('configs/later_period_protocol.json');assert saved['data_sha256']==sha(data)
  for p,v in saved['code'].items():assert sha(p)==v,p
  d=pd.read_csv(data,index_col=0,parse_dates=True);eps,_=episodes(d);net=load_net(data);model,_=fit_model(net)
  key=args.method;assert key in ['idle','rule','persistence_mpc','daily_mpc','ridge_mpc']
  if (out/f'{key}.csv').exists(): raise RuntimeError('Refusing overwrite of completed arm')
  cost=[];gain=[];through=[];residual=terminal=0.;err1=errh=0.;n1=nh=fallback=0
  for j,ep in enumerate(eps):
   env=BatteryBatch([ep]);c=np.zeros(6);g=c.copy();t=c.copy()
   for step in range(16):
    if key=='idle':a=np.zeros((1,6))
    elif key=='rule':a=-env.prev
    else:
     f,missing=predict(net,pd.Timestamp(ep['start'])+pd.Timedelta(minutes=15*step),16-step,key.removesuffix('_mpc'),model)
     delta=np.abs(f-ep['net'][step:]);err1+=delta[0].sum();n1+=6;errh+=delta.sum();nh+=delta.size
     fallback+=missing if key!='persistence_mpc' else 0
     a=mpc_action(env,f)
    _,_,_,z=env.step(a);c+=z['cost'][0];g+=z['benefit'][0];t+=np.abs(z['ac'][0]);residual=max(residual,float(np.abs(z['residual']).max()))
   terminal=max(terminal,float(np.abs(env.soc-1).max()));cost.append(c);gain.append(g);through.append(t)
   if (j+1)%100==0:print(key,j+1,flush=True)
  z=dict(cost=np.asarray(cost),gain=np.asarray(gain),throughput=np.asarray(through),energy_residual=residual,terminal_residual=terminal)
  record(out,key,eps,z,dict(first_step_mae_kwh=float(err1/n1) if n1 else None,horizon_mae_kwh=float(errh/nh) if nh else None,daily_fallback_slots=fallback))

def episodes(d):
 out=[];rows=[]
 for start in pd.date_range('2020-07-01','2020-12-31 20:00',freq='4h'):
  idx=pd.date_range(start,periods=16,freq='15min');g=d.reindex(idx);prev=d.reindex([start-pd.Timedelta(minutes=15)])
  complete=bool(g.notna().all().all());lag=bool(prev.notna().all().all());keep=complete and lag
  rows.append(dict(start=str(start),eligible=keep,complete_block=complete,complete_lag=lag,month=start.strftime('%Y-%m'),hour=start.hour))
  if keep:out.append(dict(start=str(start),net=g.iloc[:,::2].to_numpy()-g.iloc[:,1::2].to_numpy(),lag=prev.iloc[:,::2].to_numpy()[0]-prev.iloc[:,1::2].to_numpy()[0],hours=idx.hour.to_numpy()+idx.minute.to_numpy()/60))
 return out,rows

def record(out,key,eps,z,extra=None):
 rows=[dict(method=key,start=ep['start'],household=f'H{h+1}',cost_eur=float(z['cost'][j,h]),saving_eur=float(z['gain'][j,h]),throughput_kwh=float(z['throughput'][j,h])) for j,ep in enumerate(eps) for h in range(6)]
 pd.DataFrame(rows).to_csv(out/f'{key}.csv',index=False)
 summary=dict(method=key,cost_eur=float(z['cost'].sum()),saving_eur=float(z['gain'].sum()),throughput_kwh=float(z['throughput'].sum()),energy_residual=z['energy_residual'],terminal_residual=z['terminal_residual'],losing_households=int((z['gain'].sum(0)<-1e-9).sum()),**(extra or {}))
 dump(out/f'{key}.json',summary);print(key,summary['cost_eur'],flush=True)

if __name__=='__main__':main()
