#!/usr/bin/env python3
"""test_lsu_hook_lsqfwd.py — [MDSPEC][R4-1] lsq_fwd 事件契约测试。

规格（任务 R4-1 brief 1.3/1.4 + 用户裁决 2026-10-20）：
"把生产 store 的 dyn_inst_seq/sq_idx/request_id 与消费 load 的
dyn_inst_seq/lq_idx/request_id 传入 CHAOSLSQFwd；lsq_fwd 事件必录字段加入
store_dyn_inst_seq/sq_idx/lq_idx/request_id；移除仅地址关联路径
（或标注为 fallback 并记录）"

契约：
- kind=lsq_fwd → L3（转发数据被污染，S 系转发故障）
- 必录字段（PRIMARY 关联键，裁决 1）：
  dyn_inst_seq（消费 load）、store_dyn_inst_seq（生产 store）、
  sq_idx、lq_idx、request_id + 原有 fault_id/va/field/before/after
- corr 标注（裁决 1 的 fallback 半边）：seq 可得 → corr=seq_primary；
  seq 不可得 → corr=addr_fallback，不得静默走地址关联
- 注册表双源一致（store_dyn_inst_seq / corr 在 C++ 与 Python 注册表中
  同名同序——发射端 unknown-key 丢弃语义要求它们必须是注册字段）
- join 面：lsq_fwd.sq_idx 与 sq_writeback/sq_complete 的 sq_idx 同源
  （DynInst::sqIdx）；lsq_fwd.lq_idx 与 lq_read 的 lq_idx 同源（read()
  的 load_idx 参数）——字段名层面可 1:1 关联

用法：python3 tests/test_lsu_hook_lsqfwd.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def main():
    print("[1] lsq_fwd kind→层级 + 必录字段（PRIMARY 关联键）")
    # [R6-S-FWD 2026-10-30] lsq_fwd is the forward DECISION/TRANSFER (L2);
    # the producer SQ entry is the L1 witness and the forwarded response is
    # L3. The old L3 mapping made L1->L2 structurally unprovable.
    check("sq_entry -> L1", P.KIND_LAYER.get("sq_entry") == "L1",
          str(P.KIND_LAYER.get("sq_entry")))
    check("lsq_fwd -> L2", P.KIND_LAYER.get("lsq_fwd") == "L2",
          str(P.KIND_LAYER.get("lsq_fwd")))
    req = P.REQUIRED_FIELDS.get("lsq_fwd")
    check("lsq_fwd required fields registered", req is not None)
    check("new R4-1 keys required",
          req is not None and all(f in req for f in (
              "store_dyn_inst_seq", "sq_idx", "lq_idx", "request_id")),
          str(req))
    check("load-side seq required (dyn_inst_seq)",
          req is not None and "dyn_inst_seq" in req, str(req))
    check("legacy keys still required",
          req is not None and all(f in req for f in (
              "fault_id", "va", "field", "before", "after")), str(req))

    print("[2] 注册表双源一致（新字段必须进注册表——发射端丢弃 unknown key）")
    hh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
          "CHAOSPropagation.hh").read_text()
    begin = hh.index("PROP_EVT_FIELDS[] = {")
    end = hh.index("};", begin)
    import re
    cpp_fields = re.findall(r'"([a-z_0-9]+)"', hh[begin:end])
    check("store_dyn_inst_seq in both registries",
          "store_dyn_inst_seq" in P.PROP_EVT_FIELDS
          and "store_dyn_inst_seq" in cpp_fields)
    check("corr in both registries",
          "corr" in P.PROP_EVT_FIELDS and "corr" in cpp_fields)
    check("python registry == cpp registry (same name same order)",
          P.PROP_EVT_FIELDS == cpp_fields,
          f"py len={len(P.PROP_EVT_FIELDS)} cpp len={len(cpp_fields)}")

    print("[3] 契约行校验（validate_event）")
    good = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 dyn_inst_seq=207 "
        "store_dyn_inst_seq=133 sq_idx=4 lq_idx=3 request_id=207 "
        "va=7fff12a0 field=bit_flip before=store_data "
        "after=fwd_corrupt:bit_flip corr=seq_primary")
    check("complete seq_primary lsq_fwd validates",
          good is not None and P.validate_event(good) == [],
          str(P.validate_event(good)) if good else "parse None")
    bad = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 va=7fff12a0 field=bit_flip "
        "before=store_data after=fwd_corrupt:bit_flip")
    errs = P.validate_event(bad) if bad else ["parse None"]
    check("missing seq/idx keys flagged (no silent address-only)",
          len(errs) >= 5, str(errs))
    fb = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 dyn_inst_seq=207 "
        "store_dyn_inst_seq=133 sq_idx=4 lq_idx=3 request_id=207 "
        "va=7fff12a0 field=bit_flip before=store_data "
        "after=fwd_corrupt:bit_flip corr=addr_fallback")
    check("addr_fallback marker round-trips",
          fb is not None and fb.get("corr") == "addr_fallback",
          str(fb.get("corr")) if fb else "parse None")

    print("[4] join 面：sq_idx/lq_idx 字段名与 sq_*/lq_read 事件同源")
    sq_wb = P.REQUIRED_FIELDS.get("sq_writeback")
    sq_cp = P.REQUIRED_FIELDS.get("sq_complete")
    lq_rd = P.REQUIRED_FIELDS.get("lq_read")
    check("sq_writeback/sq_complete carry dyn_inst_seq+sq_idx",
          all(r is not None and "dyn_inst_seq" in r and "sq_idx" in r
              for r in (sq_wb, sq_cp)))
    check("lq_read carries dyn_inst_seq+lq_idx",
          lq_rd is not None and "dyn_inst_seq" in lq_rd
          and "lq_idx" in lq_rd)
    # 生产 store 的 sq_writeback/sq_complete 以 store seq 为 dyn_inst_seq，
    # 与 lsq_fwd.store_dyn_inst_seq 同一指令 → 字段面可 join（真机逐边
    # 记录见 docs/gem5-fi/lsu/mdspec/round4_findings.md §1.5）
    chain = [
        P.parse_line("PROP-EVT: kind=inj fault_id=1 event_id=0"),
        good,
        P.parse_line("PROP-EVT: kind=sq_writeback fault_id=1 "
                     "dyn_inst_seq=133 sq_idx=4 event_id=2 corr=seq_primary"),
        P.parse_line("PROP-EVT: kind=sq_complete fault_id=1 "
                     "dyn_inst_seq=133 sq_idx=4 event_id=3 corr=seq_primary"),
    ]
    v = P.provable_to(chain)
    check("inj→lsq_fwd→sq_writeback→sq_complete reaches L3",
          v["provable_to"] == "L3", str(v))

    print("[5] [R4-1-review-I1] corr 必录于一切经 correlate* 加入链的事件")
    corr_kinds = ["lsq_push", "lsq_sendfrag", "tlb_translate", "tlb_fault",
                  "lq_read", "lq_complete", "sq_execute", "sq_writeback",
                  "sq_complete", "atomic_op", "cache_access", "cache_return",
                  "cache_fill", "cache_evict", "mshr_alloc", "mshr_merge",
                  "mshr_fill", "mshr_free", "cache_writeback", "pf_queue",
                  "pf_issue"]
    missing = [k for k in corr_kinds
               if "corr" not in P.REQUIRED_FIELDS.get(k, [])]
    check("corr required on all correlate-joined kinds",
          not missing, str(missing))
    # pf_demand / pf_fill 允许 fault_id=0（仅预取请求链）→ corr 可空，
    # 不得列入必录（列入会把诚实缺席判成违约）
    check("pf_demand/pf_fill corr optional (fault_id=0 allowed)",
          all("corr" not in P.REQUIRED_FIELDS.get(k, [])
              for k in ("pf_demand", "pf_fill")))
    # C++ 面：correlate API 都带 corr_out 出参（调用点不必自行重推导）
    hh2 = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
           "CHAOSPropagation.hh").read_text()
    check("correlateRequest carries corr_out",
          hh2.count("const char **corr_out = nullptr") >= 4)
    check("correlateRequestBySeq carries corr_out",
          hh2.count("const char **corr_out = nullptr") >= 3)
    check("correlateBlock carries corr_out",
          "Addr *base_out = nullptr,\n"
          "                            const char **corr_out" in hh2)
    check("arm labels defined (seq_primary / addr_fallback)",
          'CORR_SEQ_PRIMARY = "seq_primary"' in hh2
          and 'CORR_ADDR_FALLBACK = "addr_fallback"' in hh2)
    # 调用点：每个 correlate 调用都传出 arm 并在事件里带 corr=
    site_files = {
        "CHAOS/gem5/src/cpu/o3/lsq.cc": 3,
        "CHAOS/gem5/src/cpu/o3/lsq_unit.cc": 4,
        "CHAOS/gem5/src/arch/arm/mmu.cc": 2,
        "CHAOS/gem5/src/mem/cache/cache.cc": 4,
        "CHAOS/gem5/src/mem/cache/base.cc": 5,
        "CHAOS/gem5/src/mem/cache/prefetch/queued.cc": 3,
    }
    total_calls = 0
    total_corr = 0
    for rel, expect_calls in site_files.items():
        txt = (ROOT / rel).read_text()
        calls = (txt.count("->correlateRequest(")
                 + txt.count("->correlateRequestBySeq(")
                 + txt.count("->correlateBlock(")
                 + txt.count("->noteMemRequest("))
        # 注释行里的调用名不算：粗校验调用数 >= 预期（唯一注释场景是
        # CHAOSArmTLB.cc，不在本表）
        corrs = txt.count("_corr = nullptr;   // [R4-1-review-I1]")
        total_calls += calls
        total_corr += corrs
        check(f"{rel.split('/')[-1]}: {expect_calls} call sites plumbed "
              f"(found {corrs} corr decls)", corrs == expect_calls,
              f"calls={calls} corr_decls={corrs}")
    check("no fallback-joined event without marker (21 sites / 23 events)",
          total_corr == 21)

    print("[6] [R4-1-review-I2] 触发器 span 语义 + 双失效模式告警")
    trig = (ROOT / "CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh").read_text()
    check("SPAN_UNREACHABLE alarm mode present",
          "mode=SPAN_UNREACHABLE" in trig
          and "attempted > 0 && injected == 0" in trig)
    check("EARLY_BIAS alarm mode present (silent bias detector)",
          "mode=EARLY_BIAS" in trig and "injected > 0 && eligible >= draw_end"
          in trig)
    check("alarm gated to F0 (span semantics)",
          "if (tier == ChaOSLsuTier::F0)" in trig)
    # 告警消息必须携带 fired_at 并诚实区分两种读法（span 低覆盖 = 真偏置
    # vs 注入故障自身延长流 = 非采样偏置）——不得把故障延长宣称为偏置
    check("EARLY_BIAS message carries fired_at (adjudication key)",
          "fired_at=%lu" in trig and "fired_at = eligible;" in trig)
    check("EARLY_BIAS message names both readings honestly",
          "span under-covers the" in trig
          and "the fault extended the stream" in trig)

    print("[7] [R4-1-review-I2] 每 (模型,负载) span 表 + 未测量对的响亮拒绝")
    camp = (ROOT / "tools/lsu_campaign.py").read_text()
    # [R6-S-REPAIR2 2026-10-30] Re-censused with the campaign's EXACT
    # absolute-path command (guest argv[0] length is timing-visible):
    # S01/S02=6, S08=1, S09=6 (old relative-path readings 7/7/2/7).
    # Evidence: docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md.
    check("LSQFWD_F0_SPAN per-(model,workload) table exists",
          "LSQFWD_F0_SPAN = {" in camp
          and '("S01", "sq_forward"): 6' in camp)
    check("no family-wide lsqfwd span constant remains",
          '"--lsqfwd_span_events", "7"' not in camp)
    check("unmeasured F0 (model,workload) refused loudly",
          "F0-span-unmeasured" in camp)
    check("F0 warmup=1 (true uniform: 1+N over N events)",
          '"--lsqfwd_warmup_events", "1"' in camp)
    check("campaign surfaces CHAOS_LSU_TRIGGER_ALARM in cell summary",
          "CHAOS_LSU_TRIGGER_ALARM" in camp and "ALARM %s" in camp)
    import re as _re
    m = _re.search(r"LSQFWD_F0_SPAN = \{(.*?)\n\}", camp, _re.S)
    entries = {(a, b): c for a, b, c in _re.findall(
        r'\("(S\d\d|L03)", "([a-z_/]+)"\):\s*(\d+)', m.group(1))} if m else {}
    # 每个测量值来自实测 teardown 行（round4_findings.md §R4-1-fix 引用）
    for pair in (("S01", "sq_forward"), ("S02", "sq_forward"),
                 ("S03", "sq_forward"), ("S08", "sq_forward"),
                 ("S09", "sq_forward"), ("L03", "sq_forward"),
                 ("L03", "sqlite_like")):
        check(f"{pair[0]}@{pair[1]} span measured (integer)",
              entries.get(pair) is not None and entries[pair].isdigit(),
              str(entries.get(pair)))
    check("S08's own stream measured (1, not the corrupt-path 7)",
          entries.get(("S08", "sq_forward")) == "1")
    check("L03 stream is workload-dependent (571 vs 18681 measured)",
          entries.get(("L03", "sq_forward")) == "571"
          and entries.get(("L03", "sqlite_like")) == "18681")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
