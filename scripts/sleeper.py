"""Thin client for the public Sleeper API with a local JSON cache."""
import json
import time
import urllib.request
from pathlib import Path

API = "https://api.sleeper.app/v1"
CACHE = Path(__file__).resolve().parent.parent / "data" / "raw"


def get(path, cache_name=None, refresh=False):
    """GET {API}{path}. If cache_name is set, read/write data/raw/{cache_name}."""
    cache_file = CACHE / cache_name if cache_name else None
    if cache_file and cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text())
    for attempt in range(4):
        try:
            with urllib.request.urlopen(API + path, timeout=60) as resp:
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
    return get(f"/stats/nfl/regular/{season}/{week}", f"stats/{season}/week_{week:02d}.json", refresh)


def matchups(league_id, week):
    return get(f"/league/{league_id}/matchups/{week}")
