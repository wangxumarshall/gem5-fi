#!/usr/bin/env python3
"""test_lsu_prop_fields.py — [MDSPEC][H0] 表 11 统一 PROP-EVT 字段解析测试。

规格（主文档 11.传播事件字段规范，24 字段）+ 计划 Task H0：
- 统一事件行 schema：全部注册字段按规范序发射；缺失字段输出空值不省略；
  evidence_status 缺省 observed（规格 11 末行：防止把缺失事件解释为未传播）。
- 发射/解析同源：Python 字段注册表必须与 CHAOSPropagation.hh 的 C++ 注册表
  逐项相等（同名同序）——双源漂移在这里被钉死。
- Unknown 语义（Review Focus #3）：链断于 Ln → provable_to=Ln, beyond=Unknown，
  不得输出 Masked（离线推断禁止）。
用法：python3 tests/test_lsu_prop_fields.py   （退出码 0=全 PASS）
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
    # ---- 1. 发射/解析同源：Python 注册表 == C++ 注册表（同名同序） ----
    print("[1] registry same-source (python == CHAOSPropagation.hh)")
    hh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh").read_text()
    begin = hh.index("PROP_EVT_FIELDS[] = {")
    end = hh.index("};", begin)
    import re
    cpp_fields = re.findall(r'"([a-z_0-9]+)"', hh[begin:end])
    check("cpp registry non-empty", len(cpp_fields) >= 38, f"got {len(cpp_fields)}")
    check("python registry == cpp registry",
          P.PROP_EVT_FIELDS == cpp_fields,
          f"py={P.PROP_EVT_FIELDS[:4]}... cpp={cpp_fields[:4]}...")
    check("registry has all spec-11 mandatory fields",
          all(f in P.PROP_EVT_FIELDS for f in [
              "run_id", "sample_run_id", "fault_id", "event_id",
              "parent_event_id", "tick", "cycle", "core_id", "thread_id",
              "dyn_inst_seq", "commit_seq", "pc", "opcode", "lq_idx", "sq_idx",
              "request_id", "walk_id", "mshr_id", "fill_id", "pf_request_id",
              "va", "pa", "cache_line", "set", "way", "entry_index", "field",
              "before", "after", "state_before", "state_after", "arch_reg",
              "phys_reg", "detection_layer", "contained", "outcome",
              "oracle_diff", "evidence_status"]))

    # ---- 2. 全字段行逐项还原 ----
    print("[2] full-field line roundtrip")
    vals = {f: f"v_{f}" for f in P.PROP_EVT_FIELDS}
    line = "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in vals.items())
    evt = P.parse_line(line)
    check("parsed non-None", evt is not None)
    check("every field restored", all(evt.get(f) == vals[f] for f in P.PROP_EVT_FIELDS),
          str({f: evt.get(f) for f in P.PROP_EVT_FIELDS if evt.get(f) != vals[f]}))
    check("non-prop line rejected", P.parse_line("random log line") is None)

    # ---- 3. 缺字段行 → 空值；evidence_status 语义缺省 ----
    print("[3] missing fields -> empty values, evidence default observed")
    partial = "PROP-EVT: kind=inj event_id=0 fault_id=1 tick=100 dyn_inst_seq=42"
    evt2 = P.parse_line(partial)
    check("present fields parsed",
          evt2["kind"] == "inj" and evt2["event_id"] == "0"
          and evt2["dyn_inst_seq"] == "42")
    check("absent fields -> empty string",
          evt2.get("pc", "X") == "" and evt2.get("va", "X") == ""
          and evt2.get("walk_id", "X") == "")
    check("evidence_status absent -> default observed",
          P.evidence_status_of(evt2) == "observed")
    check("evidence_status explicit preserved",
          P.evidence_status_of({"evidence_status": "missing"}) == "missing")

    # ---- 4. 链断裂 → Unknown（不得 Masked）----
    print("[4] chain break -> provable_to + beyond=Unknown (never Masked)")
    chain = [
        P.parse_line("PROP-EVT: kind=inj event_id=0 fault_id=1 tick=10 "
                     "detection_layer="),
        P.parse_line("PROP-EVT: kind=mem_req event_id=1 parent_event_id=0 "
                     "fault_id=1 tick=20"),
    ]
    verdict = P.provable_to(chain)
    check("provable_to == L2", verdict["provable_to"] == "L2", str(verdict))
    check("beyond == Unknown", verdict["beyond"] == "Unknown", str(verdict))
    check("never Masked", "Masked" not in str(verdict))
    # 全链：inj(L0) addr_form(L1) mem_req(L2) resp(L3) taint_reg/consumer(L4)
    #       errant_commit(L4)
    full = [P.parse_line("PROP-EVT: kind=%s event_id=%d fault_id=1" % (k, i))
            for i, k in enumerate(["inj", "addr_form", "mem_req", "resp",
                                   "taint_reg", "consumer", "errant_commit"])]
    v2 = P.provable_to(full)
    check("full chain provable_to == L4", v2["provable_to"] == "L4", str(v2))
    # 空链（无事件）→ 诚实 L0 都不可证
    v3 = P.provable_to([])
    check("empty chain -> provable_to None/before-L0",
          v3["provable_to"] in (None, "", "none"), str(v3))
    check("empty chain beyond Unknown", v3["beyond"] == "Unknown", str(v3))

    # ---- 5. read_events：gz/普通文件 + 截断容错 ----
    print("[5] read_events file ingestion (plain + truncated gz)")
    import gzip
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        plain = Path(td) / "prop_evt.txt"
        plain.write_text(line + "\n" + partial + "\n")
        evts, trunc = P.read_events(plain)
        check("plain file 2 events", len(evts) == 2 and not trunc)
        gzp = Path(td) / "prop_evt.txt.gz"
        # 剥掉 gzip trailer（CRC32+ISIZE 共 8 字节）= 模拟 abort 后的
        # Z_SYNC_FLUSH 截断流（v1 契约：前缀可救、截断必须标记）
        gzp.write_bytes(gzip.compress((line + "\n").encode())[:-8])
        evts2, trunc2 = P.read_events(gzp)
        check("truncated gz salvaged + flagged",
              trunc2 is True and len(evts2) >= 1,
              f"trunc={trunc2} n={len(evts2)}")

    # ---- 6. [R4-4-review-I1] corr 全事件覆盖契约 ------------------------
    # 评审 Important-1：writeNode 双发事件（resp/taint_reg/consumer/
    # errant_commit/inj/addr_form/mem_req）与 chain_end 曾带 corr=''——
    # 地址臂入链的事件与无标注不可区分。契约：corr 必录；无 join 时用
    # origin/taint_prop/none 显式说明，绝不静默留空。
    print("[6] [R4-4-review-I1] corr coverage contract (all chain events)")
    check("CORR_VALUES vocabulary pinned",
          P.CORR_VALUES == {"seq_primary", "addr_fallback", "origin",
                            "taint_prop", "none"},
          str(P.CORR_VALUES))
    # 发射端同源：C++ 常量必须全部在场（防词汇表漂移）
    src = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation"
           / "CHAOSPropagation.hh").read_text()
    for c in ("CORR_SEQ_PRIMARY", "CORR_ADDR_FALLBACK", "CORR_ORIGIN",
              "CORR_TAINT_PROP", "CORR_NONE"):
        check(f".hh defines {c}", f"{c} =" in src)
    cc = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation"
          / "CHAOSPropagation.cc").read_text()
    check("writeNode dual-emit writes f[\"corr\"]",
          'f["corr"] = corr ? corr : ""' in cc)
    check("dual-emit nullptr corr warns (never silent)",
          "evt_corr_missing_warned" in cc)
    check("consumer/errant_commit labeled taint_prop",
          cc.count("CORR_TAINT_PROP") >= 2)
    # 必录字段：v1 writeNode 双发族 + chain_end 全部含 corr
    v1_kinds = {
        "inj": ["fault_id", "corr"],
        "addr_form": ["fault_id", "corr", "va"],
        "mem_req": ["fault_id", "corr", "dyn_inst_seq", "va"],
        "resp": ["fault_id", "corr", "dyn_inst_seq"],
        "taint_reg": ["fault_id", "corr", "dyn_inst_seq", "phys_reg",
                      "arch_reg"],
        "consumer": ["fault_id", "corr", "dyn_inst_seq", "phys_reg",
                     "arch_reg"],
        "errant_commit": ["fault_id", "corr", "dyn_inst_seq"],
        "chain_end": ["fault_id", "outcome", "detection_layer", "contained",
                      "corr"],
    }
    for kind, fields in v1_kinds.items():
        req = P.REQUIRED_FIELDS.get(kind)
        check(f"{kind} required fields include corr",
              req is not None and all(f in req for f in fields), str(req))
    # 契约行校验：mask40 形状的地址臂链（每事件显式来源）
    good_lines = [
        # 链开启（无 join）→ origin
        "PROP-EVT: kind=inj fault_id=1 corr=origin dyn_inst_seq=301",
        "PROP-EVT: kind=addr_form fault_id=1 corr=origin va=81d35fa8",
        # 载体 store 按 seq 主臂入链 → seq_primary
        "PROP-EVT: kind=mem_req fault_id=1 corr=seq_primary "
        "dyn_inst_seq=301 va=ffffffc009483fa8",
        # 错误 PA 页上的无关流量按地址臂入链 → addr_fallback（评审核心：
        # 此前这些事件 corr=''，与 seq 入链不可区分）
        "PROP-EVT: kind=resp fault_id=1 corr=addr_fallback dyn_inst_seq=303",
        "PROP-EVT: kind=taint_reg fault_id=1 corr=addr_fallback "
        "dyn_inst_seq=303 phys_reg=10 arch_reg=5",
        # 污染集传播（commit 侧，无 correlate 查询）→ taint_prop
        "PROP-EVT: kind=consumer fault_id=1 corr=taint_prop "
        "dyn_inst_seq=391 phys_reg=10 arch_reg=5",
        "PROP-EVT: kind=errant_commit fault_id=1 corr=taint_prop "
        "dyn_inst_seq=391",
        # 退出汇总（不关联任何事件）→ none
        "PROP-EVT: kind=chain_end fault_id=1 outcome=run_end "
        "detection_layer=None contained=0 corr=none",
    ]
    for gl in good_lines:
        evt = P.parse_line(gl)
        check(f"validate {gl.split('kind=')[1].split()[0]} (labeled)",
              evt is not None and P.validate_event(evt) == [],
              str(P.validate_event(evt) if evt else None))
    # 空 corr = 契约违例（不再是合法值）
    bad_resp = P.parse_line("PROP-EVT: kind=resp fault_id=1 "
                            "dyn_inst_seq=303 corr=")
    check("resp with empty corr flagged (unlabeled join forbidden)",
          any("'corr'" in e for e in P.validate_event(bad_resp)),
          str(P.validate_event(bad_resp)))
    bad_end = P.parse_line("PROP-EVT: kind=chain_end fault_id=1 "
                           "outcome=run_end detection_layer=None contained=0")
    check("chain_end without corr flagged",
          any("'corr'" in e for e in P.validate_event(bad_end)),
          str(P.validate_event(bad_end)))
    # 已裁决的诚实缺席例外保持：tlb_pfn / pf_fill / pf_demand 的 corr
    # 不列入必录（空=无关联面 / fault_id=0 仅预取链）
    for kind in ("tlb_pfn", "pf_fill", "pf_demand"):
        check(f"{kind} corr stays optional (approved honest absence)",
              "corr" not in P.REQUIRED_FIELDS.get(kind, []),
              str(P.REQUIRED_FIELDS.get(kind)))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
