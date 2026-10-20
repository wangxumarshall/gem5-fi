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

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
