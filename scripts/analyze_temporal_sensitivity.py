"""AI-assisted conditional temporal uncertainty analysis; no confirmatory claims."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def intervals(x):
 x=np.asarray(x,float);n=len(x);result={}
 for b in [1,2,3,7,14]:
  if b>n:continue
  rng=np.random.default_rng(25092026);starts=rng.integers(0,n,size=(10000,int(np.ceil(n/b))))
  idx=((starts[:,:,None]+np.arange(b))%n).reshape(10000,-1)[:,:n]
  low,high=np.quantile(x[idx].mean(1),[.025,.975])
  result[str(b)]=[float(low),float(high)]
 return result

def contrast(x):
 x=np.asarray(x,float)
 return {'total_eur': float(x.sum()),'mean_per_retained_day_eur': float(x.mean()),'days': len(x),'negative_days': int((x<-1e-9).sum()),'ties': int((np.abs(x)<=1e-9).sum()),'positive_days': int((x>1e-9).sum()),'intervals': intervals(x),'leave_one_day_out_mean_range': [float(((x.sum()-x)/(len(x)-1)).min()),float(((x.sum()-x)/(len(x)-1)).max())]}

def main():
 out=Path('results/temporal_sensitivity');out.mkdir(exist_ok=True)
 p=Path('results/forecast_control/household_results.csv');df=pd.read_csv(p);df['date']=df.start.str[:10]
 day=df.groupby(['date','method']).cost_eur.sum().unstack();x=day.ridge-day.persistence
 day.assign(ridge_minus_persistence=x).to_csv(out/'june_daily.csv')
 june={'status': 'Exploratory conditional sensitivity; selected and reused June data','source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),'ridge_minus_persistence': contrast(x)}
 (out/'june.json').write_text(json.dumps(june,indent=2))
 root=Path('results/later_period');keys=[p.stem for p in Path('results/ablations/models').glob('*.pt')]+['idle','rule','persistence_mpc','daily_mpc','ridge_mpc'];files=[root/(k+'.csv') for k in sorted(keys)]
 assert len(files)==65,len(files)
 data=pd.concat([pd.read_csv(p) for p in files],ignore_index=True);assert data.groupby('method').size().eq(501*6).all()
 assert not data.duplicated(['method','start','household']).any()
 data['date']=data.start.str[:10];daily=data.groupby(['date','method']).cost_eur.sum().unstack();daily.to_csv(root/'daily_costs.csv')
 base=data[data.method=='idle'].set_index(['start','household']).cost_eur
 for key,g in data.groupby('method'):
  g=g.set_index(['start','household']);np.testing.assert_allclose(g.cost_eur+g.saving_eur,base.reindex(g.index),rtol=1e-12,atol=1e-12)
 variance=data.groupby(['method','start']).saving_eur.var(ddof=0).groupby('method').mean()
 variance.to_csv(root/'episode_benefit_variance.csv')
 rows=[json.loads((root/(p.stem+'.json')).read_text()) for p in files];summary=pd.DataFrame(rows).sort_values('method');summary.to_csv(root/'summary.csv',index=False)
 data.groupby(['method','household'])[['cost_eur','saving_eur','throughput_kwh']].sum().to_csv(root/'household_summary.csv')
 summary['family']=summary.method.str.replace(r'_seed\d+$','',regex=True)
 fam=summary.groupby('family').agg(cost_mean_eur=('cost_eur','mean'),cost_sd_eur=('cost_eur','std'),saving_mean_eur=('saving_eur','mean'),throughput_mean_kwh=('throughput_kwh','mean'),runs=('method','size')).fillna(0)
 fam.to_csv(root/'family_summary.csv')
 elig=pd.read_csv(root/'eligibility.csv')
 for key in ['month','hour']:
  c=elig.groupby(key).eligible.agg(['sum','count']);c.columns=['eligible','candidate'];c['coverage_pct']=100*c.eligible/c.candidate;c.to_csv(root/f'{"monthly" if key=="month" else "hour"}_coverage.csv')
 primary=daily.filter(regex=r'^discrete_300_IPPO_seed').mean(axis=1)-daily.persistence_mpc
 ridge=daily.ridge_mpc-daily.persistence_mpc
 daily.assign(primary=primary,ridge_minus_persistence=ridge).groupby(daily.index.str[:7])[['primary','ridge_minus_persistence']].sum().to_csv(root/'monthly_contrasts.csv')
 families={k:daily.filter(regex='^'+k+'_seed').mean(axis=1) for k in ['fairness_control_IPPO','fairness_weight01_IPPO','fairness_control_MAPPO','fairness_weight01_MAPPO']}
 results={'status': 'Exploratory temporal extension reconstructed after prior partial access','episodes': 501,'candidate_episodes': len(elig),'eligible_days': len(daily),'calendar_days': 184,'coverage_pct': float(100*elig.eligible.mean()),'retained_intervals': 501*16,'bootstrap': '10000 circular moving-block draws; seed 25092026; eligible source-day order; unadjusted conditional intervals','primary': contrast(primary),'ridge_minus_persistence': contrast(ridge),'fairness_IPPO': contrast(families['fairness_weight01_IPPO']-families['fairness_control_IPPO']),'fairness_MAPPO': contrast(families['fairness_weight01_MAPPO']-families['fairness_control_MAPPO']),'max_energy_residual': float(summary.energy_residual.max()),'max_terminal_residual': float(summary.terminal_residual.max()),'source_day_gaps': int((pd.Series(pd.to_datetime(daily.index)).diff().dt.days.dropna()>1).sum()),'max_source_day_gap_days': float(pd.Series(pd.to_datetime(daily.index)).diff().dt.days.max()),'all_65_arms_complete': True}
 (root/'results.json').write_text(json.dumps(results,indent=2,allow_nan=False))
 print(json.dumps(results,indent=2));print(fam.to_string())

if __name__=='__main__':main()
