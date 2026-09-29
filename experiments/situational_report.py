"""Writes reports/situational_game.csv and reports/situational_game.md from the scratch results of
experiments/situational_game.py (real.csv, placebo.csv, combo.json, engine_check.json, notes.json)."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from experiments.situational_game import SCR, REP, WINDOWS, ideas, verdicts, placebo_summary, N_PLACEBO

FAMILIES = ["Situational", "Primetime and kickoff time", "Referees", "Weather", "Injuries", "Coaching matchups"]
NARRATIVE_PATH = SCR / "narrative.json"   # the readings, written by hand after the numbers were in


def _rec(r, k, w):
    return f"{int(r[f'{k}_w_{w}'])}-{int(r[f'{k}_l_{w}'])}"


def build_table():
    real = pd.read_csv(SCR / "real.csv")
    pl = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    V = verdicts(real).set_index("name")
    I = {i["name"]: i for i in ideas()}
    b = real[real.name == "(base)"].iloc[0]
    rows = []
    for name, i in I.items():
        if name not in V.index:
            continue
        r = real[real.name == name].iloc[0]; v = V.loc[name]
        ps = placebo_summary(name, real, pl) if (v.rule1 and v.rule2) or (len(pl) and (pl.name == name).any()) else {"draws": 0, "beaten": None, "pct": {}, "pass": False}
        fail = []
        if not v.rule1:
            bad = [w for w in WINDOWS if v[f"d_team_{w}"] >= 0 or (i["eq"] in ("T", "DT") and v[f"d_total_{w}"] >= 0)]
            fail.append("1 (" + ", ".join(bad) + ")")
        if not v.rule2:
            bad = [f"{w} " + "/".join(x for x, ok in [("spread", v[f"d_sp_{w}"] >= 0), ("totals", v[f"d_to_{w}"] >= 0), ("log loss", v[f"d_ll_{w}"] <= 1e-9)] if not ok) for w in WINDOWS
                   if not (v[f"d_sp_{w}"] >= 0 and v[f"d_to_{w}"] >= 0 and v[f"d_ll_{w}"] <= 1e-9)]
            fail.append("2 (" + "; ".join(bad) + ")")
        if v.rule1 and v.rule2 and not ps["pass"]:
            fail.append(f"3 ({ps['beaten']} of {ps['draws']} shuffles matched it)")
        eqlab = {"P": "points", "T": "total", "DP": "points, dropped", "DT": "total, dropped"}[i["eq"]]
        if i["eq"] in ("DP", "DT"):
            verdict = "live term earns its place (dropping it worsens every window)" if all(v[f"d_team_{w}"] > 0 for w in WINDOWS) else "re-check: dropping it does not worsen every window"
        else:
            verdict = "ADOPT" if not fail else "not adopted: rule " + "; ".join(fail)
        row = {"family": i["family"], "idea": name, "equation": eqlab, "inputs": " ".join(i["cols"]) + (" (+ opponent's)" if i["opp"] else "") + (f" [{i['mode']}]" if i["level"] == "game" and i["eq"] == "P" else ""),
               "rule1": bool(v.rule1), "rule2": bool(v.rule2), "placebo_draws": ps["draws"], "placebo_beaten": ps["beaten"],
               **{f"placebo_pct_{w}": ps["pct"].get(w) for w in WINDOWS}, "verdict": verdict, "effect": r.get("coefs", "")}
        for w in WINDOWS:
            row[f"d_team_miss_{w}"] = round(v[f"d_team_{w}"], 4); row[f"d_total_miss_{w}"] = round(v[f"d_total_{w}"], 4); row[f"d_margin_miss_{w}"] = round(v[f"d_margin_{w}"], 4)
            row[f"spread_{w}"] = _rec(r, "sp", w); row[f"d_spread_wl_{w}"] = int(v[f"d_sp_{w}"])
            row[f"totals_{w}"] = _rec(r, "to", w); row[f"d_totals_wl_{w}"] = int(v[f"d_to_{w}"])
            row[f"d_logloss_cal_{w}"] = round(v[f"d_ll_{w}"], 5); row[f"d_logloss_raw_{w}"] = round(v[f"d_llraw_{w}"], 5); row[f"d_brier_cal_{w}"] = round(v[f"d_brier_{w}"], 5)
            row[f"ml_{w}"] = _rec(r, "ml", w); row[f"ml_units_{w}"] = round(r[f"ml_units_{w}"], 1); row[f"d_ml_units_{w}"] = round(v[f"d_mlu_{w}"], 1)
        rows.append(row)
    return pd.DataFrame(rows), real, pl


def _pct(x):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:.0f}"


def write_report():
    T, real, pl = build_table()
    b = real[real.name == "(base)"].iloc[0]
    T.to_csv(REP / "situational_game.csv", index=False)
    chk = json.loads((SCR / "engine_check.json").read_text())
    notes = json.loads((SCR / "notes.json").read_text()) if (SCR / "notes.json").exists() else {}
    combo = json.loads((SCR / "combo.json").read_text()) if (SCR / "combo.json").exists() else {"passed": []}
    nar = json.loads(NARRATIVE_PATH.read_text()) if NARRATIVE_PATH.exists() else {}
    W = list(WINDOWS)
    L = ["# Situational ideas for the game model, under the round-3 rule (29 Sep 2026)", "",
         "`experiments/situational_game.py` (engine, ideas, runs), `experiments/situational_feats.py` (the inputs), `experiments/situational_report.py` (this page). "
         "Full numbers for every row: `reports/situational_game.csv`.", ""]
    L += nar.get("summary", [])
    L += ["", "## The rule and how each idea was run", "",
          "The rule is `reports/round3_rule.md`, written before any result, applied as written: (1) the team points miss lower on 2015-18, 2019-22 and 2023-25 "
          "(for an idea in the total equation, the total miss lower on all three too); (2) the spread flag (4+ points off the line, weeks 1-17) and the totals flag "
          "(under at a 55%+ raw chance, weeks 1-17) not worse on any window in wins minus losses, and the calibrated win chance's log loss not worse on any window; "
          f"(3) the idea's own values shuffled within each season, {N_PLACEBO} draws, and the real gain must beat the shuffled gain on every window in at least 45 of 50 draws; "
          "(4) no market input, no look-ahead, no new data source; (5) whatever passes is rerun together.", "",
          "Each idea is added on its own to the live model as it runs: a points idea joins the points inputs, so the live ridge, the five blend ridges and the "
          "boosted trees all carry it; a total idea joins the total equation. The weekly walk-forward (refit before every regular-season week on every played game "
          "since 2013) is reproduced step for step and was checked against `M.walk_forward` on a random candidate for 2019: largest differences "
          f"{chk['model_spread']:.1e} points on the spread, {chk['model_total']:.1e} on the total, {chk['p_home']:.1e} on the win chance, {chk['p_over_emp']:.1e} on the over chance "
          f"({chk['games']} games). The boosted trees are refit fresh on this machine for the base and every idea (the live trees' cache holds fits from GitHub's runners; "
          f"fresh fits move the base spread by {chk['fresh_vs_cached_trees_spread_mean']:.3f} points on average, at most {chk['fresh_vs_cached_trees_spread_max']:.2f}), so base and idea are compared like for like. "
          "Nothing under nflmodel/, web/ or data/processed was written.", "",
          "Every input is as of before its game: a history uses the key's games in earlier weeks only (a Thursday result never reaches that week's Sunday game, as "
          "the weekly run prices a whole week at once), and uses the result against the model's own expectation (the residual), never against a line: the live model's "
          "walk-forward number for 2014-2025 regular-season games, and a plain as-of scoring rating from scores alone for 1999-2013 and playoff games. Histories are "
          "shrunk with 20 games of weight toward zero (sum / (games + 20)), one value for every history, fixed before any result. \"Favourite\" is always the model's own favourite.", "",
          "Scored on the regular season. Base (fresh trees): team points miss " + " / ".join(f"{b[f'team_mae_{w}']:.4f}" for w in W) +
          ", total miss " + " / ".join(f"{b[f'total_mae_{w}']:.4f}" for w in W) + ", spread flag " + " / ".join(_rec(b, 'sp', w) for w in W) +
          ", totals flag " + " / ".join(_rec(b, 'to', w) for w in W) + ", calibrated log loss " + " / ".join(f"{b[f'll_cal_{w}']:.4f}" for w in W) +
          ", Brier " + " / ".join(f"{b[f'brier_cal_{w}']:.4f}" for w in W) + ", moneyline record of the model's side " + " / ".join(f"{_rec(b, 'ml', w)} ({b[f'ml_units_{w}']:+.1f}u)" for w in W) +
          " (2015-18 / 2019-22 / 2023-25).", ""]
    n_ideas = int((~T.equation.str.contains("dropped")).sum())
    n1 = int((T.rule1 & ~T.equation.str.contains("dropped")).sum()); n12 = int((T.rule1 & T.rule2 & ~T.equation.str.contains("dropped")).sum())
    L += [f"**Count.** {n_ideas} ideas added and {int(T.equation.str.contains('dropped').sum())} live terms re-checked by dropping them. {n1} of the {n_ideas} lower the miss on all three windows (rule 1); "
          f"by chance alone, with three windows each a coin flip, about one in eight would. {n12} also pass rule 2. Passing all of 1 to 3: {len(combo.get('passed', []))}.", ""]
    # master table
    def row_md(r):
        miss = " / ".join(f"{r[f'd_team_miss_{w}']:+.3f}" for w in W)
        tmiss = " / ".join(f"{r[f'd_total_miss_{w}']:+.3f}" for w in W) if "total" in r.equation else ""
        sp = " / ".join(f"{r[f'd_spread_wl_{w}']:+d}" for w in W); to = " / ".join(f"{r[f'd_totals_wl_{w}']:+d}" for w in W)
        ll = " / ".join(f"{1000 * r[f'd_logloss_cal_{w}']:+.1f}" for w in W)
        ml = " / ".join(f"{r[f'd_ml_units_{w}']:+.1f}" for w in W)
        plc = "" if not r.placebo_draws else (f"{_pct(r[f'placebo_pct_{W[0]}'])} / {_pct(r[f'placebo_pct_{W[1]}'])} / {_pct(r[f'placebo_pct_{W[2]}'])} ({r.placebo_draws} draws)")
        return f"| {r.idea} | {r.equation} | {miss} | {tmiss} | {sp} | {to} | {ll} | {ml} | {plc or 'not run (fails 1 or 2)'} | {r.verdict} |"
    head = ["| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    L += ["Reading the tables: every change is idea minus base, per window 2015-18 / 2019-22 / 2023-25. Misses in points (below zero is better). Flag records as the change "
          "in wins minus losses (above zero is better). Log loss of the calibrated win chance, times 1000 (below zero is better). Moneyline: the change in units won by "
          "the model's side at the closing moneyline (a reading; the rule does not use it). Placebo percentile: the share of shuffled draws whose gain the real idea beats, per window; "
          "run for ideas passing rules 1 and 2 (the rule's gate).", ""]
    for fam in FAMILIES:
        x = T[T.family == fam]
        if not len(x):
            continue
        L += [f"## {fam}", ""]
        L += nar.get(fam, [])
        L += [""] + head + [row_md(r) for _, r in x.iterrows()] + [""]
        eff = x[x.effect.fillna("") != ""]
        if len(eff):
            L += ["Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):", ""]
            L += [f"- {r.idea}: {r.effect}" for _, r in eff.iterrows()] + [""]
    L += ["## Rule 5: the passing pieces together", ""]
    if combo.get("passed"):
        res = combo["result"]
        L += [f"Together ({', '.join(combo['passed'])}): team points miss " + " / ".join(f"{res[f'team_mae_{w}'] - b[f'team_mae_{w}']:+.4f}" for w in W) +
              ", spread flag " + " / ".join(f"{res[f'sp_w_{w}']}-{res[f'sp_l_{w}']}" for w in W) + ", totals flag " + " / ".join(f"{res[f'to_w_{w}']}-{res[f'to_l_{w}']}" for w in W) +
              ", log loss change x1000 " + " / ".join(f"{1000 * (res[f'll_cal_{w}'] - b[f'll_cal_{w}']):+.2f}" for w in W) + "."]
    else:
        L += ["Nothing passed rules 1 to 3, so there is nothing to combine."]
    L += [""] + nar.get("code_change", []) + [""] + nar.get("readings", []) + [""] + nar.get("recorded", [])
    (REP / "situational_game.md").write_text("\n".join(L) + "\n")
    print("wrote", REP / "situational_game.md", len(T), "rows")
