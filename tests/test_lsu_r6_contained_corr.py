#!/usr/bin/env python3
"""[R6-FIXCORR] T01 真实 L2 含住的终局 corr 契约（chaos_tlb_chain_containment 的姊妹契约）：contained 且 pending.corr 为空时终局事件写 corr=origin，不重开 arm、不放宽 grader、不制造 L2→L3/L4/L5 伪传播。

用法：python3 tests/test_lsu_r6_contained_corr.py   （exit 0=全 PASS）
"""
import gzip
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as PF        # noqa: E402
import lsu_chain_check as C         # noqa: E402
import lsu_campaign as LC           # noqa: E402

FAILED = []

# --- T01-F0-W4/seed1 的真实 PROP-EVT 流（逐字节复制；测试显式改写 corr）---
VERBATIM = '''# prop-evt v1: kind run_id sample_run_id fault_id event_id parent_event_id tick cycle core_id thread_id dyn_inst_seq store_dyn_inst_seq commit_seq pc opcode lq_idx sq_idx request_id walk_id mshr_id fill_id pf_request_id va pa cache_line set way entry_index field before after state_before state_after arch_reg phys_reg detection_layer contained outcome oracle_diff evidence_status corr containment_layer containment_reason old_request_id new_request_id source_event_id dest_event_id bridge_layer bridge_reason shared_addr shared_size
PROP-EVT: kind=inj run_id=T01-F0-W4 sample_run_id=s1 fault_id=1 event_id=0 parent_event_id= tick=237950940537 cycle=714567389 core_id=0 thread_id= dyn_inst_seq=301 store_dyn_inst_seq= commit_seq= pc= opcode= lq_idx= sq_idx= request_id=301 walk_id= mshr_id= fill_id= pf_request_id= va=ffffffc009483fa8 pa= cache_line= set= way= entry_index= field=bit_flip before=81d75 after=100000000081d75 state_before= state_after= arch_reg= phys_reg= detection_layer= contained= outcome= oracle_diff= evidence_status=observed corr=origin containment_layer= containment_reason= old_request_id= new_request_id= source_event_id= dest_event_id= bridge_layer= bridge_reason= shared_addr= shared_size=
PROP-EVT: kind=tlb_lookup run_id=T01-F0-W4 sample_run_id=s1 fault_id=1 event_id=1 parent_event_id=0 tick=237950940537 cycle=714567389 core_id=0 thread_id= dyn_inst_seq=301 store_dyn_inst_seq= commit_seq= pc= opcode= lq_idx= sq_idx= request_id=301 walk_id=0 mshr_id= fill_id= pf_request_id= va=ffffffc009483fa8 pa= cache_line= set= way=-1 entry_index=0 field=post_lookup before=81d75 after=100000000081d75 state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 arch_reg= phys_reg= detection_layer= contained= outcome= oracle_diff= evidence_status=observed corr= containment_layer= containment_reason= old_request_id= new_request_id= source_event_id= dest_event_id= bridge_layer= bridge_reason= shared_addr= shared_size=
PROP-EVT: kind=tlb_pfn run_id=T01-F0-W4 sample_run_id=s1 fault_id=1 event_id=2 parent_event_id=1 tick=237950940537 cycle=714567389 core_id=0 thread_id= dyn_inst_seq=301 store_dyn_inst_seq= commit_seq= pc= opcode= lq_idx= sq_idx= request_id=301 walk_id= mshr_id= fill_id= pf_request_id= va=ffffffc009483fa8 pa=81d75fa8 cache_line= set= way= entry_index= field=bit_flip before=81d75 after=100000000081d75 state_before=81d75fa8 state_after=81d75fa8 arch_reg= phys_reg= detection_layer= contained= outcome= oracle_diff= evidence_status=observed corr= containment_layer= containment_reason= old_request_id= new_request_id= source_event_id= dest_event_id= bridge_layer= bridge_reason= shared_addr= shared_size=
PROP-EVT: kind=tlb_translate_result run_id=T01-F0-W4 sample_run_id=s1 fault_id=1 event_id=3 parent_event_id=2 tick=237950940537 cycle=714567389 core_id=0 thread_id= dyn_inst_seq=301 store_dyn_inst_seq= commit_seq= pc= opcode= lq_idx= sq_idx= request_id=301 walk_id=0 mshr_id= fill_id= pf_request_id= va=ffffffc009483fa8 pa=81d75fa8 cache_line= set= way=-1 entry_index=0 field=effective_pa_unchanged before=81d75fa8 after=81d75fa8 state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 arch_reg= phys_reg= detection_layer=L2 contained=1 outcome=NoFault oracle_diff= evidence_status=observed corr= containment_layer=L2 containment_reason=effective_pa_unchanged old_request_id= new_request_id= source_event_id= dest_event_id= bridge_layer= bridge_reason= shared_addr= shared_size=
PROP-EVT: kind=chain_end run_id=T01-F0-W4 sample_run_id=s1 fault_id=1 event_id=4 parent_event_id=3 tick=314515193310 cycle=944490070 core_id=0 thread_id= dyn_inst_seq= store_dyn_inst_seq= commit_seq= pc= opcode= lq_idx= sq_idx= request_id= walk_id= mshr_id= fill_id= pf_request_id= va= pa= cache_line= set= way= entry_index= field= before= after= state_before= state_after= arch_reg= phys_reg= detection_layer=L2 contained=1 outcome=detected_contained oracle_diff= evidence_status=observed corr=none containment_layer=L2 containment_reason=effective_pa_unchanged old_request_id= new_request_id= source_event_id= dest_event_id= bridge_layer= bridge_reason= shared_addr= shared_size=
'''


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _write(text):
    p = Path(tempfile.mkdtemp(prefix="r6-")) / "prop_evt.txt.gz"
    with gzip.open(p, "wt") as f:
        f.write(text)
    return p


def _with_origin(text):
    out, n = [], 0
    for ln in text.splitlines(True):
        if (ln.startswith("PROP-EVT:") and "kind=tlb_translate_result" in ln
                and " corr= containment_layer=" in ln):
            ln = ln.replace(" corr= containment_layer=",
                            " corr=origin containment_layer=")
            n += 1
        out.append(ln)
    assert n == 1, "expected exactly one rewrite"
    return "".join(out)


def _gate(text, oracle="Masked"):
    p = _write(text)
    ev, tr, su, iss = PF.read_stream(p)
    acct = C.consumer_summary_accounting(su, iss)
    return LC.admission_gate("T01-F0-W4", ev, 1, oracle, 0,
                             summary_issues=iss,
                             consumer_summary_accounting=acct), ev


def _src(rel):
    return (ROOT / rel).read_text(errors="replace")

def main():
    prop = _src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc")

    print("[A1] 源码守卫：contained 且 corr 空时才改用 CORR_ORIGIN（条件式）")
    check("noteTlbTranslationResult 含条件式 evt_corr",
          "evt_corr" in prop and "contained && pending.corr.empty()" in prop,
          "未找到条件式 corr 规则")
    check("终局事件改用 evt_corr",
          '{"corr", evt_corr},' in prop, "终局事件未使用 evt_corr")

    print("[A2] 语义：corr=origin 的 contained 终局 → detected_contained 且准入")
    g, _ = _gate(_with_origin(VERBATIM))
    check("terminal == detected_contained",
          g.get("terminal") == "detected_contained", str(g.get("terminal")))
    check("path == contained", g.get("path") == "contained", str(g.get("path")))
    check("admitted is True", g.get("admitted") is True, str(g.get("admitted")))
    check("violations == []", (g.get("violations") or []) == [],
          str(g.get("violations")))

    print("[A3] 不制造伪传播：L2→L3/L3→L4/L4→L5 仍为 missing")
    ev, tr, su, iss = PF.read_stream(_write(_with_origin(VERBATIM)))
    v = C.check_chain(ev, oracle_outcome="Masked")
    f = list(v["faults"].values())[0]
    edges = {k: val for k, val in (f.get("edges") or {}).items()
             if not k.endswith("_witness")}
    check("L2->L3 missing", edges.get("L2->L3") == "missing", str(edges))
    check("L4->L5 missing", edges.get("L4->L5") == "missing", str(edges))
    check("beyond 关闭（==''）", f.get("beyond") == "", repr(f.get("beyond")))

    print("[A4] 负对照：未改 corr 的同一条流仍不被准入（测试有鉴别力）")
    g0, _ = _gate(VERBATIM)
    check("original terminal == provable_to_L2_then_unknown",
          g0.get("terminal") == "provable_to_L2_then_unknown",
          str(g0.get("terminal")))
    check("original admitted is False", g0.get("admitted") is False,
          str(g0.get("admitted")))
    check("original violations 非空", bool(g0.get("violations")), "")

    print("[A5] chain_end 仍不能充当终局证据")
    cont = C.containment_from_events(ev, "T01-F0-W4", truncated=False)
    check("含住束的非空来源不是 chain_end",
          bool(cont) and "chain_end" not in str(cont.get("reason", "")),
          str(cont and cont.get("reason")))
    check("chain_end 的 corr 仍为 none（生命周期）",
          " corr=none containment_layer=" in VERBATIM, "")

    print()
    if FAILED:
        print("FAILED (%d): %s" % (len(FAILED), FAILED))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
