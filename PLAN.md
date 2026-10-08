# Points Allowed Dashboard: Build Plan

League: `1389329271972954112` (Sleeper)

## Goal
A searchable dashboard showing fantasy points each NFL team allowed to QB, RB, WR, TE, K and DEF by week. Points are scored with this league's exact `scoring_settings`. The dashboard updates automatically after each week, covers multiple seasons and flags matchups for my roster.

## Data sources (public Sleeper API)
| Need | Endpoint |
|---|---|
| Scoring rules, roster slots, previous season's league | `GET /v1/league/{league_id}` (`scoring_settings`, `previous_league_id`) |
| Current season/week | `GET /v1/state/nfl` |
| Players: position and team | `GET /v1/players/nfl` (cache daily) |
| Weekly raw stats | `GET https://api.sleeper.app/stats/nfl/regular/{season}/{week}` |
| Schedule / opponents | Sleeper schedule endpoint, with nflverse `games.csv` as a backup |
| My roster | `GET /v1/league/{id}/users` + `GET /v1/league/{id}/rosters` (matched by my Sleeper username) |

Points are calculated from raw stats multiplied by league weights. Sleeper's precomputed point fields are not used.

## Core logic
1. For each completed week, score every player with league settings.
2. Map each player to his team that week and that team's opponent.
3. Aggregate by `season, week, defense_team, position`, giving points, player count and top scorer.
4. DEF points allowed = the DST points the opposing defense scored.

## Multi-season history
- Backfill prior seasons (start with 3: 2023 through 2025) into `data/history/{season}.json`.
- Score every season with the **current** league settings so years compare apples to apples. A toggle for "that season's league settings" is optional and uses `previous_league_id`.
- Finished seasons are fetched once and never re-pulled.
- Filters: season, week range, last-N weeks, full season.
- Caution shown in UI: early-season data leans on last year, and roster/coaching changes limit carryover.

## Upcoming matchups and roster flags
- **Upcoming opponent column:** for each team, next week's opponent and that opponent's points-allowed rank by position (last 4 weeks plus season-to-date).
- **Matchup tiers:** rank 1-8 = favorable (green), 9-24 = neutral, 25-32 = tough (red), based on points allowed versus league average.
- **My Roster view:** each of my rostered players with his position, next opponent, opponent's points allowed to that position, rank and tier flag. Starters versus bench and bye weeks are shown.
- **Optional:** the same view for my current opponent's roster and for top waiver-wire players.
- Config needs my Sleeper username (or roster ID) to identify my team.

## Dashboard views
1. **Heatmap:** teams × positions with average points allowed, sortable and filterable.
2. **Team drilldown:** weekly trend and the players who scored against them.
3. **Upcoming Matchups:** next opponent column with tiers.
4. **My Roster:** flagged matchups for my players.

## Architecture
```
config.json                  # league_id, sleeper_username, seasons
scripts/fetch_data.py        # fetch, score and aggregate
scripts/scoring.py           # league-settings scoring engine
data/raw/                    # cached weekly stats
data/history/{season}.json   # points allowed per season
data/upcoming.json           # next week's matchups and tiers
data/roster.json             # my roster with flags
dashboard/index.html         # static, client-side filtering
.github/workflows/update.yml # Tuesday morning plus Thursday refresh (injuries/roster moves)
```
Hosted on GitHub Pages (requires a public repo) or run locally.

## Phases
1. Scoring engine: validate against league matchup scores (`/league/{id}/matchups/{week}`).
2. Points-allowed aggregation for the current season.
3. Multi-season backfill.
4. Dashboard: heatmap, filters and drilldown.
5. Upcoming matchups and tiers.
6. My Roster flags.
7. Automation and deploy.

## Open items
- Sleeper username for roster lookup.
- Multi-position players: use Sleeper's primary position (default).
- Hosting: public Pages or local.
