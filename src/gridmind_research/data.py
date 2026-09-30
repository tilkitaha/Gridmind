"""Strict conversion from StoreNet one-minute power to interval energy."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def prepare(raw_dir, out_dir, history_end="2020-06-14 23:45", output_filename="storenet_h1_h6_15min.csv"):
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames, quality = [], []
    for hid in range(1, 7):
        path = raw_dir / f"H{hid}_W.csv"
        d = pd.read_csv(path)
        d.columns = d.columns.str.strip()
        d["date"] = pd.to_datetime(d["date"], errors="raise")
        if d.date.duplicated().any() or not d.date.is_monotonic_increasing:
            raise ValueError("Duplicate or unordered timestamps")
        if not d.date.dt.second.eq(0).all():
            raise ValueError("Expected minute-aligned readings")
        columns = ["Consumption(W)", "Production(W)"]
        valid = np.isfinite(d[columns]).all(axis=1) & d[columns].ge(0).all(axis=1)
        # Hn_W is an availability indicator in the published files.
        valid &= d[f"H{hid}_W"].eq(1)
        powers = d.set_index("date")[columns].copy()
        powers.loc[~valid.to_numpy(), :] = np.nan
        count = powers.resample("15min").count().min(axis=1)
        energy = powers.resample("15min").sum(min_count=15) / 60000.0
        energy.loc[count != 15] = np.nan
        energy.columns = [f"H{hid}_load_kwh", f"H{hid}_pv_kwh"]
        frames.append(energy)
        quality.append(
            {
                "household": f"H{hid}",
                "source_rows": len(d),
                "invalid_minutes": int((~valid).sum()),
                "complete_15min_intervals": int(count.eq(15).sum()),
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    aligned = pd.concat(frames, axis=1).sort_index()
    aligned.index.name = "source_timestamp"
    # Source timestamps have no offset. Keep their clock labels unchanged.
    # No external weather/price series is joined until the source time zone is verified.
    history = aligned.loc["2020-01-01":history_end].copy()
    history.to_csv(out_dir / output_filename, float_format="%.10g")
    selected = history.loc["2020-06-01":"2020-06-14 23:45"]
    report = {
        "source": "StoreNet Figshare collection 6829134",
        "source_doi": "10.1038/s41597-024-03454-2",
        "households": [f"H{i}" for i in range(1, 7)],
        "clock": "source clock retained; UTC offset not independently verified",
        "resampling": "15 complete one-minute W samples summed / 60000 = kWh",
        "missing_policy": "no interpolation; drop a pilot interval for all methods if any house is missing",
        "pilot_start": "2020-06-01",
        "pilot_end": "2020-06-14",
        "pilot_expected_intervals": 14 * 96,
        "pilot_retained_intervals": int(selected.notna().all(axis=1).sum()),
        "quality": quality,
    }
    (out_dir / "data_quality.json").write_text(json.dumps(report, indent=2))
    return history, report
