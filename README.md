# Fantasy Football Research

Research tools for The Undrafted Benchwarmers (Sleeper league `1389329271972954112`).

## Points Allowed Board

`dashboard/index.html` shows fantasy points each NFL defense allowed to QB, RB, WR, TE, K and DEF, scored with the league's own settings, plus this week's matchups and flags for my roster.

## Scripts

| Script | What it does |
|---|---|
| `scripts/update.py` | Refresh the current season and rebuild `dashboard/data.js` |
| `scripts/points_allowed.py [season]` | Build `data/points_allowed/{season}.json` |
| `scripts/build_dashboard_data.py` | Pack seasons, next week's schedule and my roster into `dashboard/data.js` |
| `scripts/validate_scoring.py` | Check our scoring against the league's matchup scores |

Settings live in `config.json`. Python 3.10+ with no extra packages.

The GitHub Action in `.github/workflows/update.yml` runs daily (and on demand) and commits refreshed data when anything changed.
