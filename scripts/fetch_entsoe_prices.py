"""Download Polish day-ahead prices from ENTSO-E and write the realized-price contract.

The token is read only from the ENTSOE_TOKEN environment variable and is never
stored or printed. Every raw response is kept with its SHA-256, retrieval time
and token-free query, and per-day CSVs are written only for complete days.
Run from project root with PYTHONPATH=src:
  python scripts/fetch_entsoe_prices.py --start 2026-07-01 --end 2026-07-31 --out data/polish/prices
"""
import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from gridmind_research.entsoe import API, parse_prices, query, split_days
from gridmind_research.polish_market import delivery_index, validate_day


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True, help='first local delivery date')
    ap.add_argument('--end', required=True, help='last local delivery date, inclusive')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    token = os.environ.get('ENTSOE_TOKEN')
    if not token:
        raise SystemExit('Set ENTSOE_TOKEN in the environment; never pass it on the command line or in a file')
    out = Path(args.out)
    (out / 'raw').mkdir(parents=True, exist_ok=True)
    (out / 'days').mkdir(exist_ok=True)

    days = pd.date_range(args.start, args.end, freq='D')
    records = []
    # One request per calendar month keeps responses small and failures local.
    for month, group in pd.Series(days, index=days).groupby(days.to_period('M')):
        first, last = group.iloc[0], group.iloc[-1]
        q = query(delivery_index(str(first.date()))[0], delivery_index(str(last.date()))[-1] + pd.Timedelta(minutes=15))
        raw_path = out / 'raw' / f'{month}.xml'
        if raw_path.exists():
            raise SystemExit(f'Refusing to overwrite {raw_path}')
        url = API + '?' + urllib.parse.urlencode({'securityToken': token, **q})
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                body = r.read()
        except urllib.error.HTTPError as e:  # "no data" answers arrive as HTTP 400 with an XML body
            body = e.read()
        raw_path.write_bytes(body)
        record = {'month': str(month), 'query': q, 'retrieved_utc': datetime.now(UTC).isoformat(),
                  'raw_file': raw_path.name, 'raw_sha256': hashlib.sha256(body).hexdigest(), 'days': {}}
        try:
            frame, record['resolutions'] = parse_prices(body)
        except LookupError as e:
            record['error'] = str(e)
            records.append(record)
            continue
        parsed = split_days(frame)
        for day in group:
            day = str(day.date())
            try:
                validate_day(parsed[day], day)
            except (KeyError, ValueError) as e:
                record['days'][day] = f'excluded: {e}'
                continue
            path = out / 'days' / f'{day}.csv'
            parsed[day].to_csv(path, index=False, lineterminator='\n')
            record['days'][day] = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(record)
        print(month, sum(not str(v).startswith('excluded') for v in record['days'].values()), 'complete days', flush=True)
    (out / 'provenance.json').write_text(json.dumps({
        'source': 'ENTSO-E Transparency Platform, day-ahead prices 12.1.D (A44)',
        'note': 'Published values at retrieval time; earlier publication versions are not audited by this script.',
        'requests': records}, indent=2), newline='\n')


if __name__ == '__main__':
    main()
