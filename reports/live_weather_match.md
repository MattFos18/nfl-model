# Live weather matches the backtest; as-of centring; checks leave the stored fits alone (2 Oct 2026)

**Claim** (re-audit of 2 Oct 2026, items 3, 5 and 6; approved as correctness fixes: "the backtest must price exactly as
live does"):
1. Live games should be priced on the same weather readings the backtest prices played games on.
2. `players.opponent_strength` should centre on the league average known before the week, not the whole season's.
3. The leak checks should not rewrite the tracked `data/processed/trees_cache.parquet`.

This is a fix, not an adoption: no new input, no rule change, so no study gate. Script: `experiments/live_weather_match.py`
(table in reports/live_weather_match.csv).

## 1. Live weather (item 3)
Before: an unplayed game's wind_out and cold came from Open-Meteo's kickoff hour (`weather.apply_to_games`), and its
points-equation rain from Open-Meteo's chance (trends). The backtest (`model.priced_weather`, #389) prices played games
2018+ on the GFS MOS / Japan reading (`wind_live.readings`), the GFS MOS temperature and the GFS MOS rain chance
(`RAIN_FC`). The totals equation's rain and the wind points already read MOS live.

Now `weather.live_source` gives each unplayed outdoor game its MOS reading where `wind_live` has one (wind = the wind-under
reading, temperature = `gfs_temp`, rain = `gfs_pop` at 50%+), Open-Meteo only where no reading exists (66 to 96 hours
out, or a failed pull). `apply_to_games` writes it into the games table before the ratings step, `trends.situation_extras`
uses it for rain, the card shows it (its tooltip names the source), and the re-price fingerprint follows it. Each
Open-Meteo fallback is a `live weather` warning, and health counts the games on each source. Roofed games get no
reading (#391). The props keep Open-Meteo (`apply_to_games(mos=False)`).

Walk-forward 2015-2025 on the stored features, main (885fda94) against this branch, stored fits read only:

| Window | Spread flag | Totals flag | Wind under | Team points miss | Total miss |
|---|---|---|---|---|---|
| 2015-18 | 67-55 -> 67-55 | 132-117 -> 132-117 | 24-20 -> 24-20 | 7.4046 -> 7.4046 | 10.7507 -> 10.7507 |
| 2019-22 | 76-47 -> 76-47 | 190-146 -> 190-146 | 143-88 -> 143-88 | 7.3643 -> 7.3643 | 10.5161 -> 10.5161 |
| 2023-25 | 37-20 -> 37-20 | 82-59 -> 82-59 | 77-52 -> 77-52 | 7.2344 -> 7.2344 | 10.1029 -> 10.1029 |

All 3,028 games' spread, total, under chance, team points, wind points and rain points are identical (largest
difference 0.0). The backtest is unchanged, as it should be: only unplayed games move.

Week 4 of 2026 (the weekly run's Open-Meteo values -> MOS): NE@BUF wind 7.6 -> 9.2 mph, GB@TB 10.2 -> 7.2, DEN@SF
4.8 -> 8.2, NYJ@CHI 7.6 -> 9.1, LA@PHI 10.3 -> 8.4; ARI@NYG 64 -> 59 F; rain called by MOS (50%+) at TEN@BAL (78%),
LA@PHI (70%), ARI@NYG (58%) and DET@CAR (78%) where Open-Meteo had 67%, 33%, 5% and 81%. IND@WAS (Monday) has no MOS
reading yet and stays on Open-Meteo. DAL@HOU is roofed (#391) and gets no reading.

## 2. Centring on the weeks before (item 5)
`players.league_mean_before` replaces the full-season mean: the season's team-games before the week, the season before's
average in week 1. The centre moves by 0.017 EPA a pass play on average (90th percentile 0.042, largest 0.110) and 0.011
a run (0.025, 0.123). It feeds only the Players tab's "EPA against an average defense" (`positions.all_values`): the
game model and the props read raw values (`players.OPP_ADJUST` is off; nothing in `props.py`, `props_sit.py` or
`experiments/props_by_season.py` calls it), so the props backtest and `props.BACKTEST` / `BACKTEST_COUNTS` do not move.

## 3. The stored fits (item 6)
`model.trees_cache_read_only()` turns off the cache save and drops the fits made inside it. `audit.leakage_test`,
`audit.own_game_shift`, `audit.decision_confidence` and `tests/test_planted_leak.py` run inside it; the planted-leak
test now asserts the file's hash is unchanged, and `tests/test_live_weather_match.py` checks every `walk_forward` in
the audit is inside it.

## Decision
Shipped as a fix (PR live-weather-match). Live prices for unplayed games move where MOS and Open-Meteo disagree; the
backtest, the bet rules and the props do not.
