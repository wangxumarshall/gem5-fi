#!/usr/bin/env python3
"""Preserve and verify the six historical When-v2 target-squash paths.

The frozen evidence is read-only.  This script never rewrites it: it
re-verifies the frozen event identities, hashes and boundaries, then maps
each cell to the new E2E dynamic stream as a separate execution version.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

ROOT = L.ROOT
FROZEN = ROOT / "LSU_When_v2_FINAL_FROZEN"
EV = FROZEN / "FINAL_180_FAULT_EVIDENCE.csv"
REP = L.EXT / "reports"

CELLS = [
    ("FW02", "C05", "T01"), ("FW05", "C05", "T01"),
    ("FW05", "C05", "T02"), ("FW05", "C05", "T03"),
    ("LP01", "C05", "T02"), ("LQ04", "C05", "T03"),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_rows():
    with open(EV, newline="") as f:
        return {(r["ModelID"], r["ContextID"], r["TimingID"]): r
                for r in csv.DictReader(f)}


def frozen_evidence(run_id):
    for base in (ROOT / "results_hardened/runs", ROOT / "results/runs"):
        p = base / run_id / "attempt_1/evidence.json"
        if p.exists():
            return p
    return None


def verify_chain(ev):
    edges = ev.get("PropagationEdges", [])
    ids = [e["edge_id"] for e in edges]
    kinds = [e["edge_kind"] for e in edges]
    # The chain to the squash boundary must stay on the target's dynamic
    # instruction.  A post-squash reload (FW05's recovery evidence) is a
    # legitimate cross-instruction edge and is checked separately.
    core = [e for e in edges
            if e["edge_kind"] not in ("fw05_reload", "reload")]
    seq_ok = all(e["producer_inst_seq"] == e["consumer_inst_seq"]
                 for e in core)
    start_ok = bool(ev.get("InjectionEvent"))
    reach_reg = "payload_to_register" in kinds or "taint_reg" in kinds
    reload_ev = [e for e in ev.get("PropagationEvents", [])
                 if e.get("event_type") == "reload_evidence"]
    reload_ok = None
    if reload_ev:
        d = reload_ev[0].get("detail", "")
        try:
            rv = int(d.split("reload_data_fnv=")[1].split(";")[0], 16)
            tv = int(d.split("true_fnv=")[1].split(";")[0], 16)
            reload_ok = rv == tv
        except (IndexError, ValueError):
            reload_ok = False
    return {
        "edge_count": len(edges),
        "edge_ids_contiguous": ids == list(range(1, len(ids) + 1)),
        "same_dyn_inst": seq_ok,
        "starts_at_injection": start_ok,
        "reaches_register": reach_reg,
        "reload_ok": reload_ok,
        "edge_kinds": ";".join(kinds),
    }


def main():
    rows = load_rows()
    out = []
    version_map = []
    for model, ctx, timing in CELLS:
        r = rows[(model, ctx, timing)]
        run_id = r["RunID"]
        ejson = frozen_evidence(run_id)
        ev = json.loads(ejson.read_text()) if ejson else {}
        edge_path = ROOT / r["FullEdgesPath"]
        edge_sha_ok = (edge_path.exists() and
                       sha(edge_path) == r["FullEdgesSHA256"])
        tgt_seq = int(r["TARGET_SEQ"])
        sq_seq = int(r["SQUASH_SEQ"])
        boundary = ev.get("BoundaryEvidence", {})
        sqs = boundary.get("target_squash", [])
        sq = sqs[0] if sqs else {}
        detail = sq.get("detail", "")
        cause = "unrelated" if "squash_cause=unrelated" in detail else ""
        fault_caused = ("0" if "fault_caused=0" in detail else
                        ("1" if "fault_caused=1" in detail else ""))
        chain = verify_chain(ev)
        target_identity_ok = (tgt_seq == sq_seq ==
                              int(sq.get("dyn_inst_seq", -1))
                              if sq else False)
        withdrawal_ok = (
            r["TARGET_COMMITTED"].upper() == "NO" and
            r["TARGET_SQUASHED"].upper() == "YES" and
            boundary.get("foreign_commit_count") == 0 and
            not ev.get("TargetCommit"))
        oracle_ok = r["OraclePass"] in ("True", "true", "YES", "1")
        # New E2E stream
        new_id = f"E2E-{model}-{ctx}-{timing}-FAULT"
        new_path = L.EXT / "evidence/strict_chains" / f"{new_id}.strict.json"
        new = json.loads(new_path.read_text()) if new_path.exists() else {}
        new_tgt = (new.get("target") or {}).get("seq")
        new_arch = (new.get("architectural") or {})
        new_term = new.get("terminal")
        new_status = (new.get("classification") or {}).get("end_to_end_status")
        old_elf = r.get("CodeBinaryWorkloadHash", "")
        try:
            old_hash = json.loads(old_elf)
            old_elf_sha = old_hash.get("elf_sha")
        except ValueError:
            old_elf_sha = None
        new_elf_sha = ((new.get("versions") or {}).get("elf_sha"))
        status = "VERIFIED"
        notes = []
        if not edge_sha_ok:
            status = "UNRESOLVED"
            notes.append("frozen edge file missing or SHA256 mismatch")
        if not target_identity_ok:
            status = "UNRESOLVED"
            notes.append("target/squash dyn-inst identity mismatch")
        if cause != "unrelated" or fault_caused != "0":
            status = "UNRESOLVED"
            notes.append("squash cause was rewritten")
        if not withdrawal_ok:
            status = "UNRESOLVED"
            notes.append("withdrawal/no-foreign-commit proof missing")
        if not chain["same_dyn_inst"] or not chain["reaches_register"]:
            status = "UNRESOLVED"
            notes.append("propagation chain does not reach the register")
        if chain.get("reload_ok") is False:
            status = "UNRESOLVED"
            notes.append("post-squash reload did not recover the true value")
        if new_tgt is None:
            notes.append("new E2E run missing")
        elif new_tgt != tgt_seq:
            notes.append("dynamic stream changed: new target seq differs")
        out.append({
            "ModelID": model, "ContextID": ctx, "TimingID": timing,
            "OldRunID": run_id, "NewRunID": new_id,
            "OldTargetSeq": tgt_seq, "OldSquashSeq": sq_seq,
            "OldTargetRole": r["TargetRole"],
            "InjectionEventID": r["INJECTION_EVENT_ID"],
            "SquashEventID": r["SQUASH_EVENT_ID"],
            "SquashCause": cause, "FaultCausedSquash": fault_caused,
            "TargetCommitted": r["TARGET_COMMITTED"],
            "TargetSquashed": r["TARGET_SQUASHED"],
            "ForeignCommits": boundary.get("foreign_commit_count"),
            "WithdrawalVerified": withdrawal_ok,
            "ChainEdges": chain["edge_count"],
            "ChainEdgeKinds": chain["edge_kinds"],
            "ChainSameDynInst": chain["same_dyn_inst"],
            "ChainReachesRegister": chain["reaches_register"],
            "RecoveryReloadVerified": chain.get("reload_ok"),
            "OldOraclePass": oracle_ok,
            "OldEligibleOrdinal": r["SelectedOrdinal"],
            "FrozenEdgeSHA256Match": edge_sha_ok,
            "OldELFSHA256": old_elf_sha, "NewELFSHA256": new_elf_sha,
            "NewTargetSeq": new_tgt,
            "NewTargetCommitted": new_arch.get("target_committed"),
            "NewTargetSquashed": new_arch.get("target_squashed"),
            "NewTerminal": new_term, "NewE2EStatus": new_status,
            "Verdict": status, "Notes": "; ".join(notes),
        })
        version_map.append({
            "ModelID": model, "ContextID": ctx, "TimingID": timing,
            "FrozenRunID": run_id, "E2ERunID": new_id,
            "FrozenTargetSeq": tgt_seq, "E2ETargetSeq": new_tgt,
            "FrozenOrdinal": r["SelectedOrdinal"],
            "FrozenELFSHA256": old_elf_sha, "E2EELFSHA256": new_elf_sha,
            "ELFChanged": (old_elf_sha != new_elf_sha),
            "DynamicStreamChanged": (new_tgt != tgt_seq),
            "Interpretation": ("separate execution version; the frozen "
                               "squash evidence is preserved and is not "
                               "merged into the 180 E2E denominator"),
        })

    REP.mkdir(parents=True, exist_ok=True)
    p = REP / "STRICT_E2E_SQUASH_AUDIT.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    p2 = REP / "STRICT_E2E_SQUASH_VERSION_MAP.csv"
    with open(p2, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(version_map[0]))
        w.writeheader()
        w.writerows(version_map)
    print("wrote", p, p2)


if __name__ == "__main__":
    main()
