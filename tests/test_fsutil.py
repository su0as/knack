"""Windows: os.replace onto a file another process is reading raises PermissionError (WinError 5).
Seen live 24 Oct 2026 when `knack ui` polled state.json during a run."""
import os

import pytest

from knack import fsutil


def _flaky_replace(fail_times):
    real = os.replace
    calls = {"n": 0}

    def fake(src, dst):
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise PermissionError(5, "Access is denied")
        return real(src, dst)

    return fake, calls


def test_retry_succeeds_after_transient_lock(tmp_path, monkeypatch):
    fake, calls = _flaky_replace(3)
    monkeypatch.setattr(fsutil.os, "replace", fake)
    assert fsutil.atomic_write_text(tmp_path / "state.json", '{"ok": 1}') is True
    assert (tmp_path / "state.json").read_text() == '{"ok": 1}' and calls["n"] == 4
    assert not list(tmp_path.glob("*.tmp"))


def test_best_effort_never_raises(tmp_path, monkeypatch):
    fake, _ = _flaky_replace(10_000)
    monkeypatch.setattr(fsutil.os, "replace", fake)
    monkeypatch.setattr(fsutil.time, "sleep", lambda s: None)
    assert fsutil.atomic_write_text(tmp_path / "state.json", "x", best_effort=True) is False
    assert not list(tmp_path.glob("*.tmp"))


def test_strict_raises_after_retries(tmp_path, monkeypatch):
    fake, _ = _flaky_replace(10_000)
    monkeypatch.setattr(fsutil.os, "replace", fake)
    monkeypatch.setattr(fsutil.time, "sleep", lambda s: None)
    with pytest.raises(PermissionError):
        fsutil.atomic_write_text(tmp_path / "result.json", "x")
