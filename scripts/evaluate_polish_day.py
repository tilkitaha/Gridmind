"""Evaluate a supplied, timestamped forecast; never download or trade."""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from gridmind_research.polish_market import BESS, optimize_schedule, realized_profit, validate_day


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--day",required=True)
    p.add_argument("--forecast",type=Path,required=True)
    p.add_argument("--realized",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise SystemExit("Output exists; choose a new path to preserve the previous record")
    forecast_frame=pd.read_csv(args.forecast)
    predicted=validate_day(forecast_frame,args.day,forecast=True)
    spec=BESS()
    # Decision is fixed before any realized price file is read.
    schedule=optimize_schedule(predicted,spec)
    actual=validate_day(pd.read_csv(args.realized),args.day)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    result={"day":args.day,"status":"conditional_fixed_schedule_evaluation","assumptions":["Complete acceptance at realized zonal prices","No imbalance, exchange fees or network charges modeled","Default settlement cost zero; ledger conversion to EUR not measured","Input publication timestamps are supplied metadata, not externally attested"],"forecast_sha256":sha(args.forecast),"realized_sha256":sha(args.realized),"spec":asdict(spec),"profit_eur":realized_profit(schedule,actual,spec),"schedule":{k:v.tolist() for k,v in schedule.items()}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))
    print("Wrote conditional evaluation",args.output)

if __name__=="__main__":main()
