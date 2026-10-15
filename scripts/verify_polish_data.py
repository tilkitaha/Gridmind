"""Check a local ENTSO-E download against the committed provenance hashes.

The raw prices, actual load and generation are not in the repository: on the ENTSO-E list of
data for free re-use (CC-BY 4.0, version 18 October 2023) only the load forecast (6.1.b) of
these items appears, so the others are not redistributed here. Anyone with an API token can
download them again with the fetch scripts; this check then shows whether the files match
the ones the results were computed from. A mismatch means ENTSO-E has republished a value.
Run from project root:
  python scripts/verify_polish_data.py
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('data/polish')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    missing, wrong, ok = [], [], 0
    for name in ('prices', 'features'):
        base = ROOT / name
        prov = json.loads((base / 'provenance.json').read_text(encoding='utf-8'))
        for req in prov['requests']:
            files = {base / 'raw' / req['raw_file']: req['raw_sha256']}
            folder = 'days' if req.get('currency', 'EUR') == 'EUR' else f"days_{req['currency'].lower()}"
            files.update({base / folder / f'{day}.csv': h for day, h in req.get('days', {}).items()
                          if not h.startswith('excluded')})
            for path, expected in files.items():
                if not path.exists():
                    missing.append(path.as_posix())
                elif sha(path) != expected:
                    wrong.append(path.as_posix())
                else:
                    ok += 1
    print(f'{ok} files match, {len(missing)} missing, {len(wrong)} differ')
    for path in wrong:
        print('differs:', path)
    if missing:
        print('missing (download with scripts/fetch_entsoe_prices.py and fetch_entsoe_features.py):', missing[0], '...')
    sys.exit(1 if missing or wrong else 0)


if __name__ == '__main__':
    main()
