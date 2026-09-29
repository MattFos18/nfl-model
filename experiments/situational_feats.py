"""Candidate inputs for experiments/situational_game.py, every one as of before its game (29 Sep 2026).

Nothing here reads a market number (no spread, total or moneyline), and nothing reads a source the weekly run does not
already pull: the schedule (games.parquet: coaches, stadium_id, surface, roof, kickoff, weekday, referee, rest, the
starting QBs), team_games / team_box (per-game stats), the play-by-play (4th-down calls, shotgun, no-huddle), the
participation file (coverage, rushers, box; used only from the previous season, since it is published after a
season), snap counts, injury reports and weekly rosters (the same ones trends.injury_table reads). One static table is
built here by hand: the coordinates, elevation and time zone of the 52 stadiums used since 2012 (public facts that never
change; not a data pull).

"Residual" everywhere means the result against the model's own expectation for that game, never against a line: the
live model's walk-forward numbers (the blend spread and the total equation, each game priced before its week) for the
2014-2025 regular seasons, and before that (1999-2013, and playoff games) a plain as-of scoring rating built here from
scores alone (offense and defense points ratings updated after every week, 60% carried into the next season). A
history is the shrunk mean of a residual over the key's earlier games: sum / (n + K), K = 20 games (one value for every
history, set before any result; a key with a handful of games stays near zero). "Earlier" means an earlier week, so a
Thursday result never reaches the same week's Sunday game, exactly as the weekly run prices a whole week at once.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from nflmodel import model as M
from nflmodel.model import OUT

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
K_HIST = 20.0
FIX = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

# stadium_id -> (lat, lon, elevation ft, hours relative to US Eastern time during the season, country)
# Arizona does not observe daylight time: Pacific-equivalent (-3) until the first Sunday of November, Mountain (-2) after.
STADIUMS = {
    "ATL00": (33.7577, -84.4008, 1050, 0, "US"), "ATL97": (33.7554, -84.4010, 1050, 0, "US"), "BAL00": (39.2780, -76.6227, 30, 0, "US"),
    "BOS00": (42.0909, -71.2643, 290, 0, "US"), "BUF00": (42.7738, -78.7870, 640, 0, "US"), "BUF01": (43.6414, -79.3894, 250, 0, "CA"),
    "CAR00": (35.2258, -80.8528, 750, 0, "US"), "CHI98": (41.8623, -87.6167, 600, -1, "US"), "CIN00": (39.0955, -84.5161, 490, 0, "US"),
    "CLE00": (41.5061, -81.6995, 600, 0, "US"), "DAL00": (32.7473, -97.0945, 560, -1, "US"), "DEN00": (39.7439, -105.0201, 5280, -2, "US"),
    "DET00": (42.3400, -83.0456, 600, 0, "US"), "FRA00": (50.0686, 8.6455, 360, 6, "DE"), "GER00": (48.2188, 11.6247, 1680, 6, "DE"),
    "GNB00": (44.5013, -88.0622, 640, -1, "US"), "HOU00": (29.6847, -95.4107, 50, -1, "US"), "IND00": (39.7601, -86.1639, 715, 0, "US"),
    "JAX00": (30.3240, -81.6373, 15, 0, "US"), "KAN00": (39.0489, -94.4839, 890, -1, "US"), "LAX01": (33.9535, -118.3392, 100, -3, "US"),
    "LAX97": (33.8644, -118.2611, 40, -3, "US"), "LAX99": (34.0141, -118.2879, 200, -3, "US"), "LON00": (51.5560, -0.2795, 150, 5, "GB"),
    "LON01": (51.4560, -0.3415, 30, 5, "GB"), "LON02": (51.6043, -0.0664, 100, 5, "GB"), "MAD01": (40.4531, -3.6883, 2130, 6, "ES"),
    "MEL00": (-37.8200, 144.9834, 30, 14, "AU"), "MEX00": (19.3029, -99.1505, 7350, -1, "MX"), "MIA00": (25.9580, -80.2389, 10, 0, "US"),
    "MIN00": (44.9737, -93.2581, 830, -1, "US"), "MIN01": (44.9737, -93.2575, 830, -1, "US"), "MIN98": (44.9765, -93.2245, 830, -1, "US"),
    "MUN01": (48.2188, 11.6247, 1680, 6, "DE"), "NAS00": (36.1665, -86.7713, 430, -1, "US"), "NOR00": (29.9511, -90.0812, 5, -1, "US"),
    "NYC01": (40.8135, -74.0745, 10, 0, "US"), "OAK00": (37.7516, -122.2005, 10, -3, "US"), "PAR00": (48.9245, 2.3602, 115, 6, "FR"),
    "PHI00": (39.9008, -75.1675, 10, 0, "US"), "PHO00": (33.5276, -112.2626, 1070, -3, "US"), "PIT00": (40.4468, -80.0158, 730, 0, "US"),
    "RIO00": (-22.9122, -43.2302, 20, 1, "BR"), "SAO00": (-23.5453, -46.4742, 2500, 1, "BR"), "SDG00": (32.7831, -117.1196, 60, -3, "US"),
    "SEA00": (47.5952, -122.3316, 10, -3, "US"), "SFO00": (37.7136, -122.3863, 10, -3, "US"), "SFO01": (37.4033, -121.9694, 10, -3, "US"),
    "STL00": (38.6328, -90.1885, 460, -1, "US"), "TAM00": (27.9759, -82.5033, 20, 0, "US"), "VEG00": (36.0909, -115.1833, 2000, -3, "US"),
    "WAS00": (38.9076, -76.8645, 180, 0, "US"),
}
GRASS = {"grass", "dessograss"}


def _tz(stadium_id: str, day: pd.Timestamp) -> float:
    v = STADIUMS.get(stadium_id)
    if v is None:
        return np.nan
    if stadium_id == "PHO00":
        first_sun_nov = pd.Timestamp(day.year, 11, 1) + pd.Timedelta(days=(6 - pd.Timestamp(day.year, 11, 1).weekday()) % 7)
        return -3.0 if day < first_sun_nov else -2.0
    return float(v[3])


def _hav(a, b):
    la1, lo1, la2, lo2 = map(np.radians, [a[0], a[1], b[0], b[1]])
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(h))


def hist(L: pd.DataFrame, keys: list, val, k: float = K_HIST, contrib=None, prior: float = 0.0, return_n=False):
    """For every row of L: the shrunk mean of `val` over the same key's rows in earlier (season, week) slots, among rows
    where `contrib` is true. (sum + k * prior) / (n + k). A row with a missing key gets the prior."""
    d = L[keys + ["season", "week"]].copy()
    miss = np.zeros(len(d), bool)
    for c in keys:
        miss |= d[c].isna().values
        d[c] = d[c].astype(str)
    v = (L[val] if isinstance(val, str) else pd.Series(val, index=L.index)).astype(float)
    if contrib is not None:
        v = v.where(np.asarray(contrib, bool))
    d["_v"] = v.fillna(0.0).values; d["_n"] = v.notna().astype(float).values
    kk = keys + ["season", "week"]
    agg = d.groupby(kk, sort=True)[["_v", "_n"]].sum()
    cs = agg.groupby(level=list(range(len(keys))), sort=False).cumsum() - agg
    cs.columns = ["_cv", "_cn"]
    j = d[kk].join(cs, on=kk)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = ((j._cv + k * prior) / (j._cn + k)).to_numpy(dtype=float, copy=True)
    out[miss] = prior
    if return_n:
        n = j._cn.values.copy(); n[miss] = 0
        return out, n
    return out


def elo_expect(g: pd.DataFrame) -> pd.DataFrame:
    """A plain as-of scoring rating from scores alone (used for residuals where the live model has no walk-forward
    number: 1999-2013 and playoff games). Expected points = league mean of the previous season + own offense rating +
    opponent defense rating +/- 1.3 at home; ratings move 8% of each miss after every week, 60% carried into a new season."""
    g = g[g.home_score.notna()].sort_values(["season", "week", "game_id"])
    off, dfn = {}, {}
    rows = []
    lg_prev = 20.7
    for s, gs in g.groupby("season", sort=True):
        for t in list(off):
            off[t] *= 0.6; dfn[t] *= 0.6
        for w, gw in gs.groupby("week", sort=True):
            upd = []
            for r in gw.itertuples():
                h, a = r.home_team, r.away_team
                hfa = 0.0 if r.location == "Neutral" else 1.3
                eh = lg_prev + off.get(h, 0.0) + dfn.get(a, 0.0) + hfa
                ea = lg_prev + off.get(a, 0.0) + dfn.get(h, 0.0) - hfa
                rows.append((r.game_id, eh, ea))
                upd.append((h, a, r.home_score - eh, r.away_score - ea))
            for h, a, dh, da in upd:
                off[h] = off.get(h, 0.0) + 0.08 * dh; dfn[a] = dfn.get(a, 0.0) + 0.08 * dh
                off[a] = off.get(a, 0.0) + 0.08 * da; dfn[h] = dfn.get(h, 0.0) + 0.08 * da
        lg_prev = float((gs.home_score.sum() + gs.away_score.sum()) / (2 * len(gs)))
    return pd.DataFrame(rows, columns=["game_id", "elo_home", "elo_away"])


def long_table(games: pd.DataFrame, base_pred: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team), regular season and playoffs, 1999 on, with the residuals against the model."""
    g = games.copy()
    g["gd"] = pd.to_datetime(g.gameday)
    g["surface_cls"] = np.where(g.surface.fillna("").str.strip().str.lower().isin(GRASS), "grass", np.where(g.surface.isna(), None, "turf"))
    # a missing surface: the stadium's most common one
    common = g[g.surface_cls.notna()].groupby("stadium_id").surface_cls.agg(lambda s: s.value_counts().index[0])
    g["surface_cls"] = g.surface_cls.fillna(g.stadium_id.map(common))
    el = elo_expect(g)
    g = g.merge(el, on="game_id", how="left")
    bp = base_pred.set_index("game_id")
    use = g.game_id.isin(bp.index) & (g.game_type == "REG")
    g["exp_home"] = np.where(use, g.game_id.map(bp.home_exp), g.elo_home)
    g["exp_away"] = np.where(use, g.game_id.map(bp.away_exp), g.elo_away)
    g["exp_src"] = np.where(use, "model", "elo")
    rows = []
    for side, o in [("home", "away"), ("away", "home")]:
        m = pd.DataFrame({"game_id": g.game_id, "season": g.season, "week": g.week, "game_type": g.game_type, "gd": g.gd, "hour_et": g.hour_et,
                          "slot": g.slot, "weekday": g.weekday, "team": g[f"{side}_team"], "opp": g[f"{o}_team"], "home": float(side == "home"),
                          "neutral": g.neutral.astype(float), "coach": g[f"{side}_coach"], "opp_coach": g[f"{o}_coach"], "qb": g[f"{side}_qb_id"],
                          "opp_qb": g[f"{o}_qb_id"], "referee": g.referee, "stadium_id": g.stadium_id, "surface_cls": g.surface_cls, "roof": g.roof,
                          "div_game": g.div_game.astype(float), "pf": g[f"{side}_score"], "pa": g[f"{o}_score"], "temp": g.temp, "wind": g.wind,
                          "exp_pf": g[f"exp_{side}"], "exp_pa": g[f"exp_{o}"], "exp_src": g.exp_src, "location": g.location})
        rows.append(m)
    L = pd.concat(rows, ignore_index=True)
    for c in ["team", "opp"]:
        L[c] = L[c].replace(FIX)
    L["margin"] = L.pf - L.pa
    L["exp_margin"] = L.exp_pf - L.exp_pa
    L["r_margin"] = L.margin - L.exp_margin
    L["r_pf"] = L.pf - L.exp_pf
    L["r_total"] = (L.pf + L.pa) - (L.exp_pf + L.exp_pa)
    L["model_fav"] = np.sign(L.exp_margin)
    return L.sort_values(["season", "week", "game_id", "home"], ascending=[True, True, True, False]).reset_index(drop=True)


def _by_team_order(L: pd.DataFrame) -> pd.DataFrame:
    return L.sort_values(["team", "season", "week"])


def build(games: pd.DataFrame, base_pred: pd.DataFrame, fp: pd.DataFrame, log=print) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Returns (team columns keyed game_id+team, game columns keyed game_id, notes)."""
    notes = {}
    L = long_table(games, base_pred)
    L["gd"] = pd.to_datetime(L.gd)
    reg = L.game_type == "REG"
    played = L.pf.notna()
    # ---------- static stadium facts
    L["lat"] = L.stadium_id.map(lambda s: STADIUMS.get(s, (np.nan,) * 5)[0]); L["lon"] = L.stadium_id.map(lambda s: STADIUMS.get(s, (np.nan,) * 5)[1])
    L["elev"] = L.stadium_id.map(lambda s: STADIUMS.get(s, (np.nan,) * 5)[2])
    L["intl"] = L.stadium_id.map(lambda s: float(STADIUMS.get(s, (0, 0, 0, 0, "US"))[4] != "US"))
    L["venue_tz"] = [_tz(s, d) for s, d in zip(L.stadium_id, L.gd)]
    # each team's home stadium in a season: its most common stadium in home (non-neutral) regular-season games
    hh = L[(L.home == 1) & (L.location != "Neutral") & reg]
    home_st = hh.groupby(["season", "team"]).stadium_id.agg(lambda s: s.value_counts().index[0])
    home_surf = hh.groupby(["season", "team"]).surface_cls.agg(lambda s: s.value_counts().index[0])
    home_dome = hh.groupby(["season", "team"]).roof.agg(lambda s: float((s.fillna("outdoors") != "outdoors").mean() > 0.5))
    key = list(zip(L.season, L.team)); okey = list(zip(L.season, L.opp))
    L["home_st"] = [home_st.get(k) for k in key]
    L["home_surf"] = [home_surf.get(k) for k in key]
    L["dome_team"] = [home_dome.get(k, 0.0) for k in key]
    L["opp_dome_team"] = [home_dome.get(k, 0.0) for k in okey]
    L["home_tz"] = [_tz(s, d) if isinstance(s, str) else np.nan for s, d in zip(L.home_st, L.gd)]
    L["opp_home_tz"] = L.set_index(["game_id", "team"]).home_tz.reindex(pd.MultiIndex.from_arrays([L.game_id, L.opp])).values
    L["home_elev"] = L.home_st.map(lambda s: STADIUMS.get(s, (np.nan,) * 5)[2] if isinstance(s, str) else np.nan)
    at_home = (L.home == 1) & (L.location != "Neutral")
    L["miles"] = [0.0 if ah else (_hav(STADIUMS[h][:2], (la, lo)) if isinstance(h, str) and h in STADIUMS and pd.notna(la) else np.nan)
                  for ah, h, la, lo in zip(at_home, L.home_st, L.lat, L.lon)]
    L["miles"] = L.miles.fillna(0.0) / 1000.0
    L["tz_shift"] = np.where(at_home, 0.0, (L.venue_tz - L.home_tz).fillna(0.0))
    L["tz_east"] = L.tz_shift.clip(lower=0); L["tz_west"] = (-L.tz_shift).clip(lower=0)
    # ---------- kickoff
    h_et = L.hour_et.fillna(13)
    L["slot3"] = np.where(h_et >= 18, "night", np.where(h_et >= 15, "late", "early"))
    L["night"] = (h_et >= 18).astype(float)
    L["prime"] = L.slot.isin(["TNF", "SNF", "MNF"]).astype(float)
    for s_ in ["TNF", "SNF", "MNF"]:
        L[s_.lower()] = (L.slot == s_).astype(float)
    L["thu"] = (L.weekday == "Thursday").astype(float); L["sat"] = (L.weekday == "Saturday").astype(float); L["mon"] = (L.weekday == "Monday").astype(float)
    L["slot_late"] = (L.slot3 == "late").astype(float); L["slot_night"] = L.night
    L["thanksgiving"] = ((L.gd.dt.month == 11) & (L.weekday == "Thursday") & L.gd.dt.day.between(22, 28)).astype(float)
    L["christmas"] = ((L.gd.dt.month == 12) & L.gd.dt.day.between(24, 26)).astype(float)
    L["sat_late"] = ((L.weekday == "Saturday") & (L.week >= 15) & reg).astype(float)
    L["bc_early_west"] = ((L.home == 0) & (L.home_tz <= -2) & (h_et <= 13)).astype(float)
    L["bc_late_east"] = ((L.home_tz == 0) & (h_et >= 20) & (L.opp_home_tz <= -2)).astype(float)
    L["bc_night_edge"] = np.where(h_et >= 18, (L.opp_home_tz - L.home_tz).fillna(0.0), 0.0)
    # ---------- surface and roof
    L["turf"] = (L.surface_cls == "turf").astype(float)
    L["roof_open"] = (L.roof == "open").astype(float); L["roof_closed"] = (L.roof == "closed").astype(float)
    outdoor_game = L.roof.fillna("outdoors").isin(["outdoors", "open"])
    L["surf_mismatch"] = ((~at_home) & L.home_surf.notna() & (L.home_surf != L.surface_cls)).astype(float)
    L["dome_team_out"] = ((~at_home) & (L.dome_team == 1) & outdoor_game).astype(float)
    L["out_team_in_dome"] = ((~at_home) & (L.dome_team == 0) & ~outdoor_game).astype(float)
    L["altitude"] = ((L.elev >= 4000) & (L.home_elev < 4000)).astype(float)
    # ---------- team schedule order: road streak, two-week miles, previous and next game slot
    T = L.sort_values(["team", "season", "week"]).copy()
    grp = T.groupby(["team", "season"])
    away = (T.home == 0) | (T.location == "Neutral")
    streak = []
    for (_, _), x in T.assign(aw=away.values).groupby(["team", "season"], sort=False):
        c = 0; out = []
        for a in x.aw.values:
            c = c + 1 if a else 0; out.append(max(c - 1, 0))
        streak += out
    T["road_streak"] = streak
    T["miles_prev"] = grp.miles.shift(1).fillna(0.0)
    T["miles_2wk"] = T.miles + T.miles_prev
    T["prev_slot"] = grp.slot.shift(1)
    T["after_prime"] = T.prev_slot.isin(["SNF", "MNF"]).astype(float)
    T["next_prime"] = grp.prime.shift(-1).fillna(0.0)
    for c in ["road_streak", "miles_2wk", "after_prime", "next_prime"]:
        L[c] = T[c].reindex(L.index)
    # ---------- coaches: tenure, experience, former teams; QB former teams
    cs = L[reg].groupby(["coach", "team"]).season.apply(lambda s: sorted(set(s))).to_dict()
    L["coach_tenure"] = [sum(1 for y in cs.get((c, t), []) if y < s) for c, t, s in zip(L.coach, L.team, L.season)]
    L["first_year_coach"] = (L.coach_tenure == 0).astype(float)
    L["coach_tenure_l"] = np.log1p(L.coach_tenure)
    _, n_games = hist(L, ["coach"], np.ones(len(L)), k=0.0, contrib=reg & played, return_n=True)
    L["coach_exp_l"] = np.log1p(n_games)
    past_teams = L[reg].groupby("coach").apply(lambda x: list(zip(x.season, x.team)), include_groups=False).to_dict()
    L["coach_vs_former"] = [float(any(t2 == o and y < s for y, t2 in past_teams.get(c, []))) for c, o, s in zip(L.coach, L.opp, L.season)]
    qb_teams = L[reg & L.qb.notna()].groupby("qb").apply(lambda x: list(zip(x.season, x.team)), include_groups=False).to_dict()
    L["qb_vs_former"] = [float(any(t2 == o and y < s for y, t2 in qb_teams.get(q, []))) if isinstance(q, str) else 0.0 for q, o, s in zip(L.qb, L.opp, L.season)]
    # ---------- residual histories (margin residual unless noted), K = 20 games
    P = played
    L["cvc"] = hist(L, ["coach", "opp_coach"], "r_margin", contrib=P)
    L["coach_vs_team"] = hist(L, ["coach", "opp"], "r_margin", contrib=P)
    L["team_vs_team"] = hist(L, ["team", "opp"], "r_margin", contrib=P)
    L["qb_vs_team"] = hist(L, ["qb", "opp"], "r_pf", contrib=P)
    L["coach_career"] = hist(L, ["coach"], "r_margin", contrib=P)
    L["coach_at_stadium"] = hist(L, ["coach", "stadium_id"], "r_margin", contrib=P)
    L["team_at_stadium"] = hist(L, ["team", "stadium_id"], "r_margin", contrib=P)
    L["road_at_stadium"] = hist(L, ["team", "stadium_id"], "r_margin", contrib=P & ~at_home) * (~at_home)
    L["team_on_surface"] = hist(L, ["team", "surface_cls"], "r_margin", contrib=P)
    L["team_prime_r"] = hist(L, ["team"], "r_margin", contrib=P & (L.prime == 1)) * L.prime
    L["team_slot_r"] = hist(L, ["team", "slot3"], "r_margin", contrib=P)
    L["coach_prime_r"] = hist(L, ["coach"], "r_margin", contrib=P & (L.prime == 1)) * L.prime
    L["coach_slot_r"] = hist(L, ["coach", "slot3"], "r_margin", contrib=P)
    L["qb_prime_r"] = hist(L, ["qb"], "r_pf", contrib=P & (L.prime == 1)) * L.prime
    L["qb_slot_r"] = hist(L, ["qb", "slot3"], "r_pf", contrib=P)
    # rematch: this season's earlier meeting (regular season), its margin residual from this team's view
    first = L[reg & P].sort_values("week").groupby(["season", "team", "opp"]).agg(w1=("week", "first"), r1=("r_margin", "first"))
    j = L[["season", "team", "opp", "week"]].join(first, on=["season", "team", "opp"])
    L["rematch_r"] = np.where(reg & (j.w1 < j.week), j.r1, 0.0)
    # referees
    sign = np.where(L.home == 1, 1.0, -1.0)
    L["ref_team_r"] = hist(L, ["referee", "team"], "r_margin", contrib=P)
    L["ref_team_pts"] = hist(L, ["referee", "team"], "r_pf", contrib=P)
    L["ref_team_venue"] = hist(L, ["referee", "team", "home"], "r_margin", contrib=P)
    L["ref_home_r"] = hist(L, ["referee"], "r_margin", contrib=P & (L.home == 1) & (L.location != "Neutral")) * sign * (L.location != "Neutral")
    fav_r = np.where(L.model_fav > 0, L.r_margin, np.where(L.model_fav < 0, -L.r_margin, np.nan))   # the model favourite's residual (by the model's own number)
    L["ref_fav_r"] = hist(L, ["referee"], fav_r, contrib=P & (L.home == 1)) * L.model_fav.fillna(0)
    L["ref_div_home"] = hist(L, ["referee"], "r_margin", contrib=P & (L.home == 1) & (L.div_game == 1)) * sign * L.div_game
    # ---------- standings as of the week: eliminated / clinched (ties and tiebreakers ignored; strict bounds)
    # eliminated: at least `spots` other conference teams already have more wins than this team's most possible, and a
    # division rival too (so neither a wildcard nor the division is reachable). clinched: at most `wildcards` other
    # conference teams can still reach this team's current wins (so even with every other division won by a team below
    # it, it keeps a wildcard). From Week 10; the final-week flag marks a clinched team in the last regular-season week.
    conf = _conferences(); divs = {t: _division(t) for t in conf}
    Rg = L[reg]
    ng = Rg.groupby(["season", "team"]).size()
    clin, elim, fin = np.zeros(len(L)), np.zeros(len(L)), np.zeros(len(L))
    pos = {i: n for n, i in enumerate(L.index)}
    for s in sorted(Rg.season.unique()):
        x = Rg[Rg.season == s]; spots = 6 if s < 2020 else 7; wild = spots - 4; last_wk = x.week.max()
        teams = x.team.unique()
        for w in sorted(x.week.unique()):
            if w < 10:
                continue
            done = x[(x.week < w) & x.pf.notna()]
            W = {t: 0.0 for t in teams}
            for t_, pf_, pa_ in zip(done.team, done.pf, done.pa):
                W[t_] += 1.0 if pf_ > pa_ else (0.5 if pf_ == pa_ else 0.0)
            gp = done.groupby("team").size()
            MX = {t: W[t] + ng.get((s, t), 16) - gp.get(t, 0) for t in teams}
            for i, t in zip(x.index[x.week == w], x.team[x.week == w]):
                c = conf.get(t)
                others = [u for u in teams if conf.get(u) == c and u != t]
                if not others:
                    continue
                if sum(1 for u in others if MX[u] >= W[t]) <= wild:
                    clin[pos[i]] = 1.0; fin[pos[i]] = float(w == last_wk)
                above = sum(1 for u in others if W[u] > MX[t])
                rival_above = any(W[u] > MX[t] for u in others if divs.get(u) == divs.get(t))
                if above >= spots and rival_above:
                    elim[pos[i]] = 1.0
    L["clinched"], L["eliminated"], L["clinched_final"] = clin, elim, fin
    log("standings done")
    return L, notes


_CONF = {"AFC": {"BUF": "E", "MIA": "E", "NE": "E", "NYJ": "E", "BAL": "N", "CIN": "N", "CLE": "N", "PIT": "N", "HOU": "S", "IND": "S", "JAX": "S", "TEN": "S",
                 "DEN": "W", "KC": "W", "LV": "W", "LAC": "W"},
         "NFC": {"DAL": "E", "NYG": "E", "PHI": "E", "WAS": "E", "CHI": "N", "DET": "N", "GB": "N", "MIN": "N", "ATL": "S", "CAR": "S", "NO": "S", "TB": "S",
                 "ARI": "W", "LA": "W", "SF": "W", "SEA": "W"}}


def _conferences():
    return {t: c for c, d in _CONF.items() for t in d}


def _division(t):
    for c, d in _CONF.items():
        if t in d:
            return c + d[t]
    return None


def _roll_prior(L: pd.DataFrame, col: str, n: int = 16, shrink_to=None, k: float = 0.0) -> np.ndarray:
    """Each team's mean of `col` over its previous n games (any season), before this week; NaN-safe."""
    T = L[["team", "season", "week", col]].sort_values(["team", "season", "week"])
    r = T.groupby("team")[col].transform(lambda s: s.shift(1).rolling(n, min_periods=1).mean())
    return r.reindex(L.index).values


def pbp_team_game(seasons=range(2012, 2027)) -> pd.DataFrame:
    """Per (game, offense): shotgun and no-huddle rates on passes and runs, and 4th-down decisions in go-for-it range
    (4th and 3 or less from the opponent's 60 in: a pass or run counts as going, a punt or field goal as not)."""
    import pyarrow.parquet as pq
    out = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        p = pq.read_table(f, columns=["game_id", "posteam", "play_type", "shotgun", "no_huddle", "down", "ydstogo", "yardline_100", "qb_hit", "qb_dropback", "sack"]).to_pandas()
        p = p[p.posteam.notna()].copy(); p["posteam"] = p.posteam.replace(FIX)
        sc = p[p.play_type.isin(["pass", "run"])]
        a = sc.groupby(["game_id", "posteam"]).agg(shotgun=("shotgun", "mean"), no_huddle=("no_huddle", "mean"),
                                                  hits=("qb_hit", "sum"), dropbacks=("qb_dropback", "sum"), sacks=("sack", "sum"))
        g4 = p[(p.down == 4) & (p.ydstogo <= 3) & (p.yardline_100 <= 60) & p.play_type.isin(["pass", "run", "punt", "field_goal"])]
        b = g4.assign(go=g4.play_type.isin(["pass", "run"]).astype(float)).groupby(["game_id", "posteam"]).agg(go4=("go", "sum"), opp4=("go", "size"))
        out.append(a.join(b, how="left").reset_index())
    d = pd.concat(out, ignore_index=True).rename(columns={"posteam": "team"})
    d[["go4", "opp4"]] = d[["go4", "opp4"]].fillna(0.0)
    return d


def injury_groups(games: pd.DataFrame, seasons=range(2012, 2027)) -> pd.DataFrame:
    """Per (game, team), the same reading trends.injury_table makes (last game's 50%+ snap players who are Out or Doubtful
    on the final report, or on a not-available roster status), split by position: DB and front-seven starters out, and
    whether both of last game's top two receivers (by snaps) are out."""
    from nflmodel.players import load_injuries, load_rosters, NOT_AVAILABLE
    from nflmodel.ids import pfr_ids
    from nflmodel.trends import _norm, long_games
    snaps = pd.concat([pd.read_parquet(RAW / "snap_counts" / f"snap_counts_{s}.parquet") for s in seasons if (RAW / "snap_counts" / f"snap_counts_{s}.parquet").exists()], ignore_index=True)
    snaps["team"] = snaps.team.replace(FIX)
    inj = load_injuries(seasons); inj["team"] = inj.team.replace(FIX)
    nmap = {}
    for s_ in seasons:
        f_ = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if f_.exists():
            r_ = pd.read_parquet(f_, columns=["season", "team", "gsis_id", "full_name"]).dropna(subset=["gsis_id"])
            r_["team"] = r_.team.replace(FIX)
            nmap.update({(t_, int(se_), k_): g_ for t_, se_, k_, g_ in zip(r_.team, r_.season, _norm(r_.full_name), r_.gsis_id)})
    pmap = pfr_ids()
    inj["key"] = inj.gsis_id
    snaps["key"] = snaps.pfr_player_id.map(pmap)
    miss = snaps.key.isna()
    snaps.loc[miss, "key"] = [nmap.get((t_, int(se_), k_)) for t_, se_, k_ in zip(snaps.team[miss], snaps.season[miss], _norm(snaps.player[miss]))]
    inj = inj[inj.report_status.isin(["Out", "Doubtful"])]
    ros = load_rosters(seasons); ros = ros[ros.status.isin(NOT_AVAILABLE)].copy()
    ros_out = {k: set(g.gsis_id) for k, g in ros.groupby(["season", "week", "team"])}
    inj_out = {k: set(g.key) for k, g in inj.groupby(["season", "week", "team"])}
    pos = snaps.position.fillna("").str.split("/").str[0]
    snaps["grp"] = np.select([pos.isin(["CB", "S", "FS", "SS", "DB"]), pos.isin(["DE", "DT", "NT", "DL", "LB", "OLB", "ILB", "MLB"]), pos.isin(["WR"])], ["DB", "FRONT", "WR"], "")
    prev = {k: g for k, g in snaps.sort_values(["season", "week"]).groupby(["season", "team"])}
    rows = []
    long = long_games(games); long = long[long.season.isin(seasons)]
    for r in long.itertuples():
        g = prev.get((r.season, r.team))
        if g is None:
            rows.append((r.game_id, r.team, np.nan, np.nan, np.nan)); continue
        before = g[g.week < r.week]
        if len(before) == 0:
            g2 = prev.get((r.season - 1, r.team))
            before = g2[g2.week == g2.week.max()] if g2 is not None else before
        else:
            before = before[before.week == before.week.max()]
        out = inj_out.get((r.season, r.week, r.team), set()) | ros_out.get((r.season, r.week, r.team), set())
        db = before[(before.grp == "DB") & (before.defense_pct >= 0.5)]; fr = before[(before.grp == "FRONT") & (before.defense_pct >= 0.5)]
        wr = before[before.grp == "WR"].sort_values("offense_pct", ascending=False).head(2)
        rows.append((r.game_id, r.team, float(db.key.isin(out).sum()), float(fr.key.isin(out).sum()), float(len(wr) == 2 and wr.key.isin(out).all())))
    return pd.DataFrame(rows, columns=["game_id", "team", "db_out", "front_out", "wr12_out"])


def participation_prev(seasons=range(2016, 2026)) -> pd.DataFrame:
    """Per (season, team), from the participation file of that season (published after it ends, so it is only ever
    used for the NEXT season): the defense's man-coverage rate on passes, blitz rate (5+ rushers) on dropbacks and
    light-box rate (6 or fewer in the box) on runs, and the offense's EPA per pass against man and zone, per dropback
    against a blitz and not, and per run against a light and a heavy box."""
    from nflmodel.scheme import load_plays
    d = load_plays(list(seasons))
    d = d[d.play_type.isin(["pass", "run"])]
    ps = d.pass_play; db = d.dropback; run = d.play_type.eq("run")
    rows = []
    for (s, t), x in d.groupby(["season", "defteam"]):
        xs = x[x.pass_play & x.cov_known]; xb = x[x.dropback & x.blitz.notna()]; xr = x[(x.play_type == "run") & x.box.notna()]
        rows.append({"season": s, "team": t, "side": "def", "man_rate": xs.man.mean() if len(xs) >= 100 else np.nan,
                     "blitz_rate": xb.blitz.mean() if len(xb) >= 100 else np.nan, "light_rate": (xr.box <= 6).mean() if len(xr) >= 100 else np.nan})
    D = pd.DataFrame(rows)
    rows = []
    for (s, t), x in d.groupby(["season", "posteam"]):
        def e(m, n=40):
            y = x[m]; return y.epa.mean() if len(y) >= n else np.nan
        rows.append({"season": s, "team": t, "epa_pass": e(x.pass_play), "epa_man": e(x.pass_play & x.man), "epa_zone": e(x.pass_play & x.zone),
                     "epa_db": e(x.dropback), "epa_blitz": e(x.dropback & (x.blitz == 1)), "epa_noblitz": e(x.dropback & (x.blitz == 0)),
                     "epa_run": e(x.play_type == "run"), "epa_light": e((x.play_type == "run") & (x.box <= 6)), "epa_heavy": e((x.play_type == "run") & (x.box >= 7))})
    O = pd.DataFrame(rows)
    return D.drop(columns="side").merge(O, on=["season", "team"], how="outer")
