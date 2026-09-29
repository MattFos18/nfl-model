# Round 3 adoption rule (written 29 Sep 2026, before any round-3 result)

Matt: "Any small benefit I want accounted for if there is no risk", and "find me all ideas ... everything thought of and tested".

A change is adopted, however small the gain, only if all of these hold:

1. **Better on every window.** The miss (team points miss for the game model, yards per player-game for props,
   season-total miss for player season totals) is lower on 2015-18 (never used to choose anything), 2019-22 and
   2023-25. Where a study has only two scored windows, the fit window must not be worse either.
2. **No bet cost.** For anything touching the game model: the spread-bet and totals-flag records on the live rules are
   not worse on any window (wins minus losses at least equal), and the calibration of the win chance is not worse.
3. **Beats its own placebo.** The same input with its values shuffled within season (50 draws) must gain less than the
   real one on every window at least 45 times in 50 (the real gain above the 90th percentile of the placebo gains).
   This is what separates a small real gain from the one-in-eight noise pass.
4. **No new risk.** No market input, no look-ahead (every input as of before the game), no new data source that the
   weekly run does not already pull, and no page change beyond the number it moves.
5. **Together.** Adopted pieces are rerun together; the combination must itself pass 1 and 2.

Anything that fails stays computed as a reading where it already is, and is recorded in docs/how_it_works.md.
