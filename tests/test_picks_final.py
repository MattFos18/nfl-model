import pandas as pd
from nflmodel.picks_final import final_report


def test_final_report_days():
    assert final_report(pd.Timestamp("2026-10-01 20:15")) == pd.Timestamp("2026-09-30 16:00")   # Thursday: Wednesday
    assert final_report(pd.Timestamp("2026-10-04 13:00")) == pd.Timestamp("2026-10-02 16:00")   # Sunday: Friday
    assert final_report(pd.Timestamp("2026-10-04 09:30")) == pd.Timestamp("2026-10-02 16:00")   # London: Friday
    assert final_report(pd.Timestamp("2026-10-05 20:15")) == pd.Timestamp("2026-10-03 16:00")   # Monday: Saturday
