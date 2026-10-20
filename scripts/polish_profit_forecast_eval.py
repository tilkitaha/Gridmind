"""Run from the repository root with PYTHONPATH=src; no raw market data needed."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from gridmind_research.profit_forecast import evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='results/polish_profile/daily.csv')
    parser.add_argument('--out', required=True)
    parser.add_argument('--window-days', type=int, default=28)
    parser.add_argument('--min-days', type=int, default=14)
    args = parser.parse_args()
    source, out = Path(args.input), Path(args.out)
    if out.exists():
        parser.error('Output directory already exists; use a new directory')
    with source.open(newline='', encoding='utf-8') as stream:
        daily, summary = evaluate(list(csv.DictReader(stream)), args.window_days, args.min_days)
    summary['inputs_sha256'] = {source.as_posix(): hashlib.sha256(source.read_bytes()).hexdigest()}
    root = Path(__file__).resolve().parents[1]
    summary['code_sha256'] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ('src/gridmind_research/profit_forecast.py',
                     'scripts/polish_profit_forecast_eval.py')}
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'daily.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(daily[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(daily)
    (out / 'results.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n',
                                    encoding='utf-8', newline='\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
