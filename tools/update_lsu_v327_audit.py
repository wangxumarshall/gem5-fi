#!/usr/bin/env python3
"""v3.2.12: derive MODEL_STATUS_MATRIX.csv rows from the 12-model closure matrix.

LSU v3.2.12 Task 19 (final-report prep unit). This tool is the single
deterministic path from ``LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv``
to the ``PROPAGATION_VERIFIED`` flag and evidence cell of
``MODEL_STATUS_MATRIX.csv``. Nothing here hand-sets a verdict:

- ``PROPAGATION_VERIFIED=1`` only when ONE binary group of the model carries
  ``>= 2`` ``COMPLETE_CAUSAL_CHAIN`` records (the standard §4 distinct-context
  corroboration rule; the closure tool ``tools/lsu_12model_closure.py`` already
  adjudicated distinctness when it aggregated the group, and verdicts are never
  merged across binaries), or when a frozen prior audit (v3.2.11, the frozen
  four: DA04, LP01, MD04, FW05) says so via the frozen sidecar
  ``FROZEN_PRIOR_PROPAGATION_VERDICTS_v3.2.12.json``.
- Every model present in the template (the 12-model list) MUST have a matrix
  row; a missing row aborts the derivation unless the operator explicitly
  declares the model pending via ``--allow-pending`` (which can only ever
  produce ``PROPAGATION_VERIFIED=0`` with a ``PENDING_NO_ROW`` evidence cell).
- The frozen sidecar is cross-checked against two committed frozen artifacts
  (the v3.2.11 audit matrix and the frozen copy of the v3.2.11-era status
  matrix), so a fabricated sidecar cannot verify a model the frozen audit did
  not verify (e.g. FW02/LQ04, whose v3.2.11 PROPAGATION_VERIFIED is 0).
- The evidence cell quotes the per-model class (verbatim FinalClassification
  of the deciding group) and terminal (verbatim ObservedTerminal), plus the
  sha256 of the closure matrix actually consumed.

The tool never writes in place: ``--output`` must differ from ``--template``.
Stage/workflow flags (DESIGNED..PILOT_RUN) are carried unchanged from the
template; ``--set MODEL:COL=0|1`` may only touch those six flag columns — a
``--set`` on PROPAGATION_VERIFIED or evidence is rejected (no hand-set PASS).
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
BASE = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"

DEFAULT_CLOSURE_MATRIX = BASE / "audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv"
DEFAULT_TEMPLATE = BASE / "MODEL_STATUS_MATRIX.csv"
DEFAULT_FROZEN_VERDICTS = BASE / "audit_v3_2_12/FROZEN_PRIOR_PROPAGATION_VERDICTS_v3.2.12.json"
DEFAULT_FROZEN_AUDIT_MATRIX = BASE / "audit_v3_2_11/LSU_11Model_Propagation_Audit_Matrix.csv"
DEFAULT_FROZEN_STATUS_MATRIX = BASE / "audit_v3_2_12/MODEL_STATUS_MATRIX_v3.2.11_frozen.csv"

STATUS_HEADER = ["model", "unit", "stage", "DESIGNED", "SOURCE_AUDITED",
                 "IMPLEMENTED", "COMPILED", "UNIT_TESTED", "PILOT_RUN",
                 "PROPAGATION_VERIFIED", "evidence"]
SETTABLE_COLUMNS = {"DESIGNED", "SOURCE_AUDITED", "IMPLEMENTED", "COMPILED",
                     "UNIT_TESTED", "PILOT_RUN"}
CLASS_VALUES = {"COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT",
                "LIFECYCLE_ONLY", "PARTIAL", "UNRESOLVED"}


class DerivationError(Exception):
    """Loud, non-recoverable rejection. Never a silent zero or PASS."""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def base_model(model_id: str) -> str:
    """`SQ01@720eb780` -> `SQ01`; `LQ04` -> `LQ04` (single-binary rows carry no suffix)."""
    return model_id.split("@", 1)[0]


def parse_classification(cell: str, pilot_count: int) -> dict:
    """Parse a matrix FinalClassification cell into {class_name: count}.

    Accepts the two writer forms of tools/lsu_12model_closure.py:
      - mixed group:  mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)
      - uniform:      COMPLETE_CAUSAL_CHAIN   or   LIFECYCLE_ONLY(3/3)
    Rejects anything else, and any form whose counts do not sum to PilotCount.
    """
    cell = (cell or "").strip()
    if not cell:
        raise DerivationError(f"blank FinalClassification cell (PilotCount={pilot_count})")
    if cell.startswith("mixed(") and cell.endswith(")"):
        counts = {}
        for part in cell[len("mixed("):-1].split(";"):
            if "=" not in part:
                raise DerivationError(f"unparseable mixed FinalClassification: {cell!r}")
            name, _, num = part.partition("=")
            name = name.strip()
            if name not in CLASS_VALUES or not num.strip().isdigit():
                raise DerivationError(f"unparseable mixed FinalClassification: {cell!r}")
            counts[name] = counts.get(name, 0) + int(num.strip())
        if sum(counts.values()) != pilot_count:
            raise DerivationError(
                f"mixed counts {counts} do not sum to PilotCount={pilot_count}: {cell!r}")
        return counts
    m = re.match(r"^([A-Z_]+)(?:\((\d+)/(\d+)\))?$", cell)
    if m and m.group(1) in CLASS_VALUES:
        if m.group(2) is not None and int(m.group(2)) != pilot_count:
            raise DerivationError(f"uniform count does not match PilotCount: {cell!r}")
        return {m.group(1): pilot_count}
    raise DerivationError(f"unparseable FinalClassification: {cell!r}")


def load_closure_matrix(path: Path) -> dict:
    """Load the closure matrix grouped by base model; validate consumed cells."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"ModelID", "PilotCount", "FinalClassification", "ObservedTerminal",
                    "MissingEvidence", "EvidencePath"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise DerivationError(f"closure matrix {path} lacks columns: {sorted(missing)}")
        groups: dict[str, list[dict]] = {}
        for row in reader:
            model = base_model(row["ModelID"].strip())
            if not model:
                raise DerivationError(f"blank ModelID in closure matrix {path}")
            for col in ("PilotCount", "FinalClassification", "ObservedTerminal"):
                if not (row.get(col) or "").strip():
                    raise DerivationError(f"blank {col} cell for {row['ModelID']!r}")
            if not row["PilotCount"].strip().isdigit():
                raise DerivationError(f"non-integer PilotCount for {row['ModelID']!r}: "
                                      f"{row['PilotCount']!r}")
            row["_group_id"] = row["ModelID"].strip()
            row["_complete"] = parse_classification(row["FinalClassification"],
                                                    int(row["PilotCount"])).get(
                "COMPLETE_CAUSAL_CHAIN", 0)
            groups.setdefault(model, []).append(row)
    if not groups:
        raise DerivationError(f"closure matrix {path} has no data rows")
    return groups


def load_frozen_verdicts(verdicts_path: Path, audit_matrix_path: Path,
                         status_matrix_path: Path) -> dict:
    """Load + cross-check the frozen prior-audit sidecar.

    A sidecar entry may only carry a model that (a) exists in the frozen
    v3.2.11 audit matrix, (b) has >=1 complete record there, and (c) is
    PROPAGATION_VERIFIED=1 in the frozen v3.2.11-era status matrix.
    """
    data = json.loads(Path(verdicts_path).read_text(encoding="utf-8"))
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        raise DerivationError(f"frozen sidecar {verdicts_path} has no models")

    with open(audit_matrix_path, newline="", encoding="utf-8") as fh:
        audit_rows = {r["ModelID"].strip(): r for r in csv.DictReader(fh)
                      if (r.get("ModelID") or "").strip()}
    with open(status_matrix_path, newline="", encoding="utf-8") as fh:
        status_rows = {r["model"].strip(): r for r in csv.DictReader(fh)
                       if (r.get("model") or "").strip()}

    checked = {}
    for model, entry in models.items():
        if entry.get("propagation_verified") != 1:
            raise DerivationError(
                f"frozen sidecar entry {model} must carry propagation_verified=1 "
                "(anything else belongs in the closure matrix, not the sidecar)")
        if model not in audit_rows:
            raise DerivationError(
                f"frozen sidecar model {model} is absent from the frozen v3.2.11 "
                f"audit matrix {audit_matrix_path}")
        final = audit_rows[model].get("FinalClassification", "")
        if not re.search(r"COMPLETE_CAUSAL_CHAIN\s*[1-9]", final) and \
                not re.search(r"COMPLETE_CAUSAL_CHAIN\s*\d+/([1-9])", final):
            raise DerivationError(
                f"frozen sidecar model {model} has no complete record in the frozen "
                f"v3.2.11 audit matrix (FinalClassification={final!r})")
        if model not in status_rows:
            raise DerivationError(
                f"frozen sidecar model {model} is absent from the frozen status "
                f"matrix {status_matrix_path}")
        if status_rows[model].get("PROPAGATION_VERIFIED", "").strip() != "1":
            raise DerivationError(
                f"frozen sidecar model {model} is PROPAGATION_VERIFIED!=1 in the "
                f"frozen status matrix {status_matrix_path}; the frozen prior audit "
                "does not say so — refusing")
        checked[model] = entry
    return checked


def derive_rows(template_rows: list[dict], matrix_groups: dict, frozen: dict,
                pending: list[str], sets: dict[tuple[str, str], str],
                matrix_sha: str) -> tuple[list[dict], list[str]]:
    """Derive the new MODEL_STATUS_MATRIX rows. Returns (rows, report lines)."""
    template_models = [r["model"].strip() for r in template_rows]
    problems = []

    unknown_pending = [m for m in pending if m not in template_models]
    if unknown_pending:
        problems.append(f"--allow-pending names models absent from the template: "
                        f"{sorted(unknown_pending)}")

    for model in template_models:
        if model in pending and model in matrix_groups:
            problems.append(f"model {model} is declared --allow-pending but HAS a "
                            f"closure-matrix row {sorted(r['_group_id'] for r in matrix_groups[model])}; "
                            "remove the stale pending declaration")
        if model not in matrix_groups and model not in pending:
            problems.append(
                f"model {model} has no closure-matrix row in the supplied matrix; "
                "either regenerate the matrix to cover it or declare it pending "
                "explicitly via --allow-pending (never a silent zero)")

    matrix_only = sorted(set(matrix_groups) - set(template_models))
    if matrix_only:
        problems.append(f"closure matrix carries models absent from the template: {matrix_only}")

    if problems:
        raise DerivationError("; ".join(problems))

    rows, report = [], []
    for tmpl in template_rows:
        model = tmpl["model"].strip()
        new = {k: tmpl[k] for k in STATUS_HEADER if k in tmpl}
        for (m, col), val in sets.items():
            if m == model:
                new[col] = val

        if model in pending:
            new["PROPAGATION_VERIFIED"] = "0"
            new["evidence"] = (
                f"PENDING_NO_ROW: no closure-matrix row for {model} at matrix "
                f"sha256:{matrix_sha[:12]}… (declared pending via --allow-pending; "
                "not counted as verified or as evidence-graded)")
            report.append(f"{model}: PENDING (no matrix row) -> PROPAGATION_VERIFIED=0")
            rows.append(new)
            continue

        groups = matrix_groups[model]
        records = sum(int(r["PilotCount"]) for r in groups)
        best = max(groups, key=lambda r: r["_complete"])
        best_n = best["_complete"]
        complete_total = sum(r["_complete"] for r in groups)
        group_summary = "; ".join(
            f"{r['_group_id']}:{r['FinalClassification']}" for r in
            sorted(groups, key=lambda r: r["_group_id"]))

        if best_n >= 2:
            new["PROPAGATION_VERIFIED"] = "1"
            new["evidence"] = (
                f"v3.2.12 closure matrix sha256:{matrix_sha[:12]}…: "
                f"{best['_group_id']} FinalClassification={best['FinalClassification']} "
                f"with ObservedTerminal={best['ObservedTerminal']} "
                f"(>=2 distinct complete contexts inside one binary group; distinct "
                "contexts adjudicated by tools/lsu_12model_closure.py at aggregation, "
                "standard §4; never merged across binaries); "
                f"groups={len(groups)}, records={records}, "
                f"complete_total={complete_total}, best={best_n}@{best['_group_id'].split('@')[-1]}")
            if model in frozen:
                new["evidence"] += (
                    f"; frozen prior audit (v3.2.11) also carries "
                    f"{frozen[model]['class']!r} / terminal {frozen[model]['terminal']!r}")
            report.append(f"{model}: VERIFIED by matrix — best group "
                          f"{best['_group_id']} COMPLETE_CAUSAL_CHAIN={best_n} "
                          f"(groups={len(groups)}, records={records})")
        elif model in frozen:
            new["PROPAGATION_VERIFIED"] = "1"
            new["evidence"] = (
                f"frozen prior audit (v3.2.11) says PROPAGATION_VERIFIED=1 "
                f"[{frozen[model]['authority']}]; frozen class "
                f"{frozen[model]['class']!r}, frozen terminal "
                f"{frozen[model]['terminal']!r}; carried while the v3.2.12 closure "
                f"matrix sha256:{matrix_sha[:12]}… shows no binary group with >=2 "
                f"COMPLETE_CAUSAL_CHAIN (groups={len(groups)}, records={records}, "
                f"complete_total={complete_total}, best={best_n}@"
                f"{best['_group_id'].split('@')[-1]}; best group "
                f"FinalClassification={best['FinalClassification']}, "
                f"ObservedTerminal={best['ObservedTerminal']})")
            report.append(f"{model}: VERIFIED by frozen prior audit (matrix best "
                          f"group {best['_group_id']} COMPLETE_CAUSAL_CHAIN={best_n})")
        else:
            new["PROPAGATION_VERIFIED"] = "0"
            new["evidence"] = (
                f"v3.2.12 closure matrix sha256:{matrix_sha[:12]}…: no binary group "
                f"with >=2 COMPLETE_CAUSAL_CHAIN and no frozen prior-audit "
                f"verification; groups={len(groups)}, records={records}, "
                f"complete_total={complete_total}; per-group classes: {group_summary}; "
                f"best ObservedTerminal={best['ObservedTerminal']}; "
                f"MissingEvidence(head)={best['MissingEvidence']}")
            report.append(f"{model}: NOT verified (best group "
                          f"{best['_group_id']} COMPLETE_CAUSAL_CHAIN={best_n})")
        rows.append(new)
    return rows, report


def parse_set(spec: str) -> tuple[str, str, str]:
    """Parse `MODEL:COLUMN=VALUE` into its three parts; reject other shapes."""
    model, sep, rest = spec.partition(":")
    col, eq, val = rest.partition("=")
    if not (sep and eq) or not model.strip() or not col.strip():
        raise DerivationError(f"--set expects MODEL:COLUMN=VALUE, got {spec!r}")
    return model.strip(), col.strip(), val.strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Derive MODEL_STATUS_MATRIX.csv rows from the v3.2.12 closure matrix.")
    ap.add_argument("--closure-matrix", type=Path, default=DEFAULT_CLOSURE_MATRIX,
                    help="closure matrix CSV (default: the v3.2.12 matrix; parameterize "
                         "when the final regenerated matrix lands)")
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE,
                    help="existing MODEL_STATUS_MATRIX.csv supplying the model list, "
                         "unit/stage and workflow flags")
    ap.add_argument("--frozen-verdicts", type=Path, default=DEFAULT_FROZEN_VERDICTS,
                    help="frozen prior-audit sidecar JSON (v3.2.11 frozen four)")
    ap.add_argument("--frozen-audit-matrix", type=Path, default=DEFAULT_FROZEN_AUDIT_MATRIX,
                    help="frozen v3.2.11 audit matrix CSV used to cross-check the sidecar")
    ap.add_argument("--frozen-status-matrix", type=Path, default=DEFAULT_FROZEN_STATUS_MATRIX,
                    help="frozen v3.2.11-era status matrix CSV used to cross-check the sidecar")
    ap.add_argument("--allow-pending", action="append", default=[],
                    metavar="MODEL",
                    help="explicitly declare a model without a matrix row as PENDING "
                         "(records PROPAGATION_VERIFIED=0 with PENDING_NO_ROW evidence; "
                         "rejected if the model actually has a row)")
    ap.add_argument("--set", action="append", default=[], metavar="MODEL:COLUMN=VALUE",
                    help="override a workflow flag column (DESIGNED, SOURCE_AUDITED, "
                         "IMPLEMENTED, COMPILED, UNIT_TESTED, PILOT_RUN) for one model; "
                         "value must be 0 or 1. PROPAGATION_VERIFIED/evidence are NOT "
                         "settable — no hand-set PASS.")
    ap.add_argument("--output", type=Path, required=True,
                    help="destination CSV (must differ from --template)")
    args = ap.parse_args(argv)

    try:
        if args.output.resolve() == args.template.resolve():
            raise DerivationError("refusing to overwrite the template in place; "
                                  "write to --output and move it deliberately")
        sets = {}
        for spec in args.set:
            model, col, val = parse_set(spec)
            if col not in SETTABLE_COLUMNS:
                raise DerivationError(f"--set column {col!r} is not settable (allowed: "
                                      f"{sorted(SETTABLE_COLUMNS)}; PROPAGATION_VERIFIED/"
                                      "evidence are always tool-derived)")
            if val not in ("0", "1"):
                raise DerivationError(f"--set {model}:{col}={val!r}: workflow flags are 0/1")
            sets[(model, col)] = val

        with open(args.template, newline="", encoding="utf-8") as fh:
            template_rows = list(csv.DictReader(fh))
        if not template_rows:
            raise DerivationError(f"template {args.template} has no rows")
        header_miss = [c for c in STATUS_HEADER if c not in (template_rows[0] or {})]
        if header_miss:
            raise DerivationError(f"template {args.template} lacks columns: {header_miss}")

        matrix_groups = load_closure_matrix(args.closure_matrix)
        frozen = load_frozen_verdicts(args.frozen_verdicts, args.frozen_audit_matrix,
                                      args.frozen_status_matrix)
        matrix_sha = sha256_of(args.closure_matrix)
        rows, report = derive_rows(template_rows, matrix_groups, frozen,
                                   list(args.allow_pending), sets, matrix_sha)
    except DerivationError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=STATUS_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    print(f"closure matrix : {args.closure_matrix} (sha256 {matrix_sha})")
    print(f"template       : {args.template}")
    print(f"frozen sidecar : {len(frozen)} model(s) "
          f"{sorted(frozen)} (cross-checked against the frozen v3.2.11 audit)")
    for line in report:
        print(line)
    verified = sum(1 for r in rows if r["PROPAGATION_VERIFIED"] == "1")
    print(f"wrote {args.output}: {len(rows)} rows, PROPAGATION_VERIFIED=1 for "
          f"{verified} model(s); no cell hand-set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
