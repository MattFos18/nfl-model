"""The site-health alert must reach GitHub (3 Oct 2026: #343 deleted _sync_issue, main() kept calling it inside a
try/except, and no failing check opened an issue for three days)."""
import os
import nflmodel.health_alert as ha


def _run(monkeypatch, ok, open_issues):
    calls = []

    def fake_gh(*args):
        calls.append(args)
        if args[:2] == ("issue", "list"):
            return open_issues
        return ""
    monkeypatch.setattr(ha, "_gh", fake_gh)
    monkeypatch.setattr(ha, "status", lambda: (ok, [] if ok else ["x: reads 1, should read 2"], {"passed": 1, "total": 2}))
    monkeypatch.setattr(ha, "_ready_issues", lambda: None)
    monkeypatch.setenv("GH_TOKEN", "test")
    monkeypatch.setattr("shutil.which", lambda name: "gh")
    import nflmodel.picks_final as pf
    monkeypatch.setattr(pf, "notify", lambda gh: None)
    ha.main()
    return calls


def test_failing_checks_open_an_issue(monkeypatch, capsys):
    calls = _run(monkeypatch, ok=False, open_issues="[]")
    assert any(c[:2] == ("issue", "create") for c in calls)
    assert "could not update the issue" not in capsys.readouterr().out


def test_passing_checks_close_the_open_issue(monkeypatch, capsys):
    calls = _run(monkeypatch, ok=True, open_issues='[{"number": 337}]')
    assert ("issue", "close", "337") == calls[-1][:3]
    assert "could not update the issue" not in capsys.readouterr().out
