"""Download Polish load and generation series from ENTSO-E for the forecast inputs.

Series: day-ahead total load forecast (6.1.B), actual total load (6.1.A) and actual
generation per production type (16.1.B&C). The token is read only from ENTSOE_TOKEN.
Each raw response is kept with its SHA-256 and token-free query; every series is
also written as a 15-minute CSV. The candidate test window is refused.
Run from project root with PYTHONPATH=src:
  python scripts/fetch_entsoe_features.py --start 2025-09-20 --end 2026-06-30 --out data/polish/features
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

from gridmind_research.entsoe import (
    API,
    FEATURES,
    feature_query,
    parse_quantities,
    to_quarter_hours,
)
from gridmind_research.polish_market import delivery_index
from gridmind_research.polish_pilot import refuse_test_window


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True, help='first local delivery date')
    ap.add_argument('--end', required=True, help='last local delivery date, inclusive')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    token = os.environ.get('ENTSOE_TOKEN')
    if not token:
        raise SystemExit('Set ENTSOE_TOKEN in the environment; never pass it on the command line or in a file')
    try:
        refuse_test_window(args.start, args.end)
    except PermissionError as e:
        raise SystemExit(str(e)) from None
    out = Path(args.out)
    (out / 'raw').mkdir(parents=True, exist_ok=True)
    days = pd.date_range(args.start, args.end, freq='D')
    records = []
    for kind in FEATURES:
        frames = []
        for month, group in pd.Series(days, index=days).groupby(days.to_period('M')):
            first, last = group.iloc[0], group.iloc[-1]
            q = feature_query(kind, delivery_index(str(first.date()))[0],
                              delivery_index(str(last.date()))[-1] + pd.Timedelta(minutes=15))
            raw_path = out / 'raw' / f'{kind}_{month}.xml'
            if raw_path.exists():
                raise SystemExit(f'Refusing to overwrite {raw_path}')
            url = API + '?' + urllib.parse.urlencode({'securityToken': token, **q})
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    body = r.read()
            except urllib.error.HTTPError as e:  # "no data" answers arrive as HTTP 400 with an XML body
                body = e.read()
            raw_path.write_bytes(body)
            record = {'kind': kind, 'month': str(month), 'query': q, 'retrieved_utc': datetime.now(UTC).isoformat(),
                      'raw_file': raw_path.name, 'raw_sha256': hashlib.sha256(body).hexdigest()}
            try:
                f = parse_quantities(body)
            except LookupError as e:
                record['error'] = str(e)
                records.append(record)
                print(kind, month, 'error:', e, flush=True)
                continue
            record['resolutions'] = sorted(f.resolution.unique())
            record['keys'] = sorted(f.key.unique())
            record['points'] = len(f)
            frames.append(to_quarter_hours(f))
            records.append(record)
            print(kind, month, record['resolutions'], len(record['keys']), 'series', flush=True)
        if frames:
            wide = pd.concat(frames).pivot_table(index='timestamp_utc', columns='key', values='value_mw', aggfunc='first')
            path = out / f'{kind}.csv'
            if path.exists():  # keep earlier downloads; a timestamp already present keeps its first value
                old = pd.read_csv(path, index_col=0)
                wide = pd.concat([old, wide[~wide.index.isin(old.index)]])
            wide.sort_index().to_csv(path, lineterminator='\n')
    prov = out / 'provenance.json'
    earlier = json.loads(prov.read_text(encoding='utf-8'))['requests'] if prov.exists() else []
    prov.write_text(json.dumps({
        'source': 'ENTSO-E Transparency Platform: 6.1.B load forecast, 6.1.A actual load, 16.1.B&C generation per type',
        'note': 'MW levels; coarser periods are held for each quarter-hour. Published values at retrieval time.',
        'requests': earlier + records}, indent=2), newline='\n')


if __name__ == '__main__':
    main()
