# Audit: leak_fix_rescore (2 Oct 2026, model-auditor)

**Verdict: holds with caveats.** Both leaks are fixed, the numbers reproduce exactly, and ref_tot fails the round-3 rule once it is clean. Dropping it is the right call. Most of the totals-flag drop comes from the referee leak, so earlier totals adoptions scored with the leaky ref_tot need rescoring.

## Checks

1. **Look-ahead: pass.**
   - Referee prior: in the stored `trends_asof.parquet`, home and away ref_tot differ in 6,767 of 7,239 games. After the fixed `trends.trend_table` that falls to 0 of 7,239. `_prior_mean` now counts only rows of the same key with an earlier kickoff (`kickoff_et` is a full datetime, with no gaps from 2015 on). The other `_prior_mean` keys (team, pair|team, coach, qb_id) are never shared by the two rows of one game. ref_pen is now centred on the previous season.
   - Japan wind: d2, d1 and d0 get steadily more accurate against the observed wind (mean miss 3.44 / 3.34 / 3.22 mph over 1,444 games), and d1 equals d0 in only 4% of games. That fits d1 being an older run. I could not check Open-Meteo's run times (no network), so "d1 is issued 24 or more hours before the hour" is the docs' definition, not verified.
   - The old reading `jma_wind_d0` is still read only by `experiments/wind_forecast.py` and the study's `old_wind()`.
2. **Market inputs: pass.** ref_tot is game totals minus the previous season's league mean, with no line in it. The wind reading has no line in it either.
3. **Every window: pass (reproduced).** I reran all three variants and every number matches `reports/leak_fix_rescore.csv`. The "before" variant matches the published records: 68-55 / 80-51 / 40-21, 137-127 / 202-146 / 98-73, 23-19 / 143-89 / 83-52, total miss 10.738 / 10.493 / 10.108.
   - I also split the two fixes apart (my runs):

     | Run | Totals flag | Total miss |
     |---|---|---|
     | Referee fix only | 133-122 / 187-145 / 79-63 | 10.768 / 10.521 / 10.130 |
     | Wind fix only | 137-127 / 202-141 / 94-75 | 10.738 / 10.505 / 10.119 |

     So the referee leak accounts for most of the flag drop.
   - Clean ref_tot is worse on 2015-18 and 2019-22. It costs totals-flag wins on 2015-18 (net 12 to 11) and 2023-25 (net 18 to 13).
4. **Placebo: pass as reported.** I recounted from `reports/leak_fix_rescore_placebo.csv` (50 draws). The real gain beats 25 / 31 / 29 draws, against 45 needed. The real gains are -0.0053 / -0.0010 / +0.0005, so this is a fail even before the placebo.
5. **Snooping: pass.** Three variants. The fixes follow from timestamps, not from results. Japan d1 was the only stored Japan column issued before kickoff. Dropping a piece that fails the rule involves no selection.
6. **Sample size: pass, with a caveat.** The totals flag has about 255 / 324 / 137 bets, a standard error of about 3.1 / 2.8 / 4.3 points on the win rate. The ref_tot effects on the flag and the miss (0.001 to 0.005 points) are inside the noise, so with ref_tot or without it is a near wash. The rule still says drop it.
7. **Leak test: pass.**
   - I ran `audit.leakage_test()` with the trees-cache write turned off. Rating change 0.0, prediction change after corrupting future targets 0.0, and the new own-game check 0.0.
   - `tests/test_same_game_leak.py`: 6 passed.
   - Note: `trees_cache.parquet` was rewritten at 11:25:43, before my run started (another process; a tie_check log has the same timestamp). Not by this audit.

## What would change the verdict
- Open-Meteo's `previous_day1` turning out to include runs issued after kickoff.
- Caveat to act on: the adoptions of wind points, RAIN_FC (decision log, 1 Oct 2026) and qb_form_sum, plus the totals shadows' records, were all measured with the leaky ref_tot and the post-kickoff Japan wind. They should be rescored on the clean inputs before their published gains are trusted. The wind under's 10 mph cutoff and its placebo were set on the old reading; on the fixed reading it is 24-20 / 141-88 / 77-52, with no fresh placebo.
