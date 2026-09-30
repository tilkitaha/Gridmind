"""Read-only verification of delivered records; does not retrain or re-run EVM."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def verify():
 checks={}
 m=read('reproducibility_manifest.json')
 checks['manifest_hashes']=all((ROOT/p).is_file() and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in m['files'].items())
 control=read('results/extension/control_results.json')
 checks['input_matches_experiment']=hashlib.sha256((ROOT/'data/storenet_h1_h6_15min.csv').read_bytes()).hexdigest()==control['data_sha256']
 checks['ten_checkpoints']=len(list((ROOT/'results/extension/models').glob('*.pt')))==10
 sums=defaultdict(lambda:[0.,0.,0])
 with (ROOT/'results/extension/household_episode_results.csv').open() as f:
  for r in csv.DictReader(f):
   a=sums[(r['method'],r['seed'])];a[0]+=float(r['cost_eur']);a[1]+=float(r['savings_vs_idle_eur']);a[2]+=1
 with (ROOT/'results/extension/seed_totals.csv').open() as f:
  totals=list(csv.DictReader(f))
 checks['all_household_records']=len(sums)==13 and all(a[2]==44*6 for a in sums.values())
 checks['aggregate_cost_and_savings']=all(math.isclose(sums[(r['method'],r['seed'])][0],float(r['cost_eur']),abs_tol=1e-8) and math.isclose(sums[(r['method'],r['seed'])][1],float(r['savings_vs_idle_eur']),abs_tol=1e-8) for r in totals)
 ledger=read('results/extension/ledger_results.json')
 checks['recorded_ledger_parity']=ledger['exact_balance_parity'] is True and sum(ledger['balances'])==6000000000 and ledger['stream_count']==64
 checks['ten_recorded_ledger_checks']=len(ledger['tests'])==10 and all(ledger['tests'].values())
 checks['recorded_test_suite']='Ran 24 tests' in (ROOT/'results/extension/test_log.txt').read_text() and '\nOK' in (ROOT/'results/extension/test_log.txt').read_text()
 print(json.dumps({'scope':'Saved records and hashes only. No fresh training, EVM run or signature verification.','checks':checks,'all_passed':all(checks.values())},indent=2))
 return all(checks.values())
if __name__=='__main__':raise SystemExit(0 if verify() else 1)
