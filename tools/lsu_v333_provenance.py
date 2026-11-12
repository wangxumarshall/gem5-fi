#!/usr/bin/env python3
"""LSU v3.3.3 workload provenance — three fields, real SHA256.

Every one of the 12 formal models gets exactly three workload fields:

* ``WorkloadSourcePath``  — canonical source artifact in this worktree.
* ``FormalExecutionPath`` — the file the runner actually executes; this is
  defined as ``tools/lsu_v332_matrix.resolve_workload(model,
  CONTEXTS[model].get("workload"))`` and is imported, never re-derived.
* ``ELF_SHA256``          — the real sha256 of the bytes at
  ``FormalExecutionPath``.

The frozen expectation comes from
``audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`` (the
9-workload table).  Hashes are always read from the file bytes; nothing is
invented and a missing file is reported, never defaulted.

Path discipline: neither field may point at another worktree
(``v3.2/``, ``v3.2.10/``) or an ``archive`` tree.  Two different-content files
sharing one basename inside the runner's workload roots are reported as an
ambiguity.

CLI::

    python3 tools/lsu_v333_provenance.py          # human table
    python3 tools/lsu_v333_provenance.py --json   # structured rows

Exit code is nonzero on any mismatch.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
FROZEN_PROVENANCE = (
    ROOT / "audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md"
)
MANIFEST_TEMPLATE = (
    ROOT / "audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv"
)
BINARY = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
CAMPAIGN_ROOT = ROOT / "runs/lsu/formal_v333_final_20261112"

# Frozen v3.3.3 launch values (plan global constraints).  Report-only when the
# file is absent; a mismatch is a launch-blocking failure.
EXPECTED_BINARY_SHA = "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd"
EXPECTED_CONFIG_SHA = "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225"

# Substrings that mark a path as belonging to a different/old tree.
FORBIDDEN_PATH_MARKERS = ("v3.2/", "v3.2.10/", "archive")

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-fA-F]{64})`\s*\|\s*$")

# ``lsu_v332_matrix`` is the single source of truth for the model->workload
# mapping.  Import it read-only (it reads the frozen identity CSV at import).
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import lsu_v332_matrix as _matrix  # noqa: E402

MODELS = tuple(_matrix.MODELS)


class ProvenanceError(RuntimeError):
    """Raised by strict callers when the provenance contract is violated."""


def sha256_file(path: Path) -> str:
    """Real sha256 of the file bytes (streamed; never synthesised)."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_frozen_table(path: Path = FROZEN_PROVENANCE) -> dict[str, str]:
    """Parse the frozen 9-workload table from the authorization document.

    Only the ``| \\`name\\` | \\`sha256\\` |`` rows in section 3 are taken.  A
    malformed or empty table is an error, never an empty success.
    """
    table: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _TABLE_ROW.match(line.strip())
        if m:
            name, digest = m.group(1), m.group(2).lower()
            if not _HEX64.match(digest):
                raise ProvenanceError(f"{path}: malformed sha256 for {name!r}")
            table[name] = digest
    if not table:
        raise ProvenanceError(f"{path}: no frozen workload rows found")
    return table


def formal_execution_path(model: str) -> Path:
    """The exact file the runner executes for ``model``."""
    path = _matrix.resolve_workload(model, _matrix.CONTEXTS[model].get("workload"))
    if path is None:
        raise ProvenanceError(f"{model}: resolve_workload returned None")
    return Path(path)


def workload_source_path(name: str) -> Path | None:
    """Canonical source artifact for a frozen workload basename.

    Priority: the git-tracked ``workloads/directed`` build output, then the
    frozen ``implementation_v3_2/workloads`` location.  Existing copies of the
    same basename are cross-checked by hash elsewhere.
    """
    for root in (_matrix.DIRECTED, _matrix.WORKLOADS):
        candidate = Path(root) / name
        if candidate.is_file():
            return candidate
    return None


def _forbidden_markers(path: Path) -> list[str]:
    text = str(path).replace("\\", "/").lower()
    return [marker for marker in FORBIDDEN_PATH_MARKERS if marker in text]


def _is_readable(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            fh.read(1)
        return True
    except OSError:
        return False


def find_duplicate_basenames(paths) -> list[dict]:
    """Return basename groups whose members hold different content.

    Identical-content copies (e.g. the directed source and the frozen formal
    copy of the same ELF) are not an ambiguity.
    """
    groups: dict[str, dict[str, list[str]]] = {}
    for raw in paths:
        path = Path(raw)
        groups.setdefault(path.name, {})
        try:
            digest = sha256_file(path)
        except OSError:
            digest = f"UNREADABLE:{path}"
        groups[path.name].setdefault(digest, []).append(str(path))
    duplicates = []
    for basename in sorted(groups):
        by_hash = groups[basename]
        if len(by_hash) > 1:
            duplicates.append({"basename": basename, "shas": by_hash})
    return duplicates


def runner_root_candidates(basenames=None) -> list[Path]:
    """Every copy of the frozen workload basenames inside the two runner roots."""
    names = set(basenames or load_frozen_table())
    candidates: list[Path] = []
    for root in (_matrix.DIRECTED, _matrix.WORKLOADS):
        root = Path(root)
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.is_file() and entry.name in names:
                candidates.append(entry)
    return candidates


def provenance_table(frozen: dict[str, str] | None = None) -> list[dict]:
    """One provenance row per model, with real hashes and verification flags."""
    frozen = dict(load_frozen_table() if frozen is None else frozen)
    rows: list[dict] = []
    for model in MODELS:
        exec_path = formal_execution_path(model)
        name = exec_path.name
        source_path = workload_source_path(name)
        exists = exec_path.is_file()
        readable = exists and _is_readable(exec_path)
        digest = sha256_file(exec_path) if readable else ""
        source_digest = ""
        if source_path is not None and source_path.is_file() and _is_readable(source_path):
            source_digest = sha256_file(source_path)
        expected = frozen.get(name)
        rows.append({
            "ModelID": model,
            "Workload": name,
            "WorkloadSourcePath": str(source_path) if source_path else "",
            "FormalExecutionPath": str(exec_path),
            "ELF_SHA256": digest,
            "FrozenSHA256": expected or "",
            "Exists": bool(exists),
            "Readable": bool(readable),
            "MatchesFrozen": bool(expected and digest == expected),
            "SourceExists": bool(source_path is not None and source_path.is_file()),
            "SourceMatchesFrozen": bool(expected and source_digest == expected),
            "ForbiddenMarkers": {
                "WorkloadSourcePath": _forbidden_markers(source_path) if source_path else [],
                "FormalExecutionPath": _forbidden_markers(exec_path),
            },
        })
    return rows


def provenance_errors(frozen: dict[str, str] | None = None) -> list[str]:
    """Every model/source/ambiguity/forbidden-path violation."""
    table = provenance_table(frozen=frozen)
    errors: list[str] = []

    frozen_table = dict(load_frozen_table() if frozen is None else frozen)
    used = {row["Workload"] for row in table}
    missing_frozen = sorted(set(frozen_table) - used)
    if missing_frozen:
        errors.append(f"frozen workloads not used by any model: {missing_frozen}")

    for row in table:
        model = row["ModelID"]
        if not row["Exists"]:
            errors.append(f"{model}: FormalExecutionPath missing: {row['FormalExecutionPath']}")
        elif not row["Readable"]:
            errors.append(f"{model}: FormalExecutionPath unreadable: {row['FormalExecutionPath']}")
        if not row["WorkloadSourcePath"]:
            errors.append(f"{model}: no WorkloadSourcePath for {row['Workload']!r}")
        elif not row["SourceExists"]:
            errors.append(f"{model}: WorkloadSourcePath missing: {row['WorkloadSourcePath']}")
        elif not row["SourceMatchesFrozen"]:
            errors.append(f"{model}: WorkloadSourcePath bytes differ from frozen {row['Workload']!r}")
        if not row["FrozenSHA256"]:
            errors.append(f"{model}: {row['Workload']!r} absent from the frozen table")
        elif not row["MatchesFrozen"]:
            errors.append(
                f"{model}: sha256 mismatch for {row['Workload']!r}: "
                f"actual {row['ELF_SHA256'] or 'n/a'} != frozen {row['FrozenSHA256']}"
            )
        for field, markers in row["ForbiddenMarkers"].items():
            if markers:
                errors.append(
                    f"{model}: {field} contains forbidden marker(s) {markers}: "
                    f"{row[field]}"
                )

    for duplicate in find_duplicate_basenames([row["FormalExecutionPath"] for row in table]):
        paths = sorted(p for paths in duplicate["shas"].values() for p in paths)
        errors.append(
            f"duplicate basename {duplicate['basename']!r} with different content: {paths}"
        )
    for duplicate in find_duplicate_basenames(runner_root_candidates(frozen_table)):
        paths = sorted(p for paths in duplicate["shas"].values() for p in paths)
        errors.append(
            f"workload-root ambiguity: basename {duplicate['basename']!r} has "
            f"different content at {paths}"
        )
    return errors


def verify_manifest_template(
    path: Path = MANIFEST_TEMPLATE,
    frozen: dict[str, str] | None = None,
) -> dict:
    """Check the 120-row template against resolve_workload() and real bytes."""
    frozen_table = dict(load_frozen_table() if frozen is None else frozen)
    result: dict = {
        "path": str(path),
        "rows": 0,
        "unique_sample_run_ids": 0,
        "unique_seeds": 0,
        "columns_present": [],
        "errors": [],
    }
    if not Path(path).is_file():
        result["errors"].append(f"manifest template missing: {path}")
        return result
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    result["rows"] = len(rows)
    required = ("WorkloadSourcePath", "FormalExecutionPath", "ELF_SHA256", "Evidence")
    result["columns_present"] = [name for name in required if name in fields]
    for name in required:
        if name not in fields:
            result["errors"].append(f"template missing column {name!r}")
    if result["rows"] != 120:
        result["errors"].append(f"template has {result['rows']} data rows, expected 120")

    run_ids: dict[str, list[dict]] = {}
    seeds: set[str] = set()
    for index, row in enumerate(rows, start=2):
        model = row.get("ModelID", "")
        if model not in _matrix.CONTEXTS:
            result["errors"].append(f"row {index}: unknown ModelID {model!r}")
            continue
        exec_path = formal_execution_path(model)
        source_path = workload_source_path(exec_path.name)
        row_exec = Path(row.get("FormalExecutionPath", "") or "/nonexistent")
        row_source = Path(row.get("WorkloadSourcePath", "") or "/nonexistent")
        if row_exec.resolve() != exec_path.resolve():
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: FormalExecutionPath "
                f"{row_exec} != resolve_workload {exec_path}"
            )
        if Path(row.get("ELF", "") or "/nonexistent").resolve() != exec_path.resolve():
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: ELF is not the formal execution path"
            )
        if source_path is None or row_source.resolve() != source_path.resolve():
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: WorkloadSourcePath {row_source} "
                f"!= canonical source {source_path}"
            )
        if row.get("Workload") != exec_path.name:
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: Workload {row.get('Workload')!r} "
                f"!= {exec_path.name!r}"
            )
        actual = sha256_file(exec_path) if exec_path.is_file() else ""
        expected = frozen_table.get(exec_path.name, "")
        if row.get("ELF_SHA256") != actual:
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: ELF_SHA256 {row.get('ELF_SHA256')} "
                f"!= actual {actual or 'n/a'}"
            )
        if expected and actual != expected:
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: actual sha256 differs from frozen table"
            )
        evidence = row.get("Evidence", "")
        if not str(Path(evidence)).startswith(str(CAMPAIGN_ROOT)):
            result["errors"].append(
                f"row {index} {row.get('RunID', '')}: Evidence {evidence!r} "
                f"not under {CAMPAIGN_ROOT}"
            )
        run_ids.setdefault(row.get("SampleRunID", ""), []).append(row)
        seeds.add(row.get("Seed", ""))

    result["unique_sample_run_ids"] = len(run_ids)
    result["unique_seeds"] = len(seeds)
    if result["unique_sample_run_ids"] != 60:
        result["errors"].append(
            f"{result['unique_sample_run_ids']} unique SampleRunID, expected 60"
        )
    if result["unique_seeds"] != 60:
        result["errors"].append(f"{result['unique_seeds']} unique Seed, expected 60")

    for sample_id, group in sorted(run_ids.items()):
        if len(group) != 2:
            result["errors"].append(
                f"SampleRunID {sample_id}: {len(group)} rows, expected fault+control pair"
            )
            continue
        roles = {row.get("Role") for row in group}
        if roles != {"fault", "control"}:
            result["errors"].append(f"SampleRunID {sample_id}: roles {sorted(roles)}")
        if len({row.get("Seed") for row in group}) != 1:
            result["errors"].append(f"SampleRunID {sample_id}: fault/control seeds differ")
        if len({row.get("ModelID") for row in group}) != 1:
            result["errors"].append(f"SampleRunID {sample_id}: models differ")
        if len({row.get("ContextID") for row in group}) != 1:
            result["errors"].append(f"SampleRunID {sample_id}: contexts differ")
    return result


def binary_config_fingerprints() -> dict:
    """Read-only fingerprints of the frozen binary and config."""
    binary_sha = sha256_file(BINARY) if BINARY.is_file() else ""
    config_sha = sha256_file(CONFIG) if CONFIG.is_file() else ""
    return {
        "BinaryPath": str(BINARY),
        "BinarySHA256": binary_sha,
        "BinaryMatchesFrozen": binary_sha == EXPECTED_BINARY_SHA,
        "ConfigPath": str(CONFIG),
        "ConfigSHA256": config_sha,
        "ConfigMatchesFrozen": config_sha == EXPECTED_CONFIG_SHA,
    }


def collect_report() -> dict:
    """Full structured report used by ``--json`` and the CLI."""
    table = provenance_table()
    manifest = verify_manifest_template()
    fingerprints = binary_config_fingerprints()
    errors = provenance_errors()
    errors += manifest["errors"]
    if not fingerprints["BinaryMatchesFrozen"]:
        errors.append(
            f"binary sha256 {fingerprints['BinarySHA256'] or 'missing'} "
            f"!= frozen {EXPECTED_BINARY_SHA}"
        )
    if not fingerprints["ConfigMatchesFrozen"]:
        errors.append(
            f"config sha256 {fingerprints['ConfigSHA256'] or 'missing'} "
            f"!= frozen {EXPECTED_CONFIG_SHA}"
        )
    return {
        "campaign_root": str(CAMPAIGN_ROOT),
        "models": [row["ModelID"] for row in table],
        "rows": table,
        "manifest": manifest,
        "binary_config": fingerprints,
        "errors": errors,
        "ok": not errors,
    }


def _print_table(report: dict) -> None:
    print("LSU v3.3.3 workload provenance")
    print(f"{'Model':<6} {'Workload':<24} {'FormalExecutionPath':<96} {'ELF_SHA256'}")
    for row in report["rows"]:
        status = "ok" if row["MatchesFrozen"] else "MISMATCH"
        print(
            f"{row['ModelID']:<6} {row['Workload']:<24} "
            f"{row['FormalExecutionPath']:<96} {row['ELF_SHA256'] or 'n/a'} [{status}]"
        )
    print()
    print(f"WorkloadSourcePath per model:")
    seen: set[str] = set()
    for row in report["rows"]:
        if row["Workload"] in seen:
            continue
        seen.add(row["Workload"])
        print(f"  {row['Workload']:<24} {row['WorkloadSourcePath'] or 'MISSING'}")
    print()
    manifest = report["manifest"]
    print(
        f"Manifest template: {manifest['path']} rows={manifest['rows']} "
        f"SampleRunID={manifest['unique_sample_run_ids']} seeds={manifest['unique_seeds']} "
        f"columns={manifest['columns_present']}"
    )
    fingerprints = report["binary_config"]
    print(
        f"Binary: {fingerprints['BinaryPath']} {fingerprints['BinarySHA256'] or 'MISSING'} "
        f"[{'ok' if fingerprints['BinaryMatchesFrozen'] else 'MISMATCH'}]"
    )
    print(
        f"Config: {fingerprints['ConfigPath']} {fingerprints['ConfigSHA256'] or 'MISSING'} "
        f"[{'ok' if fingerprints['ConfigMatchesFrozen'] else 'MISMATCH'}]"
    )
    if report["errors"]:
        print(f"\nFAIL: {len(report['errors'])} provenance error(s)")
        for error in report["errors"]:
            print(f"  - {error}")
    else:
        print("\nPASS: all 12 models resolve to frozen ELF bytes; manifest template consistent")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)
    report = collect_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_table(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
