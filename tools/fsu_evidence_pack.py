#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_evidence_pack.py — losslessly compress very large injector logs.

High-volume F5 runs (millions of eligible events) write one line per
exposure to `fpu_injections.log`. The file is raw evidence, but a 350+ MB
plain text file is impractical for git/GitHub. This tool gzip-compresses it
LOSSLESSLY, records the original size/SHA-256 and the compressed SHA-256 in
`injection_log_storage.json`, removes the plain file, and rewrites
`evidence_sha256.json` so the seed audit still verifies every present file.

It never edits the log CONTENT and never touches propagation evidence
(prop_evt.txt.gz / chain_report.json / audit.json).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_seed_runner as R  # noqa: E402


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compress_log(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    orig_sha = _sha(path)
    orig_size = path.stat().st_size
    gz = path.with_suffix(path.suffix + ".gz")
    tmp = gz.with_suffix(gz.suffix + ".tmp")
    with open(path, "rb") as src, gzip.open(tmp, "wb", compresslevel=9) as dst:
        shutil.copyfileobj(src, dst, length=1 << 20)
    os.replace(tmp, gz)
    gz_sha = _sha(gz)
    gz_size = gz.stat().st_size
    path.unlink()
    return {
        "status": "compressed",
        "original": str(path),
        "original_sha256": orig_sha,
        "original_bytes": orig_size,
        "compressed": str(gz),
        "compressed_sha256": gz_sha,
        "compressed_bytes": gz_size,
        "method": "gzip-9 (lossless; content unchanged)",
    }


def pack_attempt(attempt: Path, threshold_mb: int = 64):
    attempt = Path(attempt)
    rec = {"attempt": str(attempt), "threshold_mb": threshold_mb,
           "files": []}
    for rel in ("inject/fpu_injections.log",
                "census/fpu_injections.log"):
        p = attempt / rel
        if not p.exists():
            continue
        if p.stat().st_size < threshold_mb * (1 << 20):
            continue
        rec["files"].append(compress_log(p))
    if not rec["files"]:
        rec["status"] = "no_large_log"
        return rec
    rec["status"] = "compressed"
    (attempt / "injection_log_storage.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    R.write_hashes(attempt)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="gzip large FSU injector logs")
    ap.add_argument("attempt")
    ap.add_argument("--threshold-mb", type=int, default=64)
    a = ap.parse_args(argv)
    print(json.dumps(pack_attempt(Path(a.attempt), a.threshold_mb),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
