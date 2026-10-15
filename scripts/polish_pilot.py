"""Descriptive pilot on downloaded Polish day-ahead prices, development period only.

Refuses the candidate test window of configs/polish_test_protocol.json until
that protocol is frozen. Run from project root with PYTHONPATH=src:
  python scripts/polish_pilot.py --days data/polish/prices/days --start 2025-10-01 --end 2026-06-30 --out results/polish_pilot
"""
import argparse
import hashlib
import json
from pathlib import Path

from gridmind_research.polish_market import BESS
from gridmind_research.polish_pilot import load_days, pilot, summarize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', required=True)
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if (out / 'results.json').exists():
        raise SystemExit(f'Refusing to overwrite {out / "results.json"}')
    try:
        prices, skipped = load_days(args.days, args.start, args.end)
    except PermissionError as e:
        raise SystemExit(str(e)) from None
    if not prices:
        raise SystemExit('No valid days in range')
    out.mkdir(parents=True, exist_ok=True)
    daily = pilot(prices)
    daily.to_csv(out / 'daily.csv', index=False, lineterminator='\n')
    monthly = daily.assign(month=daily.day.str[:7]).groupby('month')[
        ['spread_eur_mwh', 'oracle_eur', 'naive_d1_eur', 'naive_d7_eur']].mean()
    monthly.to_csv(out / 'monthly_means.csv', lineterminator='\n')
    sources = sorted(Path(args.days).glob('*.csv'))
    result = {
        'status': 'Descriptive pilot on development-period prices; not a test of any controller',
        'range': [args.start, args.end],
        'bess': BESS().__dict__,
        'assumptions': ['Full acceptance at the realized zonal price', 'No imbalance, exchange or network charges',
                        'Naive forecasts use only prices published before the D-1 12:00 gate'],
        'inputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
                          if p.stem in prices},
        'skipped_days': skipped,
        'summary': summarize(daily),
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False), newline='\n')
    print(json.dumps(result['summary'], indent=2))
    print(monthly.round(2).to_string())


if __name__ == '__main__':
    main()
