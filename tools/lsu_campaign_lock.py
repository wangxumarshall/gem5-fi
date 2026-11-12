#!/usr/bin/env python3
"""Campaign-scoped exclusive lock for the LSU formal matrix.

The lock file lives in the *campaign root* (``--out-base``), never in a
hard-coded historical directory.  Its content is JSON metadata::

    {"pid": 123, "hostname": "h", "started_at": "...",
     "campaign_id": "LSU-V333-FINAL-20261112", "out_base": "..."}

Rules
-----
* ``flock(LOCK_EX | LOCK_NB)`` is the authoritative liveness signal: the
  kernel releases it when the process exits, crashes or is killed, so a free
  lock always means no runner is executing.
* A busy lock raises :class:`LockHeld` immediately -- two runners can never
  own the same campaign.  ``--force`` cannot bypass this.
* When the lock is free but contains metadata, the metadata is archived to
  ``.lsu_v332_matrix.lock.stale/<pid>-<started_at>.json`` (with the observed
  PID/hostname liveness) before the new owner writes its own metadata.  The
  lock file itself is never deleted while held, and a live holder is never
  disrupted.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import socket
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

LOCK_NAME = ".lsu_v332_matrix.lock"
STALE_DIR = ".lsu_v332_matrix.lock.stale"


class LockHeld(RuntimeError):
    """Another runner owns (or appears to own) this campaign lock."""

    def __init__(self, message: str, metadata: dict | None = None):
        super().__init__(message)
        self.metadata = metadata or {}


class StaleLockError(RuntimeError):
    """Reserved for unreclaimable lock states (foreign host, invalid data)."""


def lock_path(out_base: Path) -> Path:
    return Path(out_base) / LOCK_NAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pid_alive(pid: object) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _metadata(fh) -> dict | None:
    try:
        fh.seek(0)
        text = fh.read()
    except OSError:
        return None
    text = (text or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        # Legacy lock files held a bare PID.
        if re.fullmatch(r"\d+", text):
            return {"pid": int(text), "hostname": None, "campaign_id": None,
                    "legacy": True}
        return {"raw": text, "invalid": True}
    return data if isinstance(data, dict) else None


def _archive_stale(out_base: Path, meta: dict | None, reason: str) -> None:
    if not meta:
        return
    directory = Path(out_base) / STALE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    pid = meta.get("pid", "unknown")
    stamp = re.sub(r"[^0-9A-Za-z_.-]", "", str(meta.get("started_at") or _now()))
    name = f"{pid}-{stamp}.json"
    payload = dict(meta)
    payload["stale_reason"] = reason
    payload["observed_pid_alive"] = _pid_alive(meta.get("pid"))
    payload["observed_hostname"] = socket.gethostname()
    payload["archived_at"] = _now()
    tmp = directory / (name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, directory / name)


@contextmanager
def campaign_lock(out_base: Path, campaign_id: str):
    """Hold the campaign lock for the duration of the matrix run."""
    path = lock_path(out_base)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+", encoding="utf-8")
    acquired = False
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            meta = _metadata(fh)
            raise LockHeld(
                f"campaign lock busy: {path} "
                f"(campaign={ (meta or {}).get('campaign_id')!r}, "
                f"pid={(meta or {}).get('pid')!r})", meta)

        # We own the flock, so no runner on this kernel is executing.  The
        # residual metadata still matters: if it names a LIVE pid that is not
        # provably ours, fail closed rather than stomp a possible owner.
        meta = _metadata(fh)
        if meta:
            host = socket.gethostname()
            different_campaign = meta.get("campaign_id") != campaign_id
            foreign_host = (bool(meta.get("hostname"))
                            and meta.get("hostname") != host)
            if (different_campaign or foreign_host) and _pid_alive(
                    meta.get("pid")):
                raise LockHeld(
                    f"campaign lock metadata names a live pid "
                    f"{meta.get('pid')!r} (campaign="
                    f"{meta.get('campaign_id')!r}, host="
                    f"{meta.get('hostname')!r}) at {path}", meta)
            reason = ("legacy_pid_file" if meta.get("legacy") else
                      "stale_lock_reclaimed")
            _archive_stale(out_base, meta, reason)

        record = {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "started_at": _now(),
            "campaign_id": campaign_id,
            "out_base": str(out_base),
        }
        fh.seek(0)
        fh.truncate()
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
        yield record
    finally:
        if acquired:
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
            finally:
                fh.close()
        else:
            fh.close()
