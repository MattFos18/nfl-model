"""The game-log files list each season's games once (nflmodel/player_logs.pack); unpack gives the same logs back."""
from nflmodel.player_logs import pack, unpack


def test_pack_round_trip():
    lg = {"p1": {"rec": [[1, "2025_01_PIT_NYJ", "PIT", "NYJ", 5], [2, "2025_02_SEA_PIT", "PIT", "SEA", 7]], "box": [[1, [[0, 3]]]]},
          "p2": {"pass": [[1, "2025_01_PIT_NYJ", "NYJ", "PIT", 30]]}}
    txt = "window.PLOGS_S=window.PLOGS_S||{};window.PLOGS_S[2025]=window.PLOGS_X(" + pack(lg) + ");"
    assert unpack(txt) == lg
