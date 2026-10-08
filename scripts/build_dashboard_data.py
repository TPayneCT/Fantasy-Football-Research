"""Pack data/points_allowed/*.json into dashboard/data.js for the static dashboard.

Format: window.PA_DATA = {generated, seasons: {season: [[week, defense, position, points, [[name, team, pts], ...]], ...]}}
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

seasons = {}
for f in sorted((ROOT / "data" / "points_allowed").glob("*.json")):
    seasons[f.stem] = [
        [r["week"], r["defense"], r["position"], r["points"],
         [[p["name"], p["team"], p["pts"]] for p in r["players"]]]
        for r in json.loads(f.read_text())
    ]

payload = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "seasons": seasons}
out = ROOT / "dashboard" / "data.js"
out.write_text("window.PA_DATA=" + json.dumps(payload, separators=(",", ":")) + ";\n")
print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1e6:.1f} MB, seasons {list(seasons)}")
