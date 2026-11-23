#!/usr/bin/env python3
"""Create and verify an independent backup of the 735 server raw traces.

The authoritative file list is FINAL_EVIDENCE_MANIFEST.csv
(Scope=SERVER_WORKSPACE).  The archive preserves the RelativePath recorded
there.  The target directory must be on a different filesystem device from
the source workspace.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED = {"raw_prop_trace": 240, "raw_commit_trace": 240,
            "raw_stdout": 240, "raw_rp01_stall_trace": 15}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--backup-dir", required=True)
    args = ap.parse_args()

    manifest = Path(args.manifest).resolve()
    source = Path(args.source_root).resolve()
    backup = Path(args.backup_dir).resolve()

    rows = [r for r in csv.DictReader(open(manifest))
            if r["Scope"] == "SERVER_WORKSPACE"]
    if len(rows) != 735:
        raise SystemExit("expected 735 SERVER_WORKSPACE rows, got %d"
                         % len(rows))
    counts = {}
    for r in rows:
        counts[r["FileType"]] = counts.get(r["FileType"], 0) + 1
    if counts != EXPECTED:
        raise SystemExit("unexpected file-type counts: %s" % counts)

    if not backup.parent.exists():
        raise SystemExit("backup parent does not exist: %s" % backup.parent)
    dev_source = source.stat().st_dev
    dev_backup = backup.parent.stat().st_dev
    if dev_source == dev_backup:
        raise SystemExit(
            "backup is on the same filesystem device (%d); refusing"
            % dev_source)

    backup.mkdir(parents=True, exist_ok=False)
    # ---- verify every source file ------------------------------------
    verified = []
    missing = []
    bad = []
    for r in rows:
        p = Path(r["AbsolutePath"])
        if not p.exists():
            missing.append(str(p))
            continue
        size = p.stat().st_size
        digest = sha256(p)
        if str(size) != r["Size"] or digest != r["SHA256"]:
            bad.append((str(p), size, r["Size"], digest, r["SHA256"]))
            continue
        verified.append((r, p))
    if missing or bad:
        raise SystemExit("source verification failed: missing=%d bad=%d\n%s"
                         % (len(missing), len(bad),
                            "\n".join(missing[:10] + [str(b) for b in
                                                      bad[:10]])))
    print("source verified: %d/%d" % (len(verified), len(rows)))

    # ---- build a deterministic tar.zst -------------------------------
    filelist = backup / "BACKUP_FILELIST.txt"
    rels = sorted(r["RelativePath"] for r, _ in verified)
    filelist.write_text("\n".join(rels) + "\n")
    archive = backup / "LSU_E2E_SERVER_TRACES_735.tar.zst"
    subprocess.run(["tar", "-C", str(source), "--zstd",
                    "-cf", str(archive), "-T", str(filelist)], check=True)
    archive_sha = sha256(archive)
    (backup / "ARCHIVE.sha256").write_text(
        "%s  %s\n" % (archive_sha, archive.name))

    # ---- prove the archive extracts and hashes -----------------------
    tmp = Path(tempfile.mkdtemp(prefix="lsu_backup_verify_",
                                dir=str(backup.parent)))
    try:
        subprocess.run(["tar", "-C", str(tmp), "--zstd", "-xf",
                        str(archive)], check=True)
        extracted = tmp / "extracted"
        # tar -C tmp writes the relative paths directly under tmp
        ok = 0
        for r, p in verified:
            q = tmp / r["RelativePath"]
            if q.exists() and sha256(q) == r["SHA256"]:
                ok += 1
        if ok != len(rows):
            raise SystemExit("archive extraction verification failed: %d/%d"
                             % (ok, len(rows)))
        print("archive extraction verified: %d/%d" % (ok, len(rows)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- independent backup manifest ---------------------------------
    out = []
    for i, (r, p) in enumerate(verified, 1):
        out.append({
            "EvidenceID": "BEV%05d" % i,
            "RunID": r["RunID"],
            "FileType": r["FileType"],
            "RelativePath": r["RelativePath"],
            "OriginalAbsolutePath": str(p),
            "BackupArchive": str(archive),
            "MemberPath": r["RelativePath"],
            "Size": r["Size"],
            "SHA256": r["SHA256"],
            "VerificationStatus": "SOURCE_AND_ARCHIVE_SHA256_MATCH",
        })
    with open(backup / "BACKUP_MANIFEST.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    (backup / "BACKUP_README.md").write_text(
        "# Independent backup of the 735 LSU server raw traces\n\n"
        "* Manifest: `%s` (Scope=SERVER_WORKSPACE)\n"
        "* Source root: `%s` (device %d)\n"
        "* Backup dir: `%s` (device %d, different filesystem)\n"
        "* Archive: `%s`\n"
        "* Archive SHA256: `%s`\n"
        "* Files: 735 (240 prop, 240 commit, 240 stdout, 15 RP01 stall)\n"
        "* Source files verified: 735/735 size + SHA256\n"
        "* Archive extraction verified: 735/735 SHA256\n\n"
        "Restore:\n\n"
        "```bash\n"
        "tar -C <destination> --zstd -xf %s\n"
        "sha256sum -c <manifest-derived SHA list>\n"
        "```\n"
        "The source workspace was not modified.\n"
        % (manifest, source, dev_source, backup, dev_backup, archive,
           archive_sha, archive.name))

    print("archive:", archive, archive.stat().st_size, archive_sha)
    print("backup manifest:", backup / "BACKUP_MANIFEST.csv")


if __name__ == "__main__":
    main()
