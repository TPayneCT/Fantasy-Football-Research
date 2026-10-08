"""Pack everything the dashboard needs into dashboard/data.js.

window.PA_DATA = {
  generated,
  seasons: {season: [[week, defense, position, points, [[name, team, pts, player_id], ...]], ...]},
  upcoming: {season, week, games: [[away, home, date], ...]} or null,
  roster: {team_name, players: [{id, name, pos, team, starter}]} or null,
}
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import sleeper

ROOT = Path(__file__).resolve().parent.parent
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def seasons():
    out = {}
    for f in sorted((ROOT / "data" / "points_allowed").glob("*.json")):
        out[f.stem] = [
            [r["week"], r["defense"], r["position"], r["points"],
             [[p["name"], p["team"], p["pts"], p["id"]] for p in r["players"]]]
            for r in json.loads(f.read_text())
        ]
    return out


def upcoming(state):
    """The next week that still has games to play."""
    games = [g for g in sleeper.schedule(state["season"]) if g["status"] not in ("complete", "canceled")]
    if not games:
        return None
    week = min(g["week"] for g in games)
    week_games = [g for g in sleeper.schedule(state["season"]) if g["week"] == week and g["status"] != "canceled"]
    return {"season": state["season"], "week": week,
            "games": [[g["away"], g["home"], g["date"]] for g in sorted(week_games, key=lambda g: g["date"])]}


def roster(config):
    users = sleeper.league_users(config["league_id"])
    me = next((u for u in users if u["display_name"].lower() == config["sleeper_username"].lower()), None)
    if not me:
        print(f"warning: {config['sleeper_username']} not found in league; skipping roster")
        return None
    mine = next(r for r in sleeper.rosters(config["league_id"]) if r["owner_id"] == me["user_id"])
    starters = set(mine.get("starters") or [])
    db = sleeper.players(refresh=True)
    players = []
    for pid in mine.get("players") or []:
        p = db.get(pid, {})
        pos = p.get("position")
        if pos not in POSITIONS:
            continue
        name = p.get("full_name") or "{} {}".format(p.get("first_name", ""), p.get("last_name", "")).strip()
        players.append({"id": pid, "name": name if pos != "DEF" else f"{pid} D/ST", "pos": pos,
                        "team": p.get("team") or (pid if pos == "DEF" else None), "starter": pid in starters})
    order = {p: i for i, p in enumerate(POSITIONS)}
    players.sort(key=lambda p: (not p["starter"], order[p["pos"]], p["name"]))
    return {"team_name": (me.get("metadata") or {}).get("team_name") or me["display_name"], "players": players}


def main():
    config = json.loads((ROOT / "config.json").read_text())
    state = sleeper.nfl_state()
    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "seasons": seasons(),
        "upcoming": upcoming(state),
        "roster": roster(config),
    }
    out = ROOT / "dashboard" / "data.js"
    out.write_text("window.PA_DATA=" + json.dumps(payload, separators=(",", ":")) + ";\n")
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1e6:.1f} MB, seasons {list(payload['seasons'])}, "
          f"upcoming week {payload['upcoming'] and payload['upcoming']['week']}, "
          f"roster {payload['roster'] and len(payload['roster']['players'])} players")


if __name__ == "__main__":
    main()
