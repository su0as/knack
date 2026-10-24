"""Atomic file replacement that survives Windows readers.

On Windows, os.replace() onto a file that another process has open (the console polling
state.json or live.jpg) fails with PermissionError [WinError 5]. Seen live on 23-24 Oct 2026:
a console-started run died in round 1. Readers hold files for milliseconds, so a short retry
loop is enough. Progress files are best-effort; results that other code depends on are not.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path


def _tmp_name(path: Path) -> Path:
    return path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")


def replace_with_retry(tmp: Path, dst: Path, *, attempts: int = 25, best_effort: bool = False) -> bool:
    delay = 0.005
    for i in range(attempts):
        try:
            os.replace(tmp, dst)
            return True
        except PermissionError:
            if i == attempts - 1:
                break
            time.sleep(delay)
            delay = min(delay * 2, 0.25)
    try:
        os.remove(tmp)
    except OSError:
        pass
    if best_effort:
        print(f"[knack] warning: could not update {dst} (file in use); continuing", file=sys.stderr)
        return False
    raise PermissionError(f"could not replace {dst} after {attempts} attempts (file in use by another program)")


def atomic_write_bytes(path, data: bytes, *, best_effort: bool = False) -> bool:
    path = Path(path)
    tmp = _tmp_name(path)
    tmp.write_bytes(data)
    return replace_with_retry(tmp, path, best_effort=best_effort)


def atomic_write_text(path, text: str, *, best_effort: bool = False) -> bool:
    return atomic_write_bytes(path, text.encode("utf-8"), best_effort=best_effort)
