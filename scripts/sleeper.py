"""Thin client for the public Sleeper API with a local JSON cache."""
import json
import time
import urllib.request
from pathlib import Path

API = "https://api.sleeper.app/v1"
API_COM = "https://api.sleeper.com"
CACHE = Path(__file__).resolve().parent.parent / "data" / "raw"


def get(path, cache_name=None, refresh=False, base=API):
    """GET {base}{path}. If cache_name is set, read/write data/raw/{cache_name}."""
    cache_file = CACHE / cache_name if cache_name else None
    if cache_file and cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text())
    for attempt in range(4):
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "fantasy-football-research"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            break
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data))
    return data


def league(league_id):
    return get(f"/league/{league_id}")


def nfl_state():
    return get("/state/nfl")


def weekly_stats(season, week, refresh=False):
    """List of stat rows, each with player_id, team, opponent, player.position and stats."""
    return get(f"/stats/nfl/{season}/{week}?season_type=regular",
               f"stats/{season}/week_{week:02d}.json", refresh, API_COM)


def schedule(season, refresh=False):
    return get(f"/schedule/nfl/regular/{season}", f"schedule/{season}.json", refresh, API_COM)


def matchups(league_id, week):
    return get(f"/league/{league_id}/matchups/{week}")


def league_users(league_id):
    return get(f"/league/{league_id}/users")


def rosters(league_id):
    return get(f"/league/{league_id}/rosters")


def players(refresh=False):
    """All NFL players keyed by player_id (about 5 MB, cached)."""
    return get("/players/nfl", "players.json", refresh)
