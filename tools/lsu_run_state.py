#!/usr/bin/env python3
"""Attempt isolation, canonical selection and task-state scanning.

This module is the frozen ABI shared by the matrix runner
(``tools/lsu_v332_matrix.py``) and the formal collector
(``tools/lsu_v333_launch.py``).

Layout for one task (``run_dir`` = ``OUT_BASE/<model>-R<ctx>-<role>``)::

    run_dir/
      attempts/
        attempt_001/        # every real execution is preserved here
          attempt.json
          summary.json
          command.txt
          ...
        attempt_002/
      canonical.json        # exactly one accepted AttemptId
      summary.json -> attempts/attempt_001/summary.json   (convenience view)
      command.txt  -> attempts/attempt_001/command.txt

Rules:
  * a completed attempt is never overwritten;
  * ``canonical.json`` is written once (``O_EXCL``) and never replaced;
  * a missing or unreadable record is never upgraded to ``COMPLETED``;
  * a legacy flat run dir (no ``attempts/``) is still readable, but its
    state is derived from the evidence on disk, never assumed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_OUTPUT_INCOMPLETE = "OUTPUT_INCOMPLETE"
STATUS_HASH_MISMATCH = "HASH_MISMATCH"
STATUS_ORACLE_FAIL = "ORACLE_FAIL"

ALL_STATUSES = (
    STATUS_PENDING, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED,
    STATUS_TIMEOUT, STATUS_OUTPUT_INCOMPLETE, STATUS_HASH_MISMATCH,
    STATUS_ORACLE_FAIL,
)

# States that are accepted as the canonical, final result for an identity.
CANONICAL_ACCEPTED = (STATUS_COMPLETED, STATUS_ORACLE_FAIL)
# States that allow a new attempt on resume.
RETRYABLE = (STATUS_PENDING, STATUS_RUNNING, STATUS_FAILED, STATUS_TIMEOUT,
             STATUS_OUTPUT_INCOMPLETE)

CANONICAL_FILE = "canonical.json"
ATTEMPTS_DIR = "attempts"
ATTEMPT_RECORD = "attempt.json"

# Convenience symlinks at the run-dir root pointing at the canonical attempt.
VIEW_NAMES = (
    "summary.json", "command.txt", "pilot_meta.json", "campaign.json",
    "stats.txt", "stdout.log", "stderr.log", "oracle.log",
    "trace_v31.jsonl", "prop_trace.csv.gz", "manifest.json",
    "config.ini", "config.json",
)

_ATTEMPT_RE = re.compile(r"^attempt_(\d{3,})$")


def task_tag(model: str, ctx: int, role: str) -> str:
    return f"{model}-R{int(ctx):02d}-{role}"


def attempts_root(run_dir: Path) -> Path:
    return Path(run_dir) / ATTEMPTS_DIR


def _existing_attempts(run_dir: Path) -> list[Path]:
    root = attempts_root(run_dir)
    if not root.is_dir():
        return []
    found = []
    for child in root.iterdir():
        m = _ATTEMPT_RE.match(child.name)
        if m and child.is_dir():
            found.append((int(m.group(1)), child))
    return [p for _, p in sorted(found)]


def next_attempt_id(run_dir: Path) -> str:
    existing = _existing_attempts(run_dir)
    n = 1
    if existing:
        m = _ATTEMPT_RE.match(existing[-1].name)
        n = int(m.group(1)) + 1
    return f"attempt_{n:03d}"


def attempt_dir(run_dir: Path, attempt_id: str) -> Path:
    return attempts_root(run_dir) / attempt_id


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_attempt_record(adir: Path, record: dict) -> None:
    write_path = Path(adir) / ATTEMPT_RECORD
    # A COMPLETED record is immutable: never rewrite it from a later state.
    old = read_attempt_record(adir)
    if old is not None and old.get("status") == STATUS_COMPLETED:
        if record.get("status") != STATUS_COMPLETED:
            raise RuntimeError(
                f"refusing to downgrade completed attempt {adir}")
        return
    _atomic_write_json(write_path, record)


def read_attempt_record(adir: Path) -> dict | None:
    path = Path(adir) / ATTEMPT_RECORD
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def read_canonical(run_dir: Path) -> dict | None:
    path = Path(run_dir) / CANONICAL_FILE
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def write_canonical(run_dir: Path, record: dict) -> bool:
    """Write ``canonical.json`` exactly once.

    Returns True when this call created it, False when an identical canonical
    already exists.  Raises when a *different* canonical is already present:
    an accepted result is never silently replaced.
    """
    path = Path(run_dir) / CANONICAL_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_canonical(run_dir)
    if existing is not None:
        same = (existing.get("attempt_id") == record.get("attempt_id")
                and existing.get("campaign_id") == record.get("campaign_id"))
        if same:
            return False
        raise RuntimeError(
            f"canonical already exists for {run_dir}: "
            f"{existing.get('attempt_id')} (refusing {record.get('attempt_id')})")
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with open(tmp, "x", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.link(tmp, path)          # atomic create-if-absent
    except FileExistsError:
        tmp.unlink(missing_ok=True)
        existing = read_canonical(run_dir)
        if existing and existing.get("attempt_id") == record.get("attempt_id"):
            return False
        raise RuntimeError(f"canonical raced for {run_dir}")
    finally:
        tmp.unlink(missing_ok=True)
    return True


def canonical_dir(run_dir: Path) -> Path:
    """The directory holding the accepted evidence (legacy dirs unchanged)."""
    run_dir = Path(run_dir)
    canonical = read_canonical(run_dir)
    if canonical is None:
        return run_dir
    adir = attempt_dir(run_dir, str(canonical.get("attempt_id", "")))
    return adir if adir.is_dir() else run_dir


def _is_legacy_complete(run_dir: Path) -> bool:
    return (run_dir / "summary.json").is_file()


def scan_task_state(run_dir: Path, campaign_id: str,
                    required_outputs: tuple[str, ...] = ("summary.json",),
                    ) -> dict:
    """Derive the task state from disk; never assumes success.

    Returns ``{state, attempt_id, canonical, reason, run_dir}``.
    """
    run_dir = Path(run_dir)
    result = {"run_dir": str(run_dir), "state": STATUS_PENDING,
              "attempt_id": None, "canonical": None, "reason": None}
    if not run_dir.exists():
        return result

    canonical = read_canonical(run_dir)
    if canonical is not None:
        cid = canonical.get("campaign_id")
        if cid is not None and str(cid) != str(campaign_id):
            result.update(state=STATUS_HASH_MISMATCH,
                          reason="CANONICAL_CAMPAIGN_MISMATCH")
            return result
        aid = str(canonical.get("attempt_id") or "")
        adir = attempt_dir(run_dir, aid)
        rec = read_attempt_record(adir)
        if rec is None:
            result.update(state=STATUS_OUTPUT_INCOMPLETE, attempt_id=aid,
                          canonical=canonical, reason="MISSING_ATTEMPT_RECORD")
            return result
        status = rec.get("status")
        missing = [n for n in required_outputs if not (adir / n).is_file()]
        if missing:
            result.update(state=STATUS_OUTPUT_INCOMPLETE, attempt_id=aid,
                          canonical=canonical,
                          reason="MISSING_OUTPUT:" + ",".join(missing))
            return result
        result.update(state=status, attempt_id=aid, canonical=canonical,
                      reason=rec.get("reason"))
        return result

    attempts = _existing_attempts(run_dir)
    if attempts:
        adir = attempts[-1]
        rec = read_attempt_record(adir)
        if rec is None:
            result.update(state=STATUS_OUTPUT_INCOMPLETE,
                          attempt_id=adir.name, reason="MISSING_ATTEMPT_RECORD")
            return result
        status = rec.get("status")
        if status in (STATUS_COMPLETED, STATUS_ORACLE_FAIL):
            # A terminal attempt without a canonical pointer is recoverable,
            # but never silently treated as complete.
            missing = [n for n in required_outputs if not (adir / n).is_file()]
            result.update(
                state=(STATUS_OUTPUT_INCOMPLETE if missing else status),
                attempt_id=adir.name,
                reason=("MISSING_OUTPUT:" + ",".join(missing)) if missing
                else "UNREGISTERED_CANONICAL")
            return result
        result.update(state=status, attempt_id=adir.name,
                      reason=rec.get("reason"))
        return result

    if _is_legacy_complete(run_dir):
        result.update(state=STATUS_COMPLETED, reason="LEGACY_FLAT_RUN_DIR")
        return result
    result.update(state=STATUS_OUTPUT_INCOMPLETE, reason="NO_ATTEMPT_EVIDENCE")
    return result


def link_canonical_view(run_dir: Path, adir: Path,
                        names: tuple[str, ...] = VIEW_NAMES) -> None:
    """Expose the canonical attempt's files at the run-dir root (symlinks).

    Existing regular files are never replaced: legacy evidence stays intact.
    """
    run_dir = Path(run_dir)
    adir = Path(adir)
    for name in names:
        src = adir / name
        dst = run_dir / name
        if not src.is_file() or dst.exists() or dst.is_symlink():
            continue
        try:
            os.symlink(os.path.relpath(src, run_dir), dst)
        except OSError:
            pass
