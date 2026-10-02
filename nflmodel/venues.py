"""Where each game is played: coordinates, time zone, roof and the nearest NWS MOS airport (2 Oct 2026, data audit).

nflverse's schedule names the stadium by id (`stadium_id`). Most games are at the home team's own stadium, so the team's
coordinates stand in; this module adds the stadiums a team has left (Oakland, San Diego, Carson, the LA Coliseum, TCF
Bank Stadium, Candlestick) and every stadium abroad, and corrects games the schedule lists at the wrong place:

  2025: Sao Paulo, Dublin, London (three), Berlin and Madrid were listed at the home team's US stadium (SoFi as a dome,
        Lucas Oil as closed, TIAA Bank, Hard Rock, Acrisure, FirstEnergy, MetLife), so the weather and the forecast
        history read Jacksonville's or Miami's airport for a game in London or Madrid.
  2026: Melbourne, Paris and Munich (all open air) were marked dome, so those games got no weather at all; Philadelphia
        at Jacksonville in London was listed as a home game at Jacksonville's id.

`fix_venues` applies GAME_VENUE in build.build_games; `site` / `sites` give every reader (weather.run,
weather_archive, forecast_archive, forecast_history, wind_live) the same place for a game; `venue_problems` is the data
check (data_checks.py): a neutral-site game listed at the home team's own stadium, or a stadium abroad resolved to a US
site, fails.
"""
from __future__ import annotations
import numpy as np, pandas as pd

# home stadium coordinates (lat, lon) of every current team
STADIUM = {"ARI": (33.5276, -112.2626), "ATL": (33.7554, -84.4010), "BAL": (39.2780, -76.6227), "BUF": (42.7738, -78.7870),
           "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167), "CIN": (39.0955, -84.5161), "CLE": (41.5061, -81.6995),
           "DAL": (32.7473, -97.0945), "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
           "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3240, -81.6373), "KC": (39.0489, -94.4839),
           "LV": (36.0909, -115.1833), "LAC": (33.9535, -118.3392), "LA": (33.9535, -118.3392), "MIA": (25.9580, -80.2389),
           "MIN": (44.9736, -93.2575), "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8135, -74.0745),
           "NYJ": (40.8135, -74.0745), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158), "SF": (37.4032, -121.9698),
           "SEA": (47.5952, -122.3316), "TB": (27.9759, -82.5033), "TEN": (36.1665, -86.7713), "WAS": (38.9076, -76.8645)}
# city coordinates the older readers matched stadium names against (trends.situation_extras' US fallback); site() is the source
INTL = {"London": (51.5560, -0.2795), "Munich": (48.2188, 11.6247), "Frankfurt": (50.0686, 8.6455), "Mexico City": (19.3029, -99.1505),
        "Sao Paulo": (-23.5453, -46.4742), "Madrid": (40.4361, -3.5886), "Dublin": (53.3607, -6.2512), "Melbourne": (-37.8200, 144.9834)}
# the stadium's nearest MOS airport (checked against the airport list when the forecast history was built)
STATION = {"BUF": "KBUF", "GB": "KGRB", "CHI": "KMDW", "NE": "KOWD", "NYG": "KTEB", "NYJ": "KTEB", "PHI": "KPHL", "PIT": "KPIT",
           "CLE": "KBKL", "BAL": "KBWI", "WAS": "KDCA", "CIN": "KLUK", "KC": "KMCI", "DEN": "KDEN", "SEA": "KBFI", "SF": "KSJC",
           "TEN": "KBNA", "JAX": "KJAX", "MIA": "KMIA", "TB": "KTPA", "CAR": "KCLT", "ARI": "KPHX", "ATL": "KATL", "NO": "KMSY",
           "IND": "KIND", "DET": "KDTW", "MIN": "KMSP", "HOU": "KHOU", "DAL": "KDFW", "LAC": "KSNA", "LA": "KCQT"}
TEAM_TZ = {"ARI": "America/Phoenix", "DEN": "America/Denver", "KC": "America/Chicago", "DAL": "America/Chicago", "HOU": "America/Chicago",
           "CHI": "America/Chicago", "GB": "America/Chicago", "MIN": "America/Chicago", "NO": "America/Chicago", "TEN": "America/Chicago",
           "LV": "America/Los_Angeles", "LAC": "America/Los_Angeles", "LA": "America/Los_Angeles", "SF": "America/Los_Angeles",
           "SEA": "America/Los_Angeles"}
# nflverse stadium ids and the teams whose home they are (modern codes; LA and LAC share SoFi, the Giants and Jets MetLife)
HOME_IDS = {"ATL00": ("ATL",), "ATL97": ("ATL",), "BAL00": ("BAL",), "BOS00": ("NE",), "BUF00": ("BUF",), "CAR00": ("CAR",),
            "CHI98": ("CHI",), "CIN00": ("CIN",), "CLE00": ("CLE",), "DAL00": ("DAL",), "DEN00": ("DEN",), "DET00": ("DET",),
            "GNB00": ("GB",), "HOU00": ("HOU",), "IND00": ("IND",), "JAX00": ("JAX",), "KAN00": ("KC",), "LAX01": ("LA", "LAC"),
            "MIA00": ("MIA",), "MIN00": ("MIN",), "MIN01": ("MIN",), "NAS00": ("TEN",), "NOR00": ("NO",), "NYC01": ("NYG", "NYJ"),
            "PHI00": ("PHI",), "PHO00": ("ARI",), "PIT00": ("PIT",), "SEA00": ("SEA",), "SFO01": ("SF",), "TAM00": ("TB",),
            "VEG00": ("LV",), "WAS00": ("WAS",), "STL00": ("LA",), "OAK00": ("LV",), "SDG00": ("LAC",), "LAX97": ("LAC",),
            "LAX99": ("LA",), "MIN98": ("MIN",), "SFO00": ("SF",)}
# stadiums that are not a current team's home: key (the archive's "site"), coordinates, time zone, MOS airport (None
# abroad: no US forecast), abroad, and words its name carries in the schedule
VENUE = {
    "OAK00": ("Oakland", 37.7516, -122.2005, "America/Los_Angeles", "KOAK", False, ("Coliseum",)),
    "SDG00": ("San Diego", 32.7831, -117.1196, "America/Los_Angeles", "KSAN", False, ("Qualcomm",)),
    "LAX97": ("Carson", 33.8644, -118.2611, "America/Los_Angeles", "KTOA", False, ("StubHub",)),
    "LAX99": ("LA Coliseum", 34.0141, -118.2879, "America/Los_Angeles", "KCQT", False, ("Memorial Coliseum",)),
    "MIN98": ("TCF Bank", 44.9765, -93.2246, "America/Chicago", "KMSP", False, ("TCF",)),
    "SFO00": ("Candlestick", 37.7136, -122.3862, "America/Los_Angeles", "KSFO", False, ("Candlestick",)),
    "LON00": ("London Wembley", 51.5560, -0.2795, "Europe/London", None, True, ("Wembley",)),
    "LON01": ("London Twickenham", 51.4560, -0.3415, "Europe/London", None, True, ("Twickenham",)),
    "LON02": ("London Tottenham", 51.6043, -0.0664, "Europe/London", None, True, ("Tottenham",)),
    "MEX00": ("Mexico City", 19.3029, -99.1505, "America/Mexico_City", None, True, ("Azteca", "Banorte")),
    "GER00": ("Munich", 48.2188, 11.6247, "Europe/Berlin", None, True, ("Allianz", "Bayern")),
    "MUN01": ("Munich", 48.2188, 11.6247, "Europe/Berlin", None, True, ("Allianz", "Bayern")),
    "FRA00": ("Frankfurt", 50.0686, 8.6455, "Europe/Berlin", None, True, ("Deutsche Bank Park", "Waldstadion")),
    "BER00": ("Berlin", 52.5147, 13.2395, "Europe/Berlin", None, True, ("Olympiastadion",)),
    "SAO00": ("Sao Paulo", -23.5453, -46.4742, "America/Sao_Paulo", None, True, ("Corinthians",)),
    "RIO00": ("Rio de Janeiro", -22.9122, -43.2302, "America/Sao_Paulo", None, True, ("Maracana",)),
    "MAD01": ("Madrid", 40.4531, -3.6883, "Europe/Madrid", None, True, ("Bernabeu",)),
    "DUB00": ("Dublin", 53.3607, -6.2512, "Europe/Dublin", None, True, ("Croke",)),
    "PAR00": ("Paris", 48.9245, 2.3601, "Europe/Paris", None, True, ("Stade de France",)),
    "MEL00": ("Melbourne", -37.8200, 144.9834, "Australia/Melbourne", None, True, ("Melbourne",)),
}
ABROAD_WORDS = tuple(w for v in VENUE.values() if v[5] for w in v[6])
ROOFED_ABROAD = {"MAD01"}   # the Bernabeu has a retractable roof; every other stadium abroad above is open air
# games the schedule lists at the wrong place: game_id -> (stadium_id, stadium, roof; None keeps the schedule's roof)
GAME_VENUE = {
    "2025_01_KC_LAC": ("SAO00", "Arena Corinthians", "outdoors"),        # listed: SoFi Stadium, dome
    "2025_04_MIN_PIT": ("DUB00", "Croke Park", "outdoors"),              # listed: Acrisure Stadium
    "2025_05_MIN_CLE": ("LON02", "Tottenham Hotspur Stadium", "outdoors"),  # listed: FirstEnergy Stadium
    "2025_06_DEN_NYJ": ("LON02", "Tottenham Hotspur Stadium", "outdoors"),  # listed: MetLife Stadium
    "2025_07_LA_JAX": ("LON00", "Wembley Stadium", "outdoors"),          # listed: TIAA Bank Stadium
    "2025_10_ATL_IND": ("BER00", "Olympiastadion", "outdoors"),          # listed: Lucas Oil Stadium, closed
    "2025_11_WAS_MIA": ("MAD01", "Bernabeu", None),                      # listed: Hard Rock Stadium
    "2026_01_SF_LA": ("MEL00", "Melbourne Cricket Ground", "outdoors"),  # listed: dome
    "2026_05_PHI_JAX": ("LON02", "Tottenham Hotspur Stadium", None),     # listed: a Jacksonville home game at JAX00
    "2026_07_PIT_NO": ("PAR00", "Stade de France", "outdoors"),          # listed: dome
    "2026_10_NE_DET": ("MUN01", "FC Bayern Munich Stadium", "outdoors"),  # listed: dome
}


def fix_venues(g: pd.DataFrame) -> pd.DataFrame:
    """The schedule with GAME_VENUE applied: stadium id and name, neutral site, roof, and the dome / neutral flags."""
    g = g.copy()
    for gid, (sid, name, roof) in GAME_VENUE.items():
        m = g.game_id == gid
        if not m.any():
            continue
        g.loc[m, "stadium_id"] = sid; g.loc[m, "stadium"] = name; g.loc[m, "location"] = "Neutral"
        if roof is not None:
            g.loc[m, "roof"] = roof
    if "dome" in g.columns:
        g["dome"] = g.roof.isin(["dome", "closed"])
    if "neutral" in g.columns:
        g["neutral"] = g.location.eq("Neutral")
    return g


def site(stadium_id, home_team) -> dict:
    """The place a game is played: key, lat, lon, tz, MOS station (None abroad or unknown), abroad."""
    if isinstance(stadium_id, str) and stadium_id in VENUE:
        k, lat, lon, tz, st, ab, _ = VENUE[stadium_id]
        return {"site": k, "lat": lat, "lon": lon, "tz": tz, "station": st, "abroad": ab}
    own = HOME_IDS.get(stadium_id, (home_team,)) if isinstance(stadium_id, str) else (home_team,)
    owner = home_team if home_team in own else own[0]   # a shared stadium (SoFi, MetLife) keeps the home team's key
    owner = owner if owner in STADIUM else home_team
    ll = STADIUM.get(owner, (None, None))
    return {"site": owner, "lat": ll[0], "lon": ll[1], "tz": TEAM_TZ.get(owner, "America/New_York"), "station": STATION.get(owner), "abroad": False}


def sites(g: pd.DataFrame) -> pd.DataFrame:
    """site() for every row of a games table, on the table's index."""
    sid = g["stadium_id"] if "stadium_id" in g.columns else pd.Series(None, index=g.index)
    return pd.DataFrame([site(s, t) for s, t in zip(sid, g.home_team)], index=g.index)


def venue_problems(g: pd.DataFrame) -> list[str]:
    """Games whose place is wrong: a neutral-site game (not a Super Bowl) listed at the home team's own stadium, a
    stadium whose name is a venue abroad resolved to a US site, or an open-air stadium abroad marked dome or closed."""
    out = []
    sid = g["stadium_id"] if "stadium_id" in g.columns else pd.Series(None, index=g.index)
    st = sites(g)
    for i, gid, loc, gt, s, home, name, roof in zip(g.index, g.game_id, g.location, g.game_type, sid, g.home_team, g.stadium.fillna(""), g.roof):
        if loc == "Neutral" and gt != "SB" and home in HOME_IDS.get(s, ()) and s not in VENUE:
            out.append(gid)
        elif any(w.lower() in name.lower() for w in ABROAD_WORDS) and not st.at[i, "abroad"]:
            out.append(gid)
        elif st.at[i, "abroad"] and s not in ROOFED_ABROAD and roof in ("dome", "closed"):
            out.append(gid)
    return out
