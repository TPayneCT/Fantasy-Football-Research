"""Build fantasy points allowed by each NFL defense to each position, per week.

Usage: python scripts/points_allowed.py [season]   (default: current season)
Writes data/points_allowed/{season}.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import sleeper
from scoring import score

ROOT = Path(__file__).resolve().parent.parent
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def completed_weeks(season, state):
    games = sleeper.schedule(season, refresh=str(season) == state["season"])
    return sorted({g["week"] for g in games}
                  - {g["week"] for g in games if g["status"] != "complete"})


def build(season, scoring_settings, state):
    rows = []
    for week in completed_weeks(season, state):
        # Re-fetch the latest week in case of stat corrections; earlier weeks come from cache.
        stats = sleeper.weekly_stats(season, week, refresh=str(season) == state["season"] and week >= state["week"] - 1)
        allowed = defaultdict(lambda: {"points": 0.0, "players": []})
        for r in stats:
            pos = (r.get("player") or {}).get("position")
            if pos not in POSITIONS or not r.get("opponent") or not r["stats"].get("gp"):
                continue
            pts = score(r["stats"], scoring_settings)
            name = "{} {}".format(r["player"].get("first_name", ""), r["player"].get("last_name", "")).strip()
            cell = allowed[(r["opponent"], pos)]
            cell["points"] += pts
            cell["players"].append({"id": r["player_id"], "name": name, "team": r["team"], "pts": pts})
        for (defense, pos), cell in sorted(allowed.items()):
            players = sorted(cell["players"], key=lambda p: -p["pts"])
            rows.append({"season": int(season), "week": week, "defense": defense, "position": pos,
                         "points": round(cell["points"], 2), "players": players})
    return rows


def main():
    config = json.loads((ROOT / "config.json").read_text())
    state = sleeper.nfl_state()
    season = sys.argv[1] if len(sys.argv) > 1 else state["season"]
    settings = sleeper.league(config["league_id"])["scoring_settings"]
    rows = build(season, settings, state)
    out = ROOT / "data" / "points_allowed" / f"{season}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, separators=(",", ":")))
    print(f"{season}: {len(rows)} rows, weeks {sorted({r['week'] for r in rows})} -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
