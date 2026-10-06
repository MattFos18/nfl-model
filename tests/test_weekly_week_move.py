"""weekly.rerun_if_week_moved (6 Oct 2026): the week's input steps run again when the picks week moves while they run."""
from nflmodel import weekly as W


def _run(weeks):
    calls, it, log = [], iter(weeks), []
    W._RUN_AT["run_at"] = None   # no run log written
    W.rerun_if_week_moved(lambda suffix="": calls.append(suffix), lambda: next(it), log)
    return calls, log


def test_steps_run_once_when_the_week_holds():
    calls, log = _run([(2026, 5), (2026, 5)])
    assert calls == [""] and log == []


def test_steps_run_again_for_the_new_week_when_it_moves():
    calls, log = _run([(2026, 4), (2026, 5)])
    assert calls == ["", " (again, week 5)"]
    assert [r["step"] for r in log] == ["week moved mid-run"] and log[0]["status"] == "ok"
