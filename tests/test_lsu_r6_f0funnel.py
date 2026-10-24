#!/usr/bin/env python3
"""[R6-F0FUNNEL] F0 legacy 纯观测漏斗：attempted/eligible 计数只观测不决策、顺序在 cap+probability 之后、events_to_skip 之前；injected 用真实 faults_injected_count；摘要行与三个工具解析器兼容。

用法：python3 tests/test_lsu_r6_f0funnel.py   （exit 0=全 PASS）
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
    tlb = _src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc")
    tlbhh = _src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh")

    print("[B1] 源码守卫：F0 legacy 注册 exit 摘要（lsuTrigger 的 else 分支）")
    check("存在 legacy exit callback",
          "printLegacyFunnelSummary()" in tlb and "} else {" in tlb, "")
    check("printLegacyFunnelSummary 已定义并声明",
          "CHAOSArmTLB::printLegacyFunnelSummary() const" in tlb
          and "printLegacyFunnelSummary() const;" in tlbhh, "")

    print("[B2] 源码守卫：计数在 cap + probability 之后、events_to_skip 之前")
    i_cap = tlb.find("faults_injected_count >= max_faults) return;")
    i_leg = tlb.find("++legacy_attempted;")
    i_prob = tlb.find("if (probDist(rng) > probability) return;")
    i_el = tlb.find("++legacy_eligible;")
    i_skip = tlb.find("if (events_to_skip > 0)")
    check("顺序 attempted < cap < prob < eligible < skip",
          -1 < i_leg < i_cap < i_prob < i_el < i_skip,
          "%s %s %s %s %s" % (i_leg, i_cap, i_prob, i_el, i_skip))
    check("计数语句是纯自增（无 RNG/skip/cap 参与）",
          "++legacy_attempted;" in tlb and "++legacy_eligible;" in tlb, "")

    print("[B3] 摘要行可被三个解析器识别")
    line = ("CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=301 "
            "eligible=2 injected=1 first_eligible_tick=237950940537 "
            "last_eligible_tick=237950940537 (activated=W3-L0-layer)")
    check("campaign _armtlb_trigger_counts 解析出 (301,2,1)",
          LC._armtlb_trigger_counts(line) == (301, 2, 1),
          str(LC._armtlb_trigger_counts(line)))
    m = re.search(r"CHAOS_LSU_TRIGGER: .*?attempted=(\d+) eligible=(\d+) "
                  r"injected=(\d+)", line)
    check("lsu_l5_classify 同款正则命中", bool(m), "")
    import lsu_obs_core as OBS
    check("lsu_obs_core 同款正则命中", bool(OBS._FUNNEL_RE.search(line)), "")

    print("[B4] F0 三源一致：log/trigger/stats 无矛盾，injected 与日志一致")
    d = Path(tempfile.mkdtemp(prefix="f0src-"))
    (d / "armtlb_injections.log").write_text(
        "    protection: model=none bits=1 -> Raw\n"
        "Tick: 237950940537, Site: arm_tlb_lookup_hit, "
        "VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x100000000081d75, "
        "FaultType: bit_flip, Mask=0x1\n")
    (d / "stats.txt").write_text(
        "board.chaos_armtlb.numFaultsInjected                1"
        "                       # Total TLB-entry faults injected (Count)\n")
    s = LC.armtlb_count_sources(d, line)
    check("log == 1", s["log"] == 1, str(s["log"]))
    check("trigger == 1", s["trigger"] == 1, str(s["trigger"]))
    check("stats == 1", s["stats"] == 1, str(s["stats"]))
    check("contradiction is False", s["contradiction"] is False, s["detail"])
    check("attempted/eligible 由 F0 摘要提供（非 None）",
          s["attempted"] == 301 and s["eligible"] == 2,
          "%s/%s" % (s["attempted"], s["eligible"]))

    print("[B5] injected 用的是真实 faults_injected_count（非镜像副本）")
    parts = tlb.split("CHAOSArmTLB::printLegacyFunnelSummary() const")
    blk = parts[1][:900] if len(parts) > 1 else ""
    check("摘要打印 faults_injected_count",
          "faults_injected_count" in blk, "printLegacyFunnelSummary 未定义")
    check("头文件无 legacy_injected 镜像成员",
          "legacy_injected" not in tlbhh, "")

    print()
    if FAILED:
        print("FAILED (%d): %s" % (len(FAILED), FAILED))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
