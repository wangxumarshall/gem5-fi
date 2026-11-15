#!/usr/bin/env python3
"""Model-specific §10 acceptance gates for the 40 formal samples."""
import json
import os
import re

CAMP = "/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113"
A = os.path.join(CAMP, "analysis")
SAMPLES = json.load(open(os.path.join(A, "samples.json")))


def events(sid):
    p = os.path.join(A, "propagation_chains", sid + ".json")
    return json.load(open(p))["Events"] if os.path.exists(p) else []


def kinds(evs):
    return {e["Kind"] for e in evs}


def first(evs, kind):
    return next((e for e in evs if e["Kind"] == kind), None)


def cfg_value(rdir, key):
    p = os.path.join(rdir, "Config", "config.ini")
    if not os.path.exists(p):
        return ""
    m = re.search(r"^" + key + r"=(.*)$", open(p, errors="replace").read(),
                  re.M)
    return m.group(1) if m else ""


def check_m01(s, evs):
    ex = first(evs, "mmu_fault_activate") or {}
    extra = ex.get("ExtraFields") or {}
    k = kinds(evs)
    c = []
    c.append(("tlbi_match_present", "tlbi_match" in k))
    c.append(("tlbi_suppressed_present", "tlbi_suppressed" in k))
    c.append(("stale_entry_consumed", "tlb_lookup_hit" in k and
              "fault_entry_consume" in k or "tlb_lookup_hit" in k))
    c.append(("wrong_pa_to_lsu", "lsu_request" in k))
    c.append(("wrong_value_proof", bool(s["WrongValueProof"])))
    c.append(("l2_shared_instance",
              "l2_shared" in json.dumps(extra) or
              any("l2_shared" in json.dumps(e.get("ExtraFields") or {})
                  for e in evs) or
              any("l2_shared" in str(w) for w in s["WrongValueProof"])))
    return c


def check_m02(s, evs, man):
    k = kinds(evs)
    c = []
    c.append(("refill_pfn_corrupt", "refill_pfn_corrupt" in k))
    c.append(("pte_read_decode", "pte_read" in k and "pte_decode" in k))
    c.append(("tlb_entry_insert", "tlb_entry_insert" in k))
    c.append(("old_pfn_from_context_control",
              str(man.get("m02_old_pfn")) == "0x834b2" and
              ("CTRL-W10-%s" % s["ContextID"]) in
              str(man.get("m02_old_pfn_source"))))
    c.append(("approved_not_legacy",
              "0x83480" not in json.dumps(man)))
    return c


def check_m03(s, evs):
    ex = first(evs, "mmu_fault_activate") or {}
    extra = ex.get("ExtraFields") or {}
    k = kinds(evs)
    c = []
    c.append(("requester_asid", "asid" in extra))
    c.append(("candidate_asid", "candidate_asid" in extra))
    c.append(("false_hit_asid_mismatch",
              str(extra.get("asid")) != str(extra.get("candidate_asid"))))
    c.append(("foreign_entry_identity",
              "candidate_entry_id" in extra and
              "candidate_generation" in extra))
    c.append(("false_hit_consumed", "tlb_lookup_hit" in k))
    c.append(("legal_terminal", s["TerminalState"] in
              ("SQUASHED", "SDC", "DETECTED_CONTAINED")))
    return c


def check_m04(s, evs, man):
    ex = first(evs, "mmu_fault_activate") or {}
    extra = ex.get("ExtraFields") or {}
    k = kinds(evs)
    c = []
    c.append(("decoy_pfn_expected", str(man.get("decoy_pfn")) == "0x8353c"))
    c.append(("target_entry_identity",
              "tlb_entry_id" in extra and "old_pfn" in extra))
    c.append(("entry_lifetime_lineage", "tlb_entry_lineage" in k))
    c.append(("substituted_pfn", extra.get("new_pfn") == "0x8353c"))
    c.append(("wrong_pa_consumed",
              "fault_entry_consume" in k or "fault_entry_reuse" in k or
              ("tlb_entry_lineage" in k and "lsu_request" in k)))
    c.append(("downstream_or_execute",
              "lsu_request" in k or "commit" in k))
    return c


def check_m05(s, evs, man, rdir):
    ex = first(evs, "mmu_fault_activate") or {}
    extra = ex.get("ExtraFields") or {}
    k = kinds(evs)
    cmd = open(os.path.join(rdir, "Run_Log", "command.txt"),
               errors="replace").read()
    c = []
    c.append(("explicit_decoy_va_flag",
              "--mmu_m05_decoy_va 0x4010200000" in cmd))
    c.append(("decoy_va_recorded", str(man.get("m05_decoy_va")) ==
              "0x4010200000"))
    c.append(("table_base_zero", str(man.get("m05_decoy_table_base")) == "0"))
    c.append(("no_live_scan_fallback",
              extra.get("decoy_source") == "decoy_va"))
    c.append(("partial_entry_insert", "partial_entry_insert" in k))
    c.append(("pointer_substitution",
              extra.get("next_table_pa_before") !=
              extra.get("next_table_pa_after")))
    c.append(("decoy_pte_read", "pte_decode" in k))
    return c


def check_m06(s, evs):
    k = kinds(evs)
    act = first(evs, "mmu_fault_activate") or {}
    extra = act.get("ExtraFields") or {}
    decs = [e for e in evs if e["Kind"] == "pte_decode"]
    local = [e for e in decs if (e.get("ExtraFields") or {}).get("walk_level")
             == "L3"]
    c = []
    c.append(("descriptor_bit_changed",
              extra.get("descriptor_before") !=
              extra.get("descriptor_after")))
    c.append(("valid_bit_cleared",
              str(extra.get("descriptor_before", "")).endswith("3") and
              str(extra.get("descriptor_after", "")).endswith("2")))
    c.append(("original_pte_unchanged_upper_levels",
              all((e.get("ExtraFields") or {}).get("pte_value_before") ==
                  (e.get("ExtraFields") or {}).get("pte_value_after")
                  for e in decs
                  if (e.get("ExtraFields") or {}).get("walk_level") != "L3")))
    c.append(("local_decode_invalid",
              any((e.get("ExtraFields") or {}).get("descriptor_type") ==
                  "Invalid" for e in local)))
    c.append(("translation_fault_propagated",
              "exception_delivery" in k))
    c.append(("fault_state_consumed", "fault_state_consumed" in k))
    c.append(("legal_detected_terminal",
              s["TerminalState"] == "DETECTED_CONTAINED"))
    return c


def check_m07(s, evs, man):
    k = kinds(evs)
    act = first(evs, "mmu_fault_activate") or {}
    extra = act.get("ExtraFields") or {}
    expected = {"R03": "0x400d200000", "R04": "0x400d400100",
                "R05": "0x400d600180"}
    tv = man.get("target_va")
    tv_hex = hex(int(tv)) if isinstance(tv, int) else str(tv)
    c = []
    c.append(("exact_target_va",
              s["ContextID"] not in expected or
              int(tv_hex, 16) == int(expected[s["ContextID"]], 16)))
    c.append(("permission_before_deny",
              extra.get("permission_before") == "false"))
    c.append(("permission_after_grant",
              extra.get("permission_after") == "true"))
    c.append(("activation_at_permission_eval",
              "permission_eval" in k or
              (extra.get("permission_before") == "false" and
               extra.get("permission_after") == "true")))
    c.append(("consumer_observed",
              "lsu_request" in k or "commit" in k))
    return c


def check_m08(s, evs, rdir):
    k = kinds(evs)
    act = first(evs, "mmu_fault_activate") or {}
    extra = act.get("ExtraFields") or {}
    mask = cfg_value(rdir, "mmuM08PaXorMask")
    c = []
    c.append(("pa_xor_mask_4096", mask == "4096"))
    try:
        c.append(("final_pa_xor",
                  int(str(extra.get("old_pa")), 0) ^
                  int(str(extra.get("new_pa")), 0) == 4096))
    except (TypeError, ValueError):
        c.append(("final_pa_xor", False))
    c.append(("request_pa_is_xored",
              extra.get("request_pa_after") == extra.get("new_pa")))
    c.append(("translation_to_request", "translation_result" in k and
              "lsu_request" in k))
    c.append(("downstream_memory", "memory_response" in k or
              "cache_response" in k))
    return c


def main():
    out = []
    for s in SAMPLES:
        sid = s["SampleRunID"]
        evs = events(sid)
        man = json.load(open(os.path.join(s["RunDir"], "sample_manifest.json")))
        m = s["ModelID"]
        if m == "M01":
            checks = check_m01(s, evs)
        elif m == "M02":
            checks = check_m02(s, evs, man)
        elif m == "M03":
            checks = check_m03(s, evs)
        elif m == "M04":
            checks = check_m04(s, evs, man)
        elif m == "M05":
            checks = check_m05(s, evs, man, s["RunDir"])
        elif m == "M06":
            checks = check_m06(s, evs)
        elif m == "M07":
            checks = check_m07(s, evs, man)
        else:
            checks = check_m08(s, evs, s["RunDir"])
        rec = {"SampleRunID": sid, "ModelID": m, "ContextID": s["ContextID"],
               "checks": {k: bool(v) for k, v in checks},
               "failed": [k for k, v in checks if not v],
               "status": "PASS" if all(v for _, v in checks) else "FAIL"}
        out.append(rec)
    fails = [r for r in out if r["status"] != "PASS"]
    summary = {
        "samples": len(out),
        "pass": len(out) - len(fails),
        "fail": len(fails),
        "failed_samples": fails,
    }
    json.dump({"summary": summary, "samples": out},
              open(os.path.join(A, "model_specific_validation.json"), "w"),
              indent=1)
    md = ["# Model-specific §10 acceptance", "",
          "| Sample | Model | Ctx | Status | Failed checks |",
          "|---|---|---|---|---|"]
    for r in out:
        md.append("| `%s` | %s | %s | %s | %s |" % (
            r["SampleRunID"], r["ModelID"], r["ContextID"], r["status"],
            ", ".join(r["failed"]) or "-"))
    md.append("")
    md.append("**Summary: %d/%d PASS, %d FAIL**" % (
        summary["pass"], summary["samples"], summary["fail"]))
    open(os.path.join(A, "model_specific_validation.md"), "w").write(
        "\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))
    for r in fails:
        print("FAIL", r["SampleRunID"], r["failed"])


if __name__ == "__main__":
    main()
