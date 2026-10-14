"""Derived descriptive analysis of saved results; does not fit or replay policies."""
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 with (ROOT/'results/extension/household_episode_results.csv').open() as f: rows=list(csv.DictReader(f))
 with (ROOT/'results/extension/seed_totals.csv').open() as f: totals=list(csv.DictReader(f))
 house=defaultdict(lambda:[0.,0.,0.]);episode=defaultdict(float)
 for r in rows:
  key=(r['method'],int(r['seed']),int(r['household']));a=house[key]
  for j,k in enumerate(['cost_eur','savings_vs_idle_eur','throughput_kwh']):a[j]+=float(r[k])
  episode[(r['method'],int(r['seed']),r['start'])]+=float(r['savings_vs_idle_eur'])
 derived=[]
 for r in totals:
  method,seed=r['method'],int(r['seed']);v=[x for (m,s,t),x in episode.items() if (m,s)==(method,seed)]
  hs=[house[(method,seed,h)] for h in range(6)];gain=float(r['savings_vs_idle_eur']);q=float(r['throughput_kwh'])
  derived.append({'method':method,'seed':seed,'cost_eur':float(r['cost_eur']),'saving_eur':gain,'throughput_kwh':q,'degradation_eur':.01*q,'saving_excluding_recorded_degradation_eur':gain+.01*q,'fixed_dispatch_break_even_degradation_eur_per_kwh':(gain+.01*q)/q if q>0 else None,'positive_episodes':sum(x>1e-9 for x in v),'negative_episodes':sum(x < -1e-9 for x in v),'zero_episodes':sum(abs(x)<=1e-9 for x in v),'minimum_episode_saving_eur':min(v),'maximum_episode_saving_eur':max(v),'negative_households':sum(x[1]<-1e-9 for x in hs),'households':[{'household':h+1,'cost_eur':a[0],'saving_eur':a[1],'throughput_kwh':a[2]} for h,a in enumerate(hs)]})
 by={(r['method'],r['seed']):r for r in derived};paired=[{'seed':s,'MAPPO_minus_IPPO_cost_eur':by[('MAPPO',s)]['cost_eur']-by[('IPPO',s)]['cost_eur']} for s in [11,22,33,44,55]]
 summary={}
 for m in ['IPPO','MAPPO']:
  costs=[r['cost_eur'] for r in derived if r['method']==m];summary[m]={'mean':statistics.mean(costs),'sample_sd':statistics.stdev(costs),'median':statistics.median(costs),'minimum':min(costs),'maximum':max(costs)}
 mpc_episode_savings={t:v for (m,seed,t),v in episode.items() if m=='MPC'}
 coverage=defaultdict(int)
 for t in mpc_episode_savings:coverage[t[11:13]]+=1
 output={'retained_episodes_by_start_hour':dict(coverage),'positive_mpc_episodes':{t:v for t,v in mpc_episode_savings.items() if v>1e-9},'scope':'Post hoc descriptive analysis of retained records. Fee sensitivity holds dispatch fixed; it is not policy retraining or MPC reoptimization. No inferential confidence interval is claimed.','input_sha256':hashlib.sha256((ROOT/'results/extension/household_episode_results.csv').read_bytes()).hexdigest(),'controllers':derived,'seed_summary':summary,'paired_seed_cost_differences':paired,'mean_paired_difference_eur':statistics.mean(r['MAPPO_minus_IPPO_cost_eur'] for r in paired)}
 path=ROOT/'results/extension/defense_analysis.json';path.write_text(json.dumps(output,indent=2)+'\n');print(path)
 print(json.dumps({'controllers':[{k:r[k] for k in ['method','seed','degradation_eur','saving_excluding_recorded_degradation_eur','positive_episodes','negative_episodes','zero_episodes','negative_households','fixed_dispatch_break_even_degradation_eur_per_kwh']} for r in derived],'seed_summary':summary,'paired':paired},indent=2))
if __name__=='__main__':main()
