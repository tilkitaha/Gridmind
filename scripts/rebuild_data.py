import hashlib
import json
import urllib.request
from pathlib import Path

from gridmind_research.data import prepare

root = Path(__file__).resolve().parents[1]
raw = root / "data_raw"
raw.mkdir(exist_ok=True)
for entry in json.loads((root / "data/source_manifest.json").read_text()):
    if not entry["file"].endswith("_W.csv"):
        continue
    target = raw / entry["file"]
    if not target.exists():
        with urllib.request.urlopen(entry["url"], timeout=60) as src, target.open("wb") as dst:
            while part := src.read(1024 * 1024):
                dst.write(part)
    if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Source changed or incomplete: " + entry["file"])
prepare(raw, root / "data")
