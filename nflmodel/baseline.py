"""The spreadsheet model ("NFL Model 2022-2024"), rebuilt in Python so it can be backtested.

Copied from the sheet's formulas (Google Sheet 1ZtHSWj76sACIeQZES0Kp5Ste2i6OTDYRhDCCodS1NaI):

  Seven prediction tabs each produce an expected score for both teams, and AVG PREDICTIONS blends them
  with AVERAGE.WEIGHTED using fixed weights: OVERALL 10, 2.0 35, LAST 3 35, HOME/AWAY 15, PF/PA 5,
  LAST YEAR 0, LAST YEAR 2.0 0.

  Each tab computes expected points as
      offense strength x opponent defense strength x league average points x home factor
  from the points-for side and from the points-against side, then averages the two.

  OVERALL / LAST 3 / HOME-AWAY / PF-PA use the "TEAM STATS" strength index built on teamrankings.com
  per-game stats, each stat expressed as a ratio to the league average:
      off = (3 PPG + RZ TD + passer rating - 2 giveaways + RZ att - sacks taken - penalties/2 + yds/play + 3rd%) / 4.5
      def = (3 - 2.5 takeaways + opp RZ TD + 3 opp PPG + opp rating + opp RZ att + penalties/2 + opp rush att
             + (1 - sacks) + opp yds/play + opp 3rd% + (2 - opp 4th att)) / 11
  The home/away tab uses the same shape with slightly different coefficients (see HA_OFF / HA_DEF).

  2.0 uses the "TEAM STATS 2.0" index built on Pro-Football-Reference season totals, each stat a ratio to the
  league average, weighted by the stat's same-season correlation with points from the Stat Corelations tab.

  Home factors: OVERALL 0.92 on the away team's points-for and 1.08 on the home team's points-against;
  2.0, LAST 3 and PF/PA use 0.98 and 1.02; HOME/AWAY uses the home and away split stats instead.

  Win probability: a Poisson grid on the two expected scores (0 to 60), ties split in half.
  Bet rules (BETS tab): take the spread when the model differs from the line by 3 points, the total by 4.

What the sheet could not do, and what this copy does instead:
  * The sheet was only ever filled in for the current week. This copy recomputes every window from
    play-by-play so that, for any week of any season, it sees only games played before that week.
  * Week 1 has no current-season stats. The sheet's season columns would have been empty; this copy uses
    the previous season's full-season stats for every window until a team has played, and last season's
    final three games as its "last 3". Home/away splits fall back to last season per team until the team
    has played a home (or away) game.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import poisson

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"

WEIGHTS = {"overall": 10.0, "two": 35.0, "last3": 35.0, "homeaway": 15.0, "pfpa": 5.0, "lastyear": 0.0, "lastyear2": 0.0}
SPREAD_EDGE, TOTAL_EDGE = 3.0, 4.0

# 2.0 stat weights = same-season correlations from the sheet's Stat Corelations tab
TWO_OFF = {"pf": 0.698, "sc_pct": 0.626, "anya": 0.617, "rz_td": 0.616, "ko_yds": 0.575, "rate": 0.578,
           "first_downs": 0.559, "td_pct": 0.540, "third_pct": 0.539, "start": 0.418}
TWO_DEF = {"pa": 0.529, "opp_rush_td": 0.471, "opp_nya": 0.410, "opp_sc_pct": 0.445, "opp_rate": 0.436,
           "opp_pass_att": 0.425, "opp_rz_att": 0.386, "opp_td_pct": 0.374, "opp_first_downs": 0.343, "opp_third_pct": 0.295}


def passer_rating(cmp, att, yds, td, inte):
    att = np.maximum(att, 1)
    a = np.clip((cmp / att - 0.3) * 5, 0, 2.375)
    b = np.clip((yds / att - 3) * 0.25, 0, 2.375)
    c = np.clip((td / att) * 20, 0, 2.375)
    d = np.clip(2.375 - (inte / att) * 25, 0, 2.375)
    return (a + b + c + d) / 6 * 100


def rates(box: pd.DataFrame) -> pd.DataFrame:
    """Per-team per-game rates over a window of team-game rows (sum first, then divide)."""
    s = box.groupby("team").sum(numeric_only=True)
    g = box.groupby("team").size().rename("g")
    s = s.join(g)
    r = pd.DataFrame(index=s.index)
    r["g"] = s.g
    r["pf"] = s.pf / s.g
    r["pa"] = s.pa / s.g
    r["rz_td"] = s.off_rz_tds / s.g
    r["opp_rz_td"] = s.def_rz_tds / s.g
    r["rz_att"] = s.off_rz_trips / s.g
    r["opp_rz_att"] = s.def_rz_trips / s.g
    r["rate"] = passer_rating(s.off_completions, s.off_pass_att, s.off_pass_yards, s.off_pass_td, s.off_interceptions)
    r["opp_rate"] = passer_rating(s.def_completions, s.def_pass_att, s.def_pass_yards, s.def_pass_td, s.def_interceptions)
    r["giveaways"] = (s.off_interceptions + s.off_fumbles_lost) / s.g
    r["takeaways"] = (s.def_interceptions + s.def_fumbles_lost) / s.g
    r["sacked"] = s.off_sacks / s.g
    r["sacks"] = s.def_sacks / s.g
    r["pen"] = s.off_penalties / s.g
    r["ypp"] = s.off_yards / s.off_plays.clip(lower=1)
    r["opp_ypp"] = s.def_yards / s.def_plays.clip(lower=1)
    r["third_pct"] = s.off_third_conv / (s.off_third_conv + s.off_third_fail).clip(lower=1)
    r["opp_third_pct"] = s.def_third_conv / (s.def_third_conv + s.def_third_fail).clip(lower=1)
    r["opp_rush_att"] = s.def_rush_att / s.g
    r["opp_fourth_att"] = (s.def_fourth_conv + s.def_fourth_fail) / s.g
    # 2.0 (PFR-style) stats
    r["sc_pct"] = s.off_scoring_drives / s.off_drives.clip(lower=1)
    r["opp_sc_pct"] = s.def_scoring_drives / s.def_drives.clip(lower=1)
    r["anya"] = (s.off_pass_yards + 20 * s.off_pass_td - 45 * s.off_interceptions - s.off_sack_yards) / (s.off_pass_att + s.off_sacks).clip(lower=1)
    r["opp_nya"] = (s.def_pass_yards - s.def_sack_yards) / (s.def_pass_att + s.def_sacks).clip(lower=1)
    r["ko_yds"] = s.off_ko_yards / s.g
    r["first_downs"] = s.off_first_downs / s.g
    r["opp_first_downs"] = s.def_first_downs / s.g
    r["td_pct"] = s.off_pass_td / s.off_pass_att.clip(lower=1)
    r["opp_td_pct"] = s.def_pass_td / s.def_pass_att.clip(lower=1)
    r["start"] = s.off_start_own_sum / s.off_start_n.clip(lower=1)
    r["opp_rush_td"] = s.def_rush_td / s.g
    r["opp_pass_att"] = s.def_pass_att / s.g
    return r


def ratio(r: pd.DataFrame) -> pd.DataFrame:
    """Each stat divided by the league average of the 32 team values (the sheet's row 37 / row 49)."""
    return r.drop(columns="g") / r.drop(columns="g").mean()


def ts_strength(x: pd.DataFrame, kind="overall") -> pd.DataFrame:
    """TEAM STATS index (teamrankings tabs). x = ratios to league average."""
    if kind == "homeaway":
        off = (3 * x.pf + x.rz_td + x.rate - x.giveaways + x.rz_att - x.sacked - x.pen / 2 + x.ypp + x.third_pct) / 5.5
        de = (3 - 2 * x.takeaways + x.opp_rz_td + 2 * x.pa + x.opp_rate + x.opp_rz_att + x.pen / 2 + x.opp_rush_att
              + (1 - x.sacks) + x.opp_ypp + x.opp_third_pct + (2 - x.opp_fourth_att)) / 10.5
    else:
        off = (3 * x.pf + x.rz_td + x.rate - 2 * x.giveaways + x.rz_att - x.sacked - x.pen / 2 + x.ypp + x.third_pct) / 4.5
        de = (3 - 2.5 * x.takeaways + x.opp_rz_td + 3 * x.pa + x.opp_rate + x.opp_rz_att + x.pen / 2 + x.opp_rush_att
              + (1 - x.sacks) + x.opp_ypp + x.opp_third_pct + (2 - x.opp_fourth_att)) / 11
    return pd.DataFrame({"off": off, "def": de})


def two_strength(x: pd.DataFrame) -> pd.DataFrame:
    """TEAM STATS 2.0 index: correlation-weighted average of PFR stat ratios, scaled so the league average is 1."""
    off = sum(w * x[k] for k, w in TWO_OFF.items()) / sum(TWO_OFF.values())
    de = sum(w * x[k] for k, w in TWO_DEF.items()) / sum(TWO_DEF.values())
    return pd.DataFrame({"off": off / off.mean(), "def": de / de.mean()})


def poisson_win(exp_a, exp_h, n=61):
    """P(away wins), P(home wins) from independent Poissons on 0..60, ties split."""
    k = np.arange(n)
    pa = poisson.pmf(k, exp_a)
    ph = poisson.pmf(k, exp_h)
    grid = np.outer(pa, ph)  # [away, home]
    p_away = np.tril(grid, -1).sum()
    p_home = np.triu(grid, 1).sum()
    tie = np.trace(grid)
    return p_away + tie / 2, p_home + tie / 2


class Windows:
    """Stat windows for a given (season, week): what the sheet's tabs would have shown before kickoff."""

    def __init__(self, box: pd.DataFrame, season: int, week: int):
        reg = box[box.game_type == "REG"]
        cur = reg[(reg.season == season) & (reg.week < week)]
        last = reg[reg.season == season - 1]
        self.cur, self.last = cur, last
        self.teams = sorted(set(reg[reg.season == season].team))
        self.season_rates = self._with_fallback(cur, last)
        # last 3: the team's most recent three games this season, last season's final three if none yet
        cur3 = cur.sort_values("week").groupby("team").tail(3)
        last3 = last.sort_values("week").groupby("team").tail(3)
        self.last3_rates = self._with_fallback(cur3, last3)
        self.home_rates = self._with_fallback(cur[cur.home], last[last.home])
        self.away_rates = self._with_fallback(cur[~cur.home], last[~last.home])
        self.lastyear_rates = rates(last).reindex(self.teams)

    def _with_fallback(self, cur, last):
        rc = rates(cur) if len(cur) else pd.DataFrame()
        rl = rates(last)
        out = rl.reindex(self.teams).copy()
        if len(rc):
            have = rc.index.intersection(out.index)
            out.loc[have] = rc.loc[have]
        return out


def predict_week(box: pd.DataFrame, games: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    w = Windows(box, season, week)
    R = {k: getattr(w, k + "_rates") for k in ["season", "last3", "home", "away", "lastyear"]}
    X = {k: ratio(v) for k, v in R.items()}
    S = {"overall": ts_strength(X["season"]), "last3": ts_strength(X["last3"]),
         "home": ts_strength(X["home"], "homeaway"), "away": ts_strength(X["away"], "homeaway"),
         "two": two_strength(X["season"]), "lastyear": ts_strength(X["lastyear"]), "lastyear2": two_strength(X["lastyear"])}
    L = {k: (v.pf.mean(), v.pa.mean()) for k, v in R.items()}  # league average PPG and PA per window
    rows = []
    gw = games[(games.season == season) & (games.week == week)]
    for g in gw.itertuples():
        a, h = g.away_team, g.home_team
        if a not in S["overall"].index or h not in S["overall"].index:
            continue
        comp = {}

        def pair(st, lp, la, f_pf, f_pa, own_pf=None, own_pa=None):
            # points-for side, then points-against side, averaged, as each sheet tab does
            a_pf = st["off"][a] * st["def"][h] * (own_pf[a] if own_pf is not None else lp) * f_pf
            h_pf = st["off"][h] * st["def"][a] * (own_pf[h] if own_pf is not None else lp)
            a_pa_side = st["def"][h] * st["off"][a] * (own_pa[h] if own_pa is not None else la)       # what home allows
            h_pa_side = st["def"][a] * st["off"][h] * (own_pa[a] if own_pa is not None else la) * f_pa  # what away allows
            return (a_pf + a_pa_side) / 2, (h_pf + h_pa_side) / 2

        comp["overall"] = pair(S["overall"], *L["season"], 0.92, 1.08)
        comp["two"] = pair(S["two"], *L["season"], 0.98, 1.02)
        comp["last3"] = pair(S["last3"], *L["last3"], 0.98, 1.02)
        # home/away tab: home team's home offense vs away team's away defense, league home/away averages
        ha_a = (S["away"]["off"][a] * S["home"]["def"][h] * L["away"][0] + S["away"]["def"][a] * S["home"]["off"][h] * L["season"][1]) / 2
        ha_h = (S["home"]["off"][h] * S["away"]["def"][a] * L["home"][0] + S["home"]["def"][h] * S["away"]["off"][a] * L["season"][1]) / 2
        comp["homeaway"] = (ha_a, ha_h)
        comp["pfpa"] = pair(S["overall"], *L["season"], 0.98, 1.02, own_pf=R["season"].pf, own_pa=R["season"].pa)
        comp["lastyear"] = pair(S["lastyear"], *L["lastyear"], 0.98, 1.02)
        comp["lastyear2"] = pair(S["lastyear2"], *L["lastyear"], 0.98, 1.02)
        wsum = sum(WEIGHTS.values())
        exp_a = sum(WEIGHTS[k] * comp[k][0] for k in WEIGHTS) / wsum
        exp_h = sum(WEIGHTS[k] * comp[k][1] for k in WEIGHTS) / wsum
        p_a, p_h = poisson_win(exp_a, exp_h)
        row = {"game_id": g.game_id, "season": season, "week": week, "away_team": a, "home_team": h,
               "away_exp": exp_a, "home_exp": exp_h, "p_home": p_h,
               "model_spread": exp_h - exp_a, "model_total": exp_a + exp_h,
               "games_played": int(R["season"].g.get(h, 0)) if len(w.cur) else 0}
        for k, (ca, ch) in comp.items():
            row[f"{k}_away"], row[f"{k}_home"] = ca, ch
        rows.append(row)
    return pd.DataFrame(rows)


def run(seasons, box=None, games=None, weeks=None) -> pd.DataFrame:
    box = pd.read_parquet(OUT / "team_box.parquet") if box is None else box
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    out = []
    for s in seasons:
        wks = sorted(games[(games.season == s)].week.unique()) if weeks is None else weeks
        for wk in wks:
            out.append(predict_week(box, games, s, wk))
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2019-2025")
    a = ap.parse_args()
    lo, hi = (a.seasons.split("-") + [a.seasons])[:2]
    pred = run(range(int(lo), int(hi) + 1))
    OUT.mkdir(exist_ok=True)
    pred.to_parquet(OUT / "pred_baseline.parquet", index=False)
    print(pred.shape)
    print(pred.tail(8).to_string())
