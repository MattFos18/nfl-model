"""Leverage-weighted team EPA ratings (29 Sep 2026). Does weighting each play by its leverage (win probability near
50%) in the team ratings (ratings.STATS) price games better than counting every play the same?

Variants, each a replacement team_games frame handed to ratings.build_features (pf never changes):
  base  the live frame (control)
  ng    epa_play, pass_epa, rush_epa, success, plays replaced by build.py's `_ng` columns (wp < 0.10 or > 0.90 dropped)
  lev   recomputed from the raw play-by-play with the smooth weight w = 1 - |2*wp - 1|**2 = 4*wp*(1-wp); weighted means, plays = weight sum
  ng2   recomputed, weight 1 if 0.05 <= wp <= 0.95 else 0
  half  recomputed, weight 1 if 0.10 <= wp <= 0.90 else 0.5
Play filter and team renames as build.team_game_stats (posteam set, play_type pass/run, epa set, TEAM_FIX).

Scored with model.walk_forward (weekly refit) on 2015-18 (untouched, report only), 2019-22 (tuning), 2023-25 (held out)
and the 4+ record on 2019-2025 combined. Adoption rule (reports/leverage_ratings.md, written before any result):
margin MAE and team-points MAE both strictly lower than base on all three windows.

Usage: python experiments/leverage_ratings.py <variant>     runs one variant, writes a json to the scratch dir
       python experiments/leverage_ratings.py collect       writes reports/leverage_ratings.csv and the md table"""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M, build as BU
from nflmodel.model import OUT
from experiments.common import score

SCRATCH = Path("/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/lev")
VARIANTS = ["base", "ng", "lev", "ng2", "half"]
WINDOWS = {"2015-18": range(2015, 2019), "2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}
COLS = ["epa_play", "pass_epa", "rush_epa", "success", "plays"]   # ratings.STATS minus pf


def load_plays() -> pd.DataFrame:
    fr = []
    for s in range(2012, 2027):
        f = BU.RAW / "pbp" / f"play_by_play_{s}.parquet"
        if f.exists():
            fr.append(pd.read_parquet(f, columns=["game_id", "posteam", "play_type", "epa", "success", "pass", "rush", "qb_scramble", "wp"]))
    p = pd.concat(fr, ignore_index=True)
    p["posteam"] = p.posteam.replace(BU.TEAM_FIX)
    d = p[p.posteam.notna() & p.play_type.isin(["pass", "run"]) & p.epa.notna()].copy()
    d["is_pass"] = d["pass"] == 1
    d["is_rush"] = (d.rush == 1) & (d.qb_scramble != 1)
    d["wp"] = d.wp.fillna(0.5)   # no missing wp in 2012-2026; a missing one would count as a coin-flip play
    return d


def weights(d: pd.DataFrame, kind: str) -> np.ndarray:
    wp = d.wp.values.astype(float)
    garbage = (wp < 0.10) | (wp > 0.90)
    if kind == "lev":
        return 1.0 - np.abs(2 * wp - 1) ** 2
    if kind == "ng2":
        return np.where((wp < 0.05) | (wp > 0.95), 0.0, 1.0)
    if kind == "half":
        return np.where(garbage, 0.5, 1.0)
    if kind == "ng_check":   # replicates build.py's _ng columns, used only to verify the recomputation
        return np.where(garbage, 0.0, 1.0)
    raise ValueError(kind)


def weighted_stats(d: pd.DataFrame, w: np.ndarray) -> pd.DataFrame:
    """Per (game_id, team): w-weighted mean EPA per play, pass EPA, rush EPA, success; plays = weight sum."""
    x = d[["game_id", "posteam", "epa", "success", "is_pass", "is_rush"]].copy()
    x["w"] = w
    x["we"] = x.w * x.epa
    x["ws"] = x.w * x.success
    x["wp_"] = np.where(x.is_pass, x.w, 0.0); x["wpe"] = x.wp_ * x.epa
    x["wr_"] = np.where(x.is_rush, x.w, 0.0); x["wre"] = x.wr_ * x.epa
    g = x.groupby(["game_id", "posteam"])[["w", "we", "ws", "wp_", "wpe", "wr_", "wre"]].sum()
    out = pd.DataFrame({"plays": g.w, "epa_play": g.we / g.w.replace(0, np.nan), "success": g.ws / g.w.replace(0, np.nan),
                        "pass_epa": g.wpe / g.wp_.replace(0, np.nan), "rush_epa": g.wre / g.wr_.replace(0, np.nan)})
    return out.reset_index().rename(columns={"posteam": "team"})


def variant_frame(tg: pd.DataFrame, kind: str, plays: pd.DataFrame | None) -> pd.DataFrame:
    t = tg.copy()
    if kind == "base":
        return t
    if kind == "ng":
        for c in COLS:
            t[c] = t[f"{c}_ng"]
        return t
    st = weighted_stats(plays, weights(plays, kind))
    t = t.merge(st, on=["game_id", "team"], how="left", suffixes=("", "_v"))
    missing = t.plays_v.isna()   # a played game the raw pbp files do not carry yet (2026 week 3 on 29 Sep 2026; outside every window) keeps its base values
    for c in COLS:
        t[c] = t[f"{c}_v"].where(~missing, t[c])
    return t[tg.columns]


def check_ng(tg: pd.DataFrame, plays: pd.DataFrame) -> None:
    """The recomputation with weight 0/1 at the 0.10/0.90 cut must reproduce build.py's _ng columns."""
    st = weighted_stats(plays, weights(plays, "ng_check"))
    m = tg[["game_id", "team"] + [f"{c}_ng" for c in COLS]].merge(st, on=["game_id", "team"])
    for c in COLS:
        diff = (m[c] - m[f"{c}_ng"]).abs().max()
        print(f"  check ng recompute {c}: max abs diff {diff:.2e}", flush=True)
        assert diff < 1e-6, c


def run(kind: str) -> dict:
    t0 = time.time()
    M.TREES_CACHE = SCRATCH / f"trees_cache_{kind}.parquet"; M._TC = {"df": None, "used": set(), "new": []}
    tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
    plays = None
    if kind not in ("base", "ng"):
        plays = load_plays(); print(f"[{kind}] plays loaded {len(plays)} in {time.time() - t0:.0f}s", flush=True)
        if kind == "lev":
            check_ng(tg, plays)
    tgv = variant_frame(tg, kind, plays)
    played = tgv[tgv.pf.notna()]
    print(f"[{kind}] frame ready in {time.time() - t0:.0f}s; mean plays {played.plays.mean():.1f}, mean epa_play {played.epa_play.mean():.4f}, "
          f"sd epa_play {played.epa_play.std():.4f}, pass_epa NaN {int(played.pass_epa.isna().sum())}, rush_epa NaN {int(played.rush_epa.isna().sum())}", flush=True)
    t1 = time.time()
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tgv, games=games, qb=qb))
    print(f"[{kind}] features built in {time.time() - t1:.0f}s", flush=True)
    t2 = time.time()
    pred = M.walk_forward(f, range(2015, 2026), verbose=True)
    print(f"[{kind}] walk_forward 2015-2025 in {time.time() - t2:.0f}s", flush=True)
    rows = []
    for w, seasons in WINDOWS.items():
        r = {"variant": kind, "window": w, **score(pred, seasons)}
        rows.append(r); print(r, flush=True)
    r = {"variant": kind, "window": "2019-25", **score(pred, range(2019, 2026))}
    rows.append(r); print(r, flush=True)
    res = {"variant": kind, "rows": rows, "seconds": round(time.time() - t0), "features_seconds": round(t2 - t1), "walk_seconds": round(time.time() - t2)}
    (SCRATCH / f"{kind}.json").write_text(json.dumps(res))
    print(f"[{kind}] DONE in {res['seconds']}s", flush=True)
    return res


def collect() -> None:
    res = {k: json.loads((SCRATCH / f"{k}.json").read_text()) for k in VARIANTS if (SCRATCH / f"{k}.json").exists()}
    rows = [r for k in VARIANTS if k in res for r in res[k]["rows"]]
    df = pd.DataFrame(rows)[["variant", "window", "team_mae", "margin_mae", "total_mae", "ats4", "ats5", "n"]]
    df["seconds"] = df.variant.map({k: v["seconds"] for k, v in res.items()})
    df.to_csv("reports/leverage_ratings.csv", index=False)
    base = df[df.variant == "base"].set_index("window")
    lines = ["", "## Results (walk_forward, weekly refit; REG games)", "",
             "| variant | window | team MAE | margin MAE | total MAE | 4+ ATS | 5+ ATS | n | vs base team / margin |", "|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        b = base.loc[r.window]
        lines.append(f"| {r.variant} | {r.window} | {r.team_mae:.4f} | {r.margin_mae:.4f} | {r.total_mae:.4f} | {r.ats4} | {r.ats5} | {r.n} | "
                     f"{r.team_mae - b.team_mae:+.4f} / {r.margin_mae - b.margin_mae:+.4f} |")
    verdict = []
    for k in VARIANTS:
        if k == "base" or k not in res:
            continue
        v = df[df.variant == k].set_index("window")
        ok = all((v.loc[w, "team_mae"] < base.loc[w, "team_mae"]) and (v.loc[w, "margin_mae"] < base.loc[w, "margin_mae"]) for w in WINDOWS)
        wins = [w for w in WINDOWS if (v.loc[w, "team_mae"] < base.loc[w, "team_mae"]) and (v.loc[w, "margin_mae"] < base.loc[w, "margin_mae"])]
        verdict.append(f"- {k}: {'ADOPT' if ok else 'not adopted'} (both MAEs lower than base on {len(wins)} of 3 windows: {', '.join(wins) or 'none'})")
    lines += ["", "## Verdict (by the adoption rule above)", ""] + verdict + ["",
              "Runtimes: " + ", ".join(f"{k} {v['seconds']}s (features {v['features_seconds']}s, walk-forward {v['walk_seconds']}s)" for k, v in res.items())]
    md = Path("reports/leverage_ratings.md").read_text().split("\n## Results")[0].rstrip("\n")
    Path("reports/leverage_ratings.md").write_text(md + "\n" + "\n".join(lines) + "\n")
    print(df.to_string(index=False)); print("\n".join(verdict))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "base"
    if arg == "collect":
        collect()
    else:
        run(arg)
