"""Run-manifest generation from the frozen LSU workbook.

A manifest is the *only* place a run gets its identity.  The seed, IDs,
workload path and fault fields are copied verbatim from the Excel; this module
never calls a random generator and never fills a missing field with a default.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from config_parser import load_config


class ManifestError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def find_sample(cfg: dict[str, Any], sample_id: str) -> dict[str, Any]:
    for sample in cfg["samples"]:
        if sample["sample_run_id"] == sample_id:
            return sample
    raise KeyError(f"SampleRunID not found: {sample_id}")


def _check_workload(sample: dict[str, Any]) -> Path:
    raw = sample.get("workload_path")
    if not raw or raw == "ABSENT":
        raise FileNotFoundError(
            f"workload ABSENT for {sample['sample_run_id']}: {sample.get('workload_path_source')!r}")
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(f"workload does not exist for {sample['sample_run_id']}: {path}")
    want = str(sample.get("binary_sha256", "")).lower()
    got = sha256_file(path)
    if want and want not in {"n/a", "na", "none"} and want != got:
        raise ManifestError(
            f"workload SHA mismatch for {sample['sample_run_id']}: expected {want}, got {got}")
    return path


def build_manifest(
    cfg: dict[str, Any],
    sample_id: str,
    gem5_bin: Path,
    config_script: Path,
    *,
    output_dir: Path | None = None,
    command: Sequence[str] | None = None,
    environment: dict[str, Any] | None = None,
    allow_workload_override: bool = False,
) -> dict[str, Any]:
    sample = find_sample(cfg, sample_id)
    if allow_workload_override:
        # Pilot-only directed workload: the Excel InputHash describes the
        # frozen W8 workload, so it cannot match the override. The manifest
        # records the override explicitly instead of pretending it matches.
        workload = Path(sample["workload_path"])
        if not workload.exists():
            raise FileNotFoundError(f"workload override missing: {workload}")
    else:
        workload = _check_workload(sample)
    gem5_bin = Path(gem5_bin)
    config_script = Path(config_script)
    if not gem5_bin.is_file():
        raise FileNotFoundError(f"gem5 binary does not exist: {gem5_bin}")
    if not config_script.is_file():
        raise FileNotFoundError(f"gem5 config script does not exist: {config_script}")

    out_dir = Path(output_dir) if output_dir else Path(sample.get("output_dir") or ".")
    cmd = list(command) if command is not None else [
        str(gem5_bin), f"--outdir={out_dir}", str(config_script),
        f"--cmd={workload}", "--cpu", "O3", "--variant", "B0",
    ]
    env = dict(environment or {})
    env.setdefault("captured_at_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    env.setdefault("host", platform.node())
    env.setdefault("kernel", platform.release())
    env.setdefault("python", platform.python_version())

    manifest: dict[str, Any] = {
        "schema_version": "lsu-run-manifest-v3.2",
        "sample_run_id": sample["sample_run_id"],
        "run_id": sample["run_id"],
        "sub_task_id": sample["sub_task_id"],
        "fault_id": sample.get("fault_config_id"),
        "model_id": sample["model_id"],
        "seed": sample["seed"],
        "seed_source": "excel:5.60个样本执行矩阵!Seed",
        "fault": {
            "location": sample.get("fault_location"),
            "target_field": sample.get("target_field"),
            "target_bit": sample.get("target_bit"),
            "normal_value": sample.get("normal_value"),
            "fault_value": sample.get("fault_value"),
            "injection_mode": sample.get("injection_mode"),
            "injection_timing": sample.get("injection_timing"),
            "target_event": sample.get("target_event"),
            "event_ordinal": sample.get("event_ordinal"),
        },
        "workload": {
            "path": str(workload),
            "path_source": sample.get("workload_path_source"),
            "sha256": sha256_file(workload),
            "oracle_expected": sample.get("oracle"),
        },
        "warmup": sample.get("warmup"),
        "roi": sample.get("roi"),
        "gem5": {
            "binary": str(gem5_bin.resolve()),
            "binary_sha256": sha256_file(gem5_bin),
            "config_script": str(config_script.resolve()),
            "config_script_sha256": sha256_file(config_script),
        },
        "output_dir": str(out_dir),
        "command": cmd,
        "command_shell": " ".join(cmd),
        "environment": env,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        canonical_json(manifest).encode("utf-8")).hexdigest()
    return manifest


def write_manifest(manifest: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workbook", type=Path)
    ap.add_argument("sample_id")
    ap.add_argument("gem5_bin", type=Path)
    ap.add_argument("config_script", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--outdir", type=Path)
    args = ap.parse_args(argv)
    cfg = load_config(args.workbook, require_complete=False)
    try:
        manifest = build_manifest(cfg, args.sample_id, args.gem5_bin,
                                  args.config_script, output_dir=args.outdir)
    except (FileNotFoundError, ManifestError, KeyError) as exc:
        print(f"MANIFEST_INVALID: {exc}", file=sys.stderr)
        return 2
    write_manifest(manifest, args.output)
    print(f"MANIFEST_OK {manifest['sample_run_id']} seed={manifest['seed']} "
          f"workload_sha256={manifest['workload']['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
