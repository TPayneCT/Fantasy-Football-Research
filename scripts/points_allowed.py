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
# Defense and special-teams touchdowns (returns, fumble recoveries, blocked kicks). Kept separately
# so the dashboard can show DEF points with these unpredictable scores left out.
TD_KEYS = ("def_td", "def_st_td", "st_td", "fum_rec_td")
# Offensive touchdown points per player (including long-TD bonuses), kept as [passing, rushing, receiving]
# so the dashboard can leave out RB/WR/TE TDs, QB rushing TDs or QB passing TDs.
OFF_TD_KEYS = (("pass_td", "pass_td_40p", "pass_td_50p"),
               ("rush_td", "rush_td_40p", "rush_td_50p"),
               ("rec_td", "rec_td_40p", "rec_td_50p"))
# Raw stats kept for each player's box score on the dashboard (zeros left out).
BOX_KEYS = ("pass_cmp", "pass_att", "pass_yd", "pass_td", "pass_int", "pass_2pt",
            "rush_att", "rush_yd", "rush_td", "rush_2pt",
            "rec_tgt", "rec", "rec_yd", "rec_td", "rec_2pt", "fum_lost",
            "fgm", "fga", "fgm_0_19", "fgm_20_29", "fgm_30_39", "fgm_40_49", "fgm_50p", "xpm", "xpa",
            "pts_allow", "yds_allow", "sack", "int", "fum_rec", "def_td", "def_st_td", "st_td",
            "fum_rec_td", "safe", "blk_kick")


def category(key):
    """Group a scoring key into the label shown in the dashboard's points breakdown."""
    if "40p" in key or "50p" in key or key.startswith("bonus_"):
        return "Big-play bonuses"
    named = {"pass_yd": "Passing yds", "rush_yd": "Rushing yds", "rec_yd": "Receiving yds", "rec": "Receptions",
             "pass_td": "Passing TDs", "rush_td": "Rushing TDs", "rec_td": "Receiving TDs",
             "pass_int": "Turnovers", "fum_lost": "Turnovers", "fum": "Turnovers",
             "pass_2pt": "2-pt conversions", "rush_2pt": "2-pt conversions", "rec_2pt": "2-pt conversions",
             "xpm": "Extra points", "xpmiss": "Extra points",
             "sack": "Sacks", "int": "Interceptions", "safe": "Safeties", "blk_kick": "Blocked kicks",
             "def_2pt": "Defensive 2-pt returns"}
    if key in named:
        return named[key]
    if key.startswith("fg"):
        return "Field goals"
    if key.startswith("pts_allow"):
        return "Points allowed"
    if key.startswith("yds_allow"):
        return "Yards allowed"
    if key.endswith("_td"):
        return "Return / defensive TDs"
    if "fum_rec" in key or key.endswith("ff"):
        return "Fumbles forced / recovered"
    return "Other"


def breakdown(stats, scoring_settings):
    """[[label, points], ...] for every scoring category that produced points, largest first."""
    out = defaultdict(float)
    for k, w in scoring_settings.items():
        if w and stats.get(k):
            out[category(k)] += stats[k] * w
    return sorted(([label, round(v, 2)] for label, v in out.items() if round(v, 2)), key=lambda x: -abs(x[1]))


def completed_weeks(season, state):
    games = [g for g in sleeper.schedule(season, refresh=str(season) == state["season"])
             if g["status"] != "canceled"]
    return sorted({g["week"] for g in games}
                  - {g["week"] for g in games if g["status"] != "complete"})


def build(season, scoring_settings, state):
    rows = []
    for week in completed_weeks(season, state):
        # Re-fetch the latest week in case of stat corrections; earlier weeks come from cache.
        stats = sleeper.weekly_stats(season, week, refresh=str(season) == state["season"] and week >= state["week"] - 1)
        allowed = defaultdict(lambda: {"points": 0.0, "td_points": 0.0, "players": []})
        for r in stats:
            pos = (r.get("player") or {}).get("position")
            if pos not in POSITIONS or not r.get("opponent") or not r["stats"].get("gp"):
                continue
            pts = score(r["stats"], scoring_settings)
            name = "{} {}".format(r["player"].get("first_name", ""), r["player"].get("last_name", "")).strip()
            cell = allowed[(r["opponent"], pos)]
            cell["points"] += pts
            if pos == "DEF":
                cell["td_points"] += score({k: r["stats"].get(k, 0) for k in TD_KEYS}, scoring_settings)
            player = {"id": r["player_id"], "name": name, "team": r["team"], "pts": pts}
            box = {k: r["stats"][k] for k in BOX_KEYS if r["stats"].get(k)}
            if box:
                player["s"] = box
            bd = breakdown(r["stats"], scoring_settings)
            if bd:
                player["b"] = bd
            if pos in ("QB", "RB", "WR", "TE"):
                td = [score({k: r["stats"].get(k, 0) for k in keys}, scoring_settings) for keys in OFF_TD_KEYS]
                if any(td):
                    player["td"] = td
            cell["players"].append(player)
        for (defense, pos), cell in sorted(allowed.items()):
            players = sorted(cell["players"], key=lambda p: -p["pts"])
            rows.append({"season": int(season), "week": week, "defense": defense, "position": pos,
                         "points": round(cell["points"], 2), "players": players,
                         **({"td_points": round(cell["td_points"], 2)} if pos == "DEF" else {})})
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
