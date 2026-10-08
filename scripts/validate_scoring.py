"""Check our scores against the points Sleeper awarded in this league's matchups.

Usage: python scripts/validate_scoring.py [weeks...]   (default: all completed weeks)
"""
import json
import sys
from pathlib import Path

import sleeper
from scoring import score

config = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
lg = sleeper.league(config["league_id"])
settings = lg["scoring_settings"]
state = sleeper.nfl_state()
weeks = [int(w) for w in sys.argv[1:]] or range(1, state["week"])

checked = mismatched = 0
for week in weeks:
    stats = sleeper.weekly_stats(lg["season"], week)
    for team in sleeper.matchups(config["league_id"], week):
        for pid, official in (team["players_points"] or {}).items():
            ours = score(stats.get(pid, {}), settings)
            checked += 1
            if abs(ours - official) > 0.011:
                mismatched += 1
                print(f"week {week} player {pid}: ours {ours} vs sleeper {official}")

print(f"{checked} player-weeks checked, {mismatched} mismatches")
sys.exit(1 if mismatched else 0)
