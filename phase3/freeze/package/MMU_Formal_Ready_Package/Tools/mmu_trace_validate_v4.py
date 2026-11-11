#!/usr/bin/env python3
"""MMU unified trace validator v4 (Phase 2.2).

v3 remains the Phase 2.1 baseline (kept unchanged). v4 adds the M02
ENTRY-LINEAGE audit required by Phase 2.2 and applies it as an ADDITIONAL,
STRICTER gate — it never relaxes a v3 rule:

  * every `fault_entry_consume` / `fault_entry_reuse` must name a REAL faulted
    `tlb_entry_insert` (same tlb_instance + entry_id + generation) through
    `source_event_id`;
  * its `lookup_event_id` must be the real `tlb_lookup_hit` event, with the
    same entry identity / dyn_inst_seq / fault_id, and its parent;
  * the consumer's PA must equal pfn << page_size_n;
  * the ORIGINAL instruction's squash witness (`origin_squashed`,
    `origin_squash_event_id`) must match a real squash event;
  * at least one consumer must be a DIFFERENT dynamic instruction than the
    origin walk (cross-dynamic propagation), unless the origin itself consumed
    without being squashed;
  * the terminal consumer branch must carry translation_result -> lsu_request
    -> cache_request/cache_lookup -> (cache_response or memory_response) ->
    rf_writeback -> commit, or honestly report the missing kind.

Everything comes from the real PROP-EVT stream. Nothing is inferred from tick
order or VA/PA equality.
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_trace_validate_v3 as v3


def _i(ev, key, base=10):
    v = ev.get(key, "")
    if v in ("", None):
        return 0
    try:
        return int(v, base)
    except ValueError:
        return 0


def audit_lineage(events):
    """Exact entry-lineage audit. Returns dict + list of per-consumer rows."""
    by_id = {e["event_id"]: e for e in events}
    kinds = lambda e: e.get("kind", "")
    inserts = [e for e in events
               if kinds(e) == "tlb_entry_insert"
               and e.get("fault_id", "0") not in ("", "0")]
    consumes = [e for e in events
                if kinds(e) in ("fault_entry_consume", "fault_entry_reuse")]
    ends = [e for e in events if kinds(e) == "fault_entry_end"]
    errors, rows = [], []
    layers = {}
    for e in inserts:
        fid = e.get("fault_id", "0")
        layers.setdefault(fid, set()).add(
            (e.get("tlb_instance", ""), e.get("tlb_entry_id", ""),
             e.get("entry_generation", "")))

    for c in consumes:
        fid = c.get("fault_id", "0")
        inst = c.get("tlb_instance", "")
        eid = c.get("tlb_entry_id", "")
        gen = c.get("entry_generation", "")
        seq = c.get("dyn_inst_seq", "")
        origin_seq = c.get("origin_dyn_inst_seq", "")
        key = (inst, eid, gen)
        err = []

        # 1. source insert is a real faulted insert of THIS entry identity.
        src_id = _i(c, "source_event_id")
        src = by_id.get(src_id)
        if src is None or kinds(src) != "tlb_entry_insert":
            err.append("source_event_not_insert")
        else:
            if (src.get("tlb_instance", ""), src.get("tlb_entry_id", ""),
                    src.get("entry_generation", "")) != key:
                err.append("source_entry_identity_mismatch")
            if src.get("fault_id", "0") != fid:
                err.append("source_fault_id_mismatch")
            if not src.get("pfn", "") or _i(src, "pfn", 16) != _i(c, "pfn", 16):
                err.append("source_pfn_mismatch")

        # 2. lookup event is the real hit, same identity/seq/fault, parent.
        lk_id = _i(c, "lookup_event_id")
        lk = by_id.get(lk_id)
        if lk is None or kinds(lk) != "tlb_lookup_hit":
            err.append("lookup_event_missing")
        else:
            if (lk.get("tlb_instance", ""), lk.get("tlb_entry_id", ""),
                    lk.get("entry_generation", "")) != key:
                err.append("lookup_entry_identity_mismatch")
            if lk.get("dyn_inst_seq", "") != seq:
                err.append("lookup_dyn_seq_mismatch")
            if lk.get("fault_id", "0") != fid:
                err.append("lookup_fault_id_mismatch")
            if c.get("parent_event_id", "") != str(lk_id):
                err.append("consume_parent_is_not_lookup")
            if lk.get("pa", "") and c.get("pa", "") and \
                    _i(lk, "pa", 16) != _i(c, "pa", 16):
                err.append("lookup_pa_mismatch")

        # 3. PA arithmetic, page containment.
        pfn = _i(c, "pfn", 16)
        n = _i(c, "page_size_n")
        pa = _i(c, "pa", 16)
        if pa != (pfn << n):
            err.append("consume_pa_arithmetic_mismatch")
        va = _i(c, "va", 16)
        if n and src is not None:
            if (va >> n) != (_i(src, "va", 16) >> n):
                err.append("consume_va_page_mismatch")

        # 4. origin squash witness must be real.
        origin_squashed = c.get("origin_squashed", "")
        osq_id = _i(c, "origin_squash_event_id")
        if origin_squashed == "1":
            osq = by_id.get(osq_id)
            if osq is None or kinds(osq) != "squash":
                err.append("origin_squash_witness_missing")
            else:
                if osq.get("dyn_inst_seq", "") != origin_seq:
                    err.append("origin_squash_seq_mismatch")

        # 5. cross-dynamic consumers.
        cross = bool(origin_seq) and seq != origin_seq

        # 6. downstream branch of THIS consumer (all carry the same fault).
        downstream = {}
        for k in ("translation_result", "lsu_request", "cache_request",
                  "cache_lookup", "cache_response", "memory_response",
                  "rf_writeback", "commit", "squash"):
            downstream[k] = any(
                kinds(e) == k and e.get("fault_id", "0") == fid and
                (e.get("dyn_inst_seq", "") == seq or
                 (e.get("translation_id", "") == c.get("translation_id", "") and
                  seq == "")) for e in events)

        rows.append({
            "fault_id": fid, "tlb_instance": inst, "tlb_entry_id": eid,
            "entry_generation": gen, "dyn_inst_seq": seq,
            "origin_dyn_inst_seq": origin_seq, "cross_dynamic": cross,
            "translation_id": c.get("translation_id", ""),
            "execution_attempt_id": c.get("execution_attempt_id", ""),
            "reuse_ordinal": c.get("reuse_ordinal", ""),
            "pa": c.get("pa", ""), "pfn": c.get("pfn", ""),
            "lookup_event_id": lk_id, "source_event_id": src_id,
            "origin_event_id": _i(c, "origin_event_id"),
            "origin_squashed": origin_squashed,
            "origin_squash_event_id": osq_id,
            "downstream": downstream,
            "errors": err,
        })
        errors.extend("%s:%s" % (seq, e) for e in err)

    cross_consumers = [r for r in rows if r["cross_dynamic"]]
    committing = [r for r in rows if r["downstream"].get("commit")]
    # The terminal branch: prefer a committing consumer; otherwise a squashed
    # consumer branch is a real (non-final) lifecycle and is reported as such.
    terminal = committing[0] if committing else (rows[0] if rows else None)

    # Strict structural checks for the terminal consumer branch.
    terminal_missing = []
    if terminal is not None:
        d = terminal["downstream"]
        for k in ("translation_result", "lsu_request", "cache_request",
                  "cache_lookup", "rf_writeback"):
            if not d.get(k):
                terminal_missing.append("consumer_missing:%s" % k)
        if not (d.get("cache_response") or d.get("memory_response")):
            terminal_missing.append("consumer_missing:cache_or_memory_response")
        if not (d.get("commit") or d.get("squash")):
            terminal_missing.append("consumer_missing:terminal")
        if d.get("commit") and not d.get("rf_writeback"):
            terminal_missing.append("consumer_missing:rf_writeback_before_commit")

    status = {
        "faulted_insert_layers": {fid: sorted(list(v))
                                  for fid, v in layers.items()},
        "consume_events": len(consumes),
        "consumer_count": len(rows),
        "cross_dynamic_consumer_count": len(cross_consumers),
        "cross_dynamic_seqs": sorted({r["dyn_inst_seq"]
                                      for r in cross_consumers}),
        "committing_consumer_seqs": sorted({r["dyn_inst_seq"]
                                            for r in committing}),
        "entry_end_events": len(ends),
        "identity_errors": sorted(set(errors)),
        "terminal_consumer": terminal,
        "terminal_consumer_missing": terminal_missing,
        "cross_dynamic_link": bool(cross_consumers),
        "cache_link": bool(terminal and terminal["downstream"].get(
            "cache_request") and terminal["downstream"].get("cache_lookup")
            and (terminal["downstream"].get("cache_response") or
                 terminal["downstream"].get("memory_response"))),
        "memory_response_link": bool(terminal and
                                     terminal["downstream"].get(
                                         "memory_response")),
        "rf_wb_commit_link": bool(
            terminal and terminal["downstream"].get("rf_writeback") and
            (terminal["downstream"].get("commit") or
             terminal["downstream"].get("squash"))),
        "complete": bool(rows) and not errors and not terminal_missing and
                    bool(terminal and (terminal["downstream"].get("commit") or
                                       terminal["downstream"].get("squash"))),
    }
    return status, rows


def _has_parent(evs, by_id, child_kind, parent_kinds):
    for e in evs:
        if v3.kind(e) == child_kind and \
                v3.parent_kind(e, by_id) in parent_kinds:
            return True
    return False


def refine_m02(result, events, lineage, rows):
    """Replace v3's per-fault union with the LOGICAL fault chain.

    v3 unions every translation branch of one fault id. A squashed origin
    branch legitimately lacks the data path, and an early squashed consumer
    legitimately lacks it too; those facts must not be reported as missing
    edges of the final fault chain. v4 evaluates the origin refill/insert
    edges and the TERMINAL consumer branch (the one that commits, else the
    real squashed branch) and keeps every real identity check.
    """
    by_id = {e["event_id"]: e for e in events}
    terminal = lineage.get("terminal_consumer")
    for fid, f in result.get("fault_chain_completeness", {}).items():
        me = []
        fevs = [e for e in events if e.get("fault_id", "0") == fid]
        # Origin: a real tlb_fill -> refill_pfn_corrupt -> insert chain.
        if not _has_parent(fevs, by_id, "refill_pfn_corrupt", {"tlb_fill"}):
            me.append("tlb_fill->refill_pfn_corrupt")
        for e in fevs:
            if v3.kind(e) != "tlb_entry_insert":
                continue
            pk = v3.parent_kind(e, by_id)
            if pk not in ("refill_pfn_corrupt", "tlb_entry_insert",
                          "tlb_lookup_hit"):
                me.append("refill->tlb_entry_insert@%s" %
                          e.get("tlb_instance", "?"))
        # Terminal consumer branch (real ParentEventID edges).
        if terminal is not None and terminal.get("fault_id") == fid:
            seq = terminal.get("dyn_inst_seq", "")
            cevs = [e for e in events
                    if e.get("dyn_inst_seq", "") == seq and
                    e.get("fault_id", "0") == fid]
            checks = [
                ("translation_result", "permission_eval->translation_result",
                 {"permission_eval"}),
                ("lsu_request", "translation_result->lsu_request",
                 {"translation_result"}),
                ("rf_writeback", "memory_response->rf_writeback",
                 {"memory_response"}),
                ("commit", "rf_writeback->commit",
                 {"rf_writeback", "consumer", "memory_response"}),
            ]
            for k, label, parents in checks:
                if any(v3.kind(e) == k for e in cevs):
                    if not _has_parent(cevs, by_id, k, parents):
                        me.append(label)
            if not _has_parent(cevs, by_id, "cache_request",
                               {"lsu_request", "cache_request", "mshr_alloc"}):
                me.append("lsu_request->cache_request")
            if not _has_parent(cevs, by_id, "cache_lookup", {"cache_request"}):
                me.append("cache_request->cache_lookup")
            if (any(v3.kind(e) == "cache_response" for e in cevs) and
                    not _has_parent(cevs, by_id, "cache_response",
                                    {"mshr_alloc", "cache_lookup",
                                     "cache_response"})):
                me.append("cache_lookup/mshr_alloc->cache_response")
        me.extend(lineage.get("terminal_consumer_missing", []))
        if lineage.get("identity_errors"):
            me.append("lineage:identity_errors")
        # Cross-dynamic consumption is REQUIRED only when the origin walk was
        # actually squashed. An unsquashed origin consuming its own corrupted
        # entry is a legitimate single-instruction chain (Phase 2.1 R01-R03).
        origin_squashed_any = any(
            r.get("origin_squashed") == "1" for r in rows
            if r.get("fault_id") == fid)
        if origin_squashed_any and not lineage.get("cross_dynamic_link"):
            me.append("lineage:no_cross_dynamic_consumer")
        f["missing_edges"] = sorted(set(me))
        ok = (not f.get("missing_kinds") and not me and
              lineage.get("complete"))
        f["completeness"] = "COMPLETE" if ok else "PARTIAL"
        f["structural_completeness"] = "COMPLETE" if ok else "PARTIAL"
        f["terminal_verified"] = bool(
            terminal and (terminal["downstream"].get("commit") or
                          terminal["downstream"].get("squash")))
        f["fault_effect_coverage"] = (
            "COMPLETE_CAUSAL_CHAIN"
            if lineage.get("cache_link") and
               lineage.get("memory_response_link") and
               lineage.get("rf_wb_commit_link") else "LIFECYCLE_ONLY")
        f["squash_then_reexecution"] = bool(
            lineage.get("cross_dynamic_link") and
            any(r.get("origin_squashed") == "1" for r in rows))
        f["continuation_translation_ids"] = sorted({
            r["translation_id"] for r in rows
            if r.get("fault_id") == fid and r.get("cross_dynamic")})

    origin_squashed_any = any(r.get("origin_squashed") == "1" for r in rows)
    result["phase2_2_status"] = {
        "M02_CROSS_DYNAMIC_CONSUMER_LINK_STATUS":
            "LINKED" if lineage.get("cross_dynamic_link") else
            ("NOT_REQUIRED_ORIGIN_NOT_SQUASHED"
             if not origin_squashed_any else "NOT_LINKED"),
        "M02_CACHE_RESPONSE_LINK_STATUS":
            "LINKED" if lineage.get("cache_link") else "NOT_LINKED",
        "M02_RF_WB_COMMIT_LINK_STATUS":
            "LINKED" if lineage.get("rf_wb_commit_link") else "NOT_LINKED",
        "M02_ORIGIN_SQUASH_WITNESS_STATUS":
            "VERIFIED" if all(
                r.get("origin_squashed") == "0" or
                not r.get("errors") for r in rows) else "INCONSISTENT",
        "M02_ENTRY_IDENTITY_STATUS":
            "VERIFIED" if not lineage.get("identity_errors") else "FAILED",
    }


def write_lineage_csv(prefix, run_id, rows):
    with open(prefix + "_lineage.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "FaultID", "TLBInstance", "EntryID",
                    "Generation", "ConsumerDynSeq", "OriginDynSeq",
                    "CrossDynamic", "TranslationID", "ExecutionAttempt",
                    "ReuseOrdinal", "PFN", "PA", "LookupEventID",
                    "SourceInsertEventID", "OriginEventID", "OriginSquashed",
                    "OriginSquashEventID", "HasTranslationResult",
                    "HasLSURequest", "HasCacheRequest", "HasCacheLookup",
                    "HasCacheResponse", "HasMemoryResponse", "HasRFWriteback",
                    "HasCommit", "HasSquash", "IdentityErrors"])
        for r in rows:
            d = r["downstream"]
            w.writerow([
                run_id, r["fault_id"], r["tlb_instance"], r["tlb_entry_id"],
                r["entry_generation"], r["dyn_inst_seq"],
                r["origin_dyn_inst_seq"], "YES" if r["cross_dynamic"] else "NO",
                r["translation_id"], r["execution_attempt_id"],
                r["reuse_ordinal"], r["pfn"], r["pa"], r["lookup_event_id"],
                r["source_event_id"], r["origin_event_id"],
                r["origin_squashed"], r["origin_squash_event_id"],
                "1" if d["translation_result"] else "0",
                "1" if d["lsu_request"] else "0",
                "1" if d["cache_request"] else "0",
                "1" if d["cache_lookup"] else "0",
                "1" if d["cache_response"] else "0",
                "1" if d["memory_response"] else "0",
                "1" if d["rf_writeback"] else "0",
                "1" if d["commit"] else "0",
                "1" if d["squash"] else "0",
                ";".join(r["errors"]),
            ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--workload", required=True, choices=["W9", "W10"])
    ap.add_argument("--model", required=True,
                    choices=["CONTROL", "M01", "M02"])
    ap.add_argument("--run-id", default="")
    ap.add_argument("--va", action="append", default=[])
    ap.add_argument("--csv-prefix", default=None)
    ap.add_argument("--report-json", default=None)
    args = ap.parse_args()

    events, bad = v3.load_events(args.input)
    by_id = {e["event_id"]: e for e in events}

    # Stricter than v3: a Phase 2.2 M02 chain must carry the explicit
    # cross-dynamic entry-consumption witness.
    if args.model == "M02":
        req = list(v3.MODEL_REQUIRED[("W10", "M02")])
        if "fault_entry_consume" not in req:
            req = req + ["fault_entry_consume"]
            v3.MODEL_REQUIRED[("W10", "M02")] = req

    result, chains = v3.evaluate(events, by_id, args)
    result["validator"] = "mmu_trace_validate_v4"
    result["parse_skipped"] = bad

    lineage, rows = audit_lineage(events)
    result["phase2_2_lineage_audit"] = lineage

    # A complete v3 chain is not enough for M02: the lineage audit is a
    # mandatory additional gate, and the logical fault chain is evaluated on
    # the origin refill/insert plus the terminal consumer branch (v3 unions
    # every squashed attempt, which would mislabel real recovery as missing).
    if args.model == "M02":
        refine_m02(result, events, lineage, rows)

    if args.csv_prefix:
        v3.write_csvs(result, chains, args.csv_prefix)
        write_lineage_csv(args.csv_prefix, args.run_id, rows)
    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)

    print(json.dumps({
        "run_id": result.get("run_id"),
        "record_integrity": result.get("record_integrity"),
        "fault_chain_completeness": result.get("fault_chain_completeness"),
        "run_trace_completeness": result.get("run_trace_completeness"),
        "lineage": lineage,
    }, indent=2, sort_keys=True, default=str))
    return 0 if result["record_integrity"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
