import csv
import hashlib
import json
import statistics
from pathlib import Path

P=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((P/'results/later_period/summary.csv').open())); lookup={x['method']:x for x in rows}
base=float(lookup['persistence_mpc']['cost_eur']); ridge=float(lookup['ridge_mpc']['cost_eur'])
metrics={'source':'results/later_period/summary.csv','source_sha256':hashlib.sha256((P/'results/later_period/summary.csv').read_bytes()).hexdigest(),'scope':'Descriptive reanalysis of retained exploratory results. No new training or independent test.','ridge_cost_reduction_eur':base-ridge,'ridge_cost_reduction_percent':100*(base-ridge)/base,'ridge_horizon_mae_reduction_percent':100*(1-float(lookup['ridge_mpc']['horizon_mae_kwh'])/float(lookup['persistence_mpc']['horizon_mae_kwh'])),'ridge_first_step_mae_increase_percent':100*(float(lookup['ridge_mpc']['first_step_mae_kwh'])/float(lookup['persistence_mpc']['first_step_mae_kwh'])-1),'families':[]}
for algo in ['IPPO','MAPPO']:
 for action in ['discrete','continuous']:
  for budget in [60,300]:
   a=[float(x['cost_eur']) for x in rows if x['method'].startswith(f'{action}_{budget}_{algo}_')]
   metrics['families'].append({'algorithm':algo,'action':action,'updates':budget,'seeds':len(a),'mean_cost_eur':statistics.mean(a),'min_cost_eur':min(a),'max_cost_eur':max(a),'mean_excess_over_persistence_eur':statistics.mean(a)-base})
(P/'results/release_analysis.json').write_text(json.dumps(metrics,indent=2)+'\n')
