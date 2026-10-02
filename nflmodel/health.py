"""Weekly health check: did everything that should have run actually run, and did it pass? Reads the logs the
pipeline leaves behind and writes reports/health.md; exits non-zero on any FAIL so the health workflow can open an
issue. WARN rows are things worth a look that do not by themselves mean the numbers are wrong.

Checks: the weekly run is fresh and every step of the latest run is ok; enough runs in the last seven days; the
verification suite and the tie-out passed; the line watch is logging; the kickoff forecasts are fresh; the coming
week has a picks file and, when it flags games, matching tracker rows; the model settings the page quotes are the
code's. Usage: python -m nflmodel.health"""
from __future__ import annotations
import json, re, sys
import pandas as pd
from .features import RAW, OUT, ROOT
REP = ROOT / "reports"; DATA = ROOT / "data"; WEB = ROOT / "web" / "data"
IN_SEASON = (9, 10, 11, 12, 1, 2)   # months the checks about lines and picks apply to


def main() -> bool:
    now = pd.Timestamp.now("UTC").tz_localize(None); rows = []
    def add(level, what, detail): rows.append((level, what, detail))
    # 1. weekly run
    rl = DATA / "runs" / "run_log.csv"
    if rl.exists():
        log = pd.read_csv(rl); log["t"] = pd.to_datetime(log.run_at.str.replace(" UTC", ""), errors="coerce")
        last = log[log.t == log.t.max()]; age_h = (now - log.t.max()).total_seconds() / 3600
        add("FAIL" if age_h > 72 else "OK", "weekly run is fresh", f"last run {log.t.max():%Y-%m-%d %H:%M} UTC, {age_h:.0f} hours ago (limit 72)")
        bad = last[last.status != "ok"]
        add("FAIL" if len(bad) else "OK", "every step of the latest run ok", ", ".join(f"{r.step}: {r.status}" for r in bad.itertuples()) if len(bad) else f"{len(last)} steps ok")
        for step in ["verify", "tie check (sources)", "tie check (page)", "export data room", "record picks"]:
            add("OK" if step in set(last.step) else "FAIL", f"latest run has the step: {step}", "present" if step in set(last.step) else "missing")
        # the picks week holds until the week before is in every source (28 Sep 2026); a source more than 36 hours late fails
        try:
            from . import lines as _LN
            g_ = pd.read_parquet(DATA / "processed" / "games.parquet"); st = _LN.week_state(g_)
            if st["pending"]:
                last_k = pd.to_datetime(g_[(g_.season == st["season"]) & (g_.week == st["week"]) & (g_.game_type == "REG")].kickoff_et).max()
                late_h = (pd.Timestamp.now(tz="America/New_York").tz_localize(None) - last_k).total_seconds() / 3600
                add("FAIL" if late_h > 36 else "WARN", "picks week waiting on a late source", f"week {st['week']} kicked off fully {late_h:.0f} hours ago; missing: " + "; ".join(st["missing"]) + " (the run retries Tue 11am, 4pm and Wed 6am ET)")
            else:
                add("OK", "picks week's sources", f"week {st['week']}: " + ("every game in every source" if st["complete"] else "in play; the week before it is complete"))
        except Exception as e:  # noqa
            add("FAIL", "picks week's sources", f"could not check: {str(e)[:120]}")
        n7 = log[log.t > now - pd.Timedelta(days=7)].run_at.nunique()
        add("OK" if n7 >= 3 else "WARN", "runs in the last seven days", f"{n7} (four scheduled: Tue, Thu, Sat, Sun)")
    else:
        add("FAIL", "weekly run log", "data/runs/run_log.csv missing")
    # 2. verification and tie-out
    for name, f in [("verification suite", REP / "verification.md"), ("tie-out", REP / "tie_check.md")]:
        if f.exists():
            txt = f.read_text(); ok = re.search(r"Result: PASS", txt) is not None
            add("OK" if ok else "FAIL", f"{name} passed", (re.findall(r"Result: .*", txt) or ["no result line"])[-1])
        else:
            add("FAIL", f"{name} report", f"{f.name} missing")
    # 3. line watch (in season)
    wl = DATA / "lines" / "watch_log.csv"
    if now.month in IN_SEASON:
        if wl.exists():
            w = pd.read_csv(wl); w["t"] = pd.to_datetime(w.ts.str.replace("Z", ""), format="%Y-%m-%dT%H-%M-%S", errors="coerce")
            age_h = (now - w.t.max()).total_seconds() / 3600; n7 = int((w.t > now - pd.Timedelta(days=7)).sum())
            add("FAIL" if age_h > 24 else ("WARN" if age_h > 3 else "OK"), "line watch is logging", f"last snapshot {age_h:.1f} hours ago, {n7} in the last seven days (every 30 minutes when GitHub's cron fires)")
            zero = w[w.t > now - pd.Timedelta(days=2)]; z = int((zero.rows == 0).sum())
            add("WARN" if len(zero) and z == len(zero) else "OK", "line watch returns rows", f"{z} of {len(zero)} snapshots in the last two days logged no lines")
        else:
            add("FAIL", "line watch log", "data/lines/watch_log.csv missing")
        # 4. forecasts
        fl = DATA / "weather" / "forecast_latest.csv"
        if fl.exists():
            f = pd.read_csv(fl); ft = pd.to_datetime(f.fetched_at, errors="coerce").max(); age_h = (now - ft).total_seconds() / 3600 if pd.notna(ft) else 9e9
            add("FAIL" if age_h > 96 else "OK", "kickoff forecasts are fresh", f"fetched {age_h:.0f} hours ago (limit 96)")
            # 27 Sep 2026: every unplayed outdoor game inside the window has a reading (fetched, or carried from the last good fetch
            # once it kicked off): the forecast file used to drop a game at kickoff, and re-prices lost its weather
            try:
                from . import weather as WX
                g_ = pd.read_parquet(OUT / "games.parquet"); nowet = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
                g_ = g_[g_.home_score.isna() & (g_.game_type == "REG") & ~g_.roof.isin(["dome", "closed"]) & (g_.kickoff_et >= nowet - pd.Timedelta(days=2)) & (g_.kickoff_et <= nowet + pd.Timedelta(days=WX.USE_WITHIN_DAYS))]
                have = set(f[f.status.isin(["ok", "carried"])].game_id); miss = sorted(set(g_.game_id) - have)
                add("FAIL" if miss else "OK", "kickoff forecast for every outdoor game inside the window", f"{len(g_) - len(miss)} of {len(g_)} games have a reading" + (f"; missing: {', '.join(miss)}" if miss else ""))
            except Exception as e:  # noqa
                add("WARN", "kickoff forecast coverage", str(e)[:80])
        else:
            add("WARN", "kickoff forecasts", "data/weather/forecast_latest.csv missing")
        # 5. the coming week's picks and tracker
        try:
            from . import lines as LN
            g = pd.read_parquet(OUT / "games.parquet"); season, week = LN.current_week(g)
            pk = REP / f"picks_{season}_wk{week}.csv"
            add("OK" if pk.exists() else "FAIL", f"picks file for Week {week}, {season}", pk.name if pk.exists() else "missing")
            if pk.exists():
                # only games still to come: a flag on a game that has kicked off is never recorded (tracker._record), and a
                # recorded pick stays once its game starts; the week's file re-prices every game on the newest line
                kick = pd.to_datetime(g.set_index("game_id").kickoff_et); now_ = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
                p = pd.read_csv(pk); p = p[p.game_id.map(kick) > now_]; flagged = p[p.bet.fillna("") != ""]
                mp = DATA / "tracker" / "model_picks.csv"
                cur = pd.read_csv(mp) if mp.exists() else pd.DataFrame(columns=["season", "week", "bet"])
                cur = cur[(cur.season == season) & (cur.week == week) & (cur.game_id.map(kick) > now_)]
                same = sorted(flagged.bet) == sorted(cur.bet)
                add("OK" if same else "FAIL", "tracker holds the week's flags", f"picks: {sorted(flagged.bet)}; tracker: {sorted(cur.bet)}")
                from .picks import SHADOWS
                for name in SHADOWS:
                    col, f2 = f"{name}_bet", DATA / "tracker" / f"{name}_picks.csv"
                    if col in p.columns:
                        want = sorted(p[p[col].fillna("") != ""][col]); have = pd.read_csv(f2) if f2.exists() else pd.DataFrame(columns=["season", "week", "bet"])
                        have = sorted(have[(have.season == season) & (have.week == week) & (have.game_id.map(kick) > now_)].bet) if len(have) else []
                        add("OK" if want == have else "FAIL", f"shadow rule recorded for the week: {name}", f"picks: {want}; tracker: {have}")
        except Exception as e:  # noqa
            add("FAIL", "picks and tracker check", str(e)[:120])
    # 6. page quotes the code's settings
    try:
        from . import picks as P, model as M, ratings as R, players as PL
        s = (WEB / "week.js").read_text(); wk = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
        add("OK" if wk.get("spread_edge") == P.SPREAD_EDGE else "FAIL", "page flag threshold = code", f"page {wk.get('spread_edge')}, code {P.SPREAD_EDGE}")
        s = (WEB / "meta.js").read_text(); meta = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
        add("OK" if meta.get("feats") == M.FEATS else "FAIL", "page inputs = code", f"{len(meta.get('feats', []))} on the page, {len(M.FEATS)} in code")
        built = pd.to_datetime(str(meta.get("built", "")).replace(" UTC", ""), errors="coerce"); age_h = (now - built).total_seconds() / 3600 if pd.notna(built) else 9e9
        add("FAIL" if age_h > 96 else "OK", "page data is fresh", f"built {age_h:.0f} hours ago (limit 96)")
        # nothing on a card may be older than its source: the newest line snapshot on the cards is the log's newest, and the
        # props panel's line pull is the props log's newest (the line watch rewrites week.js after every snapshot)
        ll = pd.read_csv(RAW.parent / "lines" / "lines_log.csv", usecols=["ts", "game_id"]) if (RAW.parent / "lines" / "lines_log.csv").exists() else None
        page_ts = max([r["ts"] for g in wk.get("games", []) for r in g.get("line_history", [])] or ["none"])
        if ll is not None: ll = ll[ll.game_id.isin([g_["game_id"] for g_ in wk.get("games", [])])]   # the log's rows for the cards' games (29 Sep 2026: after the week's last kickoff the log carries only next week's)
        if ll is not None and len(ll):
            add("OK" if page_ts == ll.ts.max() else "FAIL", "cards carry the newest line snapshot", f"cards {page_ts}, log {ll.ts.max()}")
        pl = RAW.parent / "lines" / "props_log.csv"
        if pl.exists() and (WEB / "props.js").exists():
            s2 = (WEB / "props.js").read_text(); pj = json.loads(s2[s2.index("=") + 1:].rstrip().rstrip(";")); plog = pd.read_csv(pl, usecols=["ts", "season", "week"])
            cur = plog[(plog.season == pj.get("season")) & (plog.week == pj.get("week"))]
            mts = max([str(side.get("market_ts")) for gm in pj.get("games", {}).values() for side in gm.values() if side.get("market_ts")] or ["none"])
            if len(cur): add("OK" if mts == cur.ts.max() else "FAIL", "props panel carries the newest prop-line pull", f"page {mts}, log {cur.ts.max()}")
        # injury reports for the week being priced: the league's (nflverse, a lag of hours to a day) plus ESPN's page for
        # the teams not in yet; the ESPN file must be this week's (players.ESPN_MAX_AGE_DAYS) or it is not used
        try:
            from . import players as PL
            g = pd.read_parquet(OUT / "games.parquet"); season, week = LN.current_week(g)
            f = RAW / "injuries" / f"injuries_{season}.parquet"
            if not f.exists():
                raise RuntimeError("raw injuries not on this machine (the weekly run checks them)")
            nv = pd.read_parquet(f, columns=["week", "team"])
            have = set(nv[nv.week == week].team); ef = RAW / "injuries" / "espn_injuries.csv"
            es = pd.read_csv(ef) if ef.exists() else pd.DataFrame(columns=["team", "fetched_at"])
            e_age = (now - pd.to_datetime(es.fetched_at, errors="coerce").max()).total_seconds() / 86400 if len(es) else 9e9
            merged = PL.load_injuries([season]); merged = merged[merged.week == week]      # what the model actually sees, fill included
            fill = set(merged.team) - have
            days_to_kick = (g[(g.season == season) & (g.week == week)].kickoff_et.min() - pd.Timestamp.now("America/New_York").tz_localize(None)).total_seconds() / 86400
            gw = g[(g.season == season) & (g.week == week)]; playing = set(gw.home_team) | set(gw.away_team)   # teams with a game this week (a bye week has fewer than 32; 28 Sep 2026)
            covered = len((have | fill) & playing); level = "OK" if covered == len(playing) or days_to_kick > 2 else "WARN"
            add(level, f"injury reports cover the week being priced (week {week})", f"league reports for {len(have & playing)} teams, ESPN fills {len(fill & playing)} more ({'no ESPN file' if e_age > 1e8 else f'fetched {e_age * 24:.0f} hours ago'}), {covered} of {len(playing)} playing; first kickoff in {days_to_kick:.1f} days")
        except Exception as e:  # noqa
            add("OK" if "not on this machine" in str(e) else "WARN", "injury reports cover the week being priced", str(e)[:120])
        s = (WEB / "rankings.js").read_text(); rk = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
        add("OK" if rk.get("params", {}).get("qb_prior") == R.DEFAULT["qb_prior"] else "FAIL", "page rankings use the code's QB replacement level", f"page {rk.get('params', {}).get('qb_prior')}, code {R.DEFAULT['qb_prior']}")
    except Exception as e:  # noqa
        add("FAIL", "page settings check", str(e)[:120])
    # the QB-out check (2 Oct 2026, code review): ratings.qbs_out_now's injury load, and the week's swaps (starter ruled out ->
    # QB priced, and which source chose him); a failed load used to price every named starter silently
    sw_f = DATA / "runs" / "qb_swaps.json"
    if sw_f.exists():
        try:
            sw = json.loads(sw_f.read_text()); swaps = sw.get("swaps", [])
            lst = "; ".join(f"{x['team']} {x.get('from_name') or x['from']} -> {x.get('to_name') or x.get('to') or 'replacement-level prior'} ({x.get('source')})" for x in swaps)
            from . import lines as _LQ
            cur = list(_LQ.current_week(pd.read_parquet(OUT / "games.parquet")))
            st_ = sw.get("status")
            add("FAIL" if st_ == "error" else ("WARN" if st_ != "ok" or [sw.get("season"), sw.get("week")] != cur else "OK"), f"QB-out check loaded the injury reports (week {sw.get('week')})",
                f"{st_}{': ' + sw['detail'] if sw.get('detail') else ''}" + ("" if [sw.get("season"), sw.get("week")] == cur else f"; written for {sw.get('season')} week {sw.get('week')}, the picks week is {cur[0]} week {cur[1]}"))
            weak = [x for x in swaps if not x.get("to") or "no weekly roster" in str(x.get("source"))]   # priced at the prior, or a QB no roster could confirm
            add("WARN" if weak else "OK", f"QB swaps priced this week (week {sw.get('week')})", lst or "no named starter ruled out")
            um = sw.get("espn_unmatched") or []
            add("WARN" if um else "OK", "ESPN Out/Doubtful players all matched to a roster player", f"{len(um)} unmatched: {', '.join(um[:8])}" if um else "all matched")
        except Exception as e:  # noqa
            add("FAIL", "QB-out check", f"data/runs/qb_swaps.json unreadable: {str(e)[:100]}")
    else:
        add("WARN", "QB-out check", "data/runs/qb_swaps.json missing (written by the ratings step)")
    # warnings a step raised without failing (2 Oct 2026, code review; nflmodel/warnlog.py): a forecast that fell back to an
    # older pull or one model, a weather reader that priced games calm, a data check's forecast gaps
    try:
        from . import warnlog as WL_
        ws = WL_.recent()
        for src in sorted({w["source"] for w in ws}):
            m_ = [w["message"] for w in ws if w["source"] == src]
            add("WARN", f"warnings from {src} (last {WL_.WINDOW_H} hours)", f"{len(m_)}: " + "; ".join(m_[:4]))
        if not ws:
            add("OK", f"no step raised a warning in the last {WL_.WINDOW_H} hours", "data/weather/warnings.json")
    except Exception as e:  # noqa
        add("WARN", "step warnings", f"data/weather/warnings.json unreadable: {str(e)[:100]}")
    # the drift monitor (30 Sep 2026): an alert is a warning, never a failure (a real shift is news, not a broken run)
    try:
        dr = pd.read_csv(REP / "drift.csv"); al = dr[dr.level == "ALERT"]
        add("WARN" if len(al) else "OK", "drift monitor: numbers that move the edge are at their long-run level", "; ".join(f"{r.measure} (z {r.z:+.1f}, CUSUM {r.cusum:.1f})" for r in al.itertuples()) if len(al) else f"{len(dr)} measures within noise; {int((dr.level == 'WATCH').sum())} to watch")
    except Exception as e:  # noqa
        add("WARN", "drift monitor", f"no reports/drift.csv yet ({str(e)[:60]})")
    fails = [r for r in rows if r[0] == "FAIL"]; warns = [r for r in rows if r[0] == "WARN"]
    L = [f"# Health check, {now:%Y-%m-%d %H:%M} UTC", "", f"**{'BROKEN' if fails else 'HEALTHY'}**: {len(fails)} failing, {len(warns)} warnings, {len(rows) - len(fails) - len(warns)} ok.", "",
         "| Level | Check | Detail |", "|---|---|---|"] + [f"| {lv} | {w} | {d} |" for lv, w, d in rows] + ["", f"Result: {'FAIL' if fails else 'PASS'}"]
    REP.mkdir(exist_ok=True); (REP / "health.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
    return not fails


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
