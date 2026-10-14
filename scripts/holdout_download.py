"""Download, hash and process StoreNet households for the held-out 24-hour study.

Held-out households (anything outside H1-H6) are refused unless the protocol is
frozen and --confirm-frozen is given. Run from project root with PYTHONPATH=src.

Dry run on a development household:
  python scripts/holdout_download.py --households H1 --raw-dir data_raw/dev --out <dir>
"""
import argparse
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from gridmind_research.holdout import (
    DEVELOPMENT,
    figshare_files,
    prepare_households,
    protocol_frozen,
    sha,
)

PROTOCOL = Path('docs/PROTOCOL_24H_HOLDOUT_DRAFT.md')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--households', nargs='+', default=[f'H{i}' for i in range(7, 21)])
    ap.add_argument('--raw-dir', default='data_raw/holdout')
    ap.add_argument('--out', default='data/holdout')
    ap.add_argument('--confirm-frozen', action='store_true')
    args = ap.parse_args()
    held_out = [h for h in args.households if h not in DEVELOPMENT]
    if held_out and not (protocol_frozen(PROTOCOL) and args.confirm_frozen):
        raise SystemExit(f'Refusing to download held-out households {held_out}: '
                         'freeze the protocol first and pass --confirm-frozen.')
    raw, out = Path(args.raw_dir), Path(args.out)
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    data = out / f"storenet_{'_'.join(h.lower() for h in args.households)}_2020_15min.csv"
    if data.exists():
        raise SystemExit(f'Refusing to overwrite {data}')

    entries = figshare_files(args.households)
    for e in entries:
        target = raw / e['file']
        if not target.exists():
            with urllib.request.urlopen(e['url'], timeout=120) as src, target.open('wb') as dst:
                while part := src.read(1024 * 1024):
                    dst.write(part)
        if target.stat().st_size != e['size']:
            raise ValueError(f"Incomplete download: {e['file']}")
        e['sha256'] = sha(target)
        e['retrieved_utc'] = datetime.now(UTC).isoformat()
    (out / 'source_retrieval.json').write_text(json.dumps(entries, indent=2))

    processed, quality = prepare_households(raw, args.households)
    processed.to_csv(data, float_format='%.10g')
    (out / 'data_quality.json').write_text(json.dumps({
        'source': 'StoreNet Figshare collection 6829134', 'source_doi': '10.1038/s41597-024-03454-2',
        'households': args.households, 'clock': 'source clock retained; UTC offset not independently verified',
        'resampling': '15 complete one-minute W samples summed / 60000 = kWh', 'output_sha256': sha(data),
        'quality': quality}, indent=2))
    print(f'wrote {data} ({sha(data)})')


if __name__ == '__main__':
    main()
