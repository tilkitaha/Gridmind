"""Compare profit/error selection locally, without raw data or network access."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from gridmind_research.forecast_selection import evaluate


def report_markdown(summary):
    lines = ['# Profit versus error: exploratory forecast selection', '',
             'Retained development outcomes; no independent test or new model training.', '',
             'Both selectors use the same candidates and dates. Rolling choices use only',
             'earlier days; frozen June choices use January-May only.', '']
    for name in ('all_scored_days', 'june_validation'):
        period = summary[name]
        lines += [f'## {name.replace("_", " ").title()} ({period["days"]} days)', '',
                  '| Method | EUR/day | MAE EUR/MWh | Losing days |',
                  '| --- | ---: | ---: | ---: |']
        for arm, values in period['methods'].items():
            lines.append(f'| {arm} | {values["eur_per_day"]:.2f} | '
                         f'{values["mae_eur_mwh"]:.2f} | {values["losing_days"]} |')
        lines += ['', 'Paired differences in EUR/day (exploratory 95% intervals):', '']
        for contrast, values in period['comparisons'].items():
            lines.append(f'- {contrast}: {values["mean_eur_per_day"]:.2f} '
                         f'[{values["lower95"]:.2f}, {values["upper95"]:.2f}]')
        lines.append('')
    lines += ['## Limits', '', *[f'- {s}' for s in summary['limits']], '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='results/polish_forecast/daily.csv')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        parser.error('Output directory already exists; use a new directory')
    source = Path(args.input)
    raw = source.read_bytes()
    records = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    daily, decisions, summary = evaluate(records)
    summary['inputs_sha256'] = {source.as_posix(): hashlib.sha256(raw).hexdigest()}
    root = Path(__file__).resolve().parents[1]
    summary['code_sha256'] = {
        p: hashlib.sha256((root / p).read_bytes()).hexdigest()
        for p in ('src/gridmind_research/forecast_selection.py',
                  'scripts/compare_forecast_selection.py')}
    out.mkdir(parents=True, exist_ok=False)
    fields = list(dict.fromkeys(key for row in daily for key in row))
    with (out / 'daily.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(daily)
    for name, value in [('results.json', summary), ('decisions.json', decisions)]:
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n',
                                encoding='utf-8', newline='\n')
    report = report_markdown(summary)
    (out / 'REPORT.md').write_text(report, encoding='utf-8', newline='\n')
    print(report)


if __name__ == '__main__':
    main()
