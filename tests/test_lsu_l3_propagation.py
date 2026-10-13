#!/usr/bin/env python3
"""test_lsu_l3_propagation.py — [LSU][OBS-L3] 传播链解析器单测（不起 gem5）。

合成 fixture 覆盖（用户指令 2026-10-13 自验证清单）：
  1 完整链（inj→addr_form→mem_req→resp→taint_reg→consumer→
    errant_commit→funnel）→ complete + path_complete=True
  2 链早断（inj→addr_form 止）→ complete + path_complete=False
  3 家族未覆盖（lsqfwd/prefetch）→ unsupported
  4 prop_trace 缺失（None / 文件不存在）→ unsupported
  5 空 trace（仅格式头 / 0 字节）→ unsupported
  6 截断流（无 gzip trailer 的 Z_SYNC_FLUSH 前缀 = abort 样本真形态）
    → truncated=True + 前缀打捞
  7 inactive → N/A(inactive_no_activation)
  8 FUNNEL 解析（多 funnel 行取最后）+ malformed 行不静默丢弃
"""
import gzip
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_l3_propagation as LP  # noqa: E402

HEADER = ("# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,"
          "request_id,addr,phys_reg,arch_reg,detail\n")

# 与 CHAOSPropagation.cc writeNode 逐列对齐的合成节点（十进制数值列、
# 无值列=空串、addr=无前缀小写 hex、detail='k=v;k=v' 无逗号）。
FULL_CHAIN = HEADER + (
    "0,123450,1,inj,77,,1a2b3000,,,"
    "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;"
    "new_size=8;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "1,123450,1,addr_form,77,,1a2b3008,,,"
    "site=lsq_pushRequest_PRE;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "2,124000,1,mem_req,77,77,1a2b3008,,,"
    "site=lsq_sendFragmentToTranslation;family=addrpath;size=8\n"
    "3,130000,1,resp,77,77,1a2b3008,,,"
    "family=addrpath;size=8;data_fnv=0123456789abcdef\n"
    "4,130001,1,taint_reg,77,77,1a2b3008,42,5,class=int;dest_idx=0\n"
    "5,140000,1,consumer,90,,,42,5,class=int;src_idx=1;pc=8f00\n"
    "6,140000,1,errant_commit,90,,,,,trigger=first_consumer;pc=8f00\n"
    "7,150000,0,funnel,,,,,,"
    "site=CHAOSAddrPath;attempted=12;eligible=5;injected=1\n"
)

EARLY_CUT = HEADER + (
    "0,123450,1,inj,77,,1a2b3000,,,"
    "site=lsq_sendFragmentToTranslation;family=addrpath;is_load=1;"
    "old_size=8;new_size=8;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "1,123450,1,addr_form,77,,1a2b3008,,,"
    "site=lsq_sendFragmentToTranslation;old_addr=1a2b3000;"
    "new_addr=1a2b3008\n"
)

MULTI_FUNNEL = HEADER + (
    "0,1000,1,inj,7,,ffff0000,,,family=cache;field=data;byte_offset=3;"
    "block_addr=ffff0000\n"
    "1,1000,0,funnel,,,,,,site=CHAOSCache;attempted=1;eligible=1;"
    "injected=1\n"
    "2,2000,0,funnel,,,,,,site=CHAOSCache;attempted=2;eligible=2;"
    "injected=1\n"
)

MALFORMED_MIX = HEADER + (
    "0,1000,1,inj,7,,ffff0000,,,family=cache;field=data;byte_offset=3;"
    "block_addr=ffff0000\n"
    "not,enough,columns\n"
)


def write_gz(tmp, name, text, finish=True):
    """写 gzip 文件；finish=False → 无 trailer 的 Z_SYNC_FLUSH 前缀
    （CHAOSPropagation abort 时的真实形态：每节点 flush，无 gzclose）。"""
    p = tmp / name
    if finish:
        with gzip.open(p, "wt", encoding="utf-8") as f:
            f.write(text)
    else:
        co = zlib.compressobj(9, zlib.DEFLATED, 31)  # wbits=31: gzip 头
        blob = co.compress(text.encode("utf-8")) \
            + co.flush(zlib.Z_SYNC_FLUSH)            # 无 trailer
        p.write_bytes(blob)
    return p


def main():
    tmp = Path(tempfile.mkdtemp(prefix="l3_prop_test_"))
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # 1) 完整链
    full = write_gz(tmp, "full.csv.gz", FULL_CHAIN)
    r = LP.parse_prop_trace(full)
    check("full_not_truncated", r["truncated"] is False, r)
    check("full_8_nodes", len(r["nodes"]) == 8,
          f"{len(r['nodes'])} nodes")
    n0 = r["nodes"][0]
    check("full_node0_cols",
          n0["node_id"] == 0 and n0["tick"] == 123450
          and n0["ptag"] == 1 and n0["kind"] == "inj"
          and n0["dyn_inst_seq"] == 77 and n0["request_id"] is None
          and n0["addr"] == 0x1a2b3000 and n0["phys_reg"] is None
          and n0["arch_reg"] is None
          and n0["detail"]["family"] == "addrpath", n0)
    t = r["nodes"][4]
    check("full_taint_cols",
          t["kind"] == "taint_reg" and t["phys_reg"] == 42
          and t["arch_reg"] == 5 and t["request_id"] == 77
          and t["detail"]["class"] == "int", t)
    check("full_funnel",
          r["funnel"] == {"site": "CHAOSAddrPath", "attempted": 12,
                          "eligible": 5, "injected": 1, "node_id": 7,
                          "tick": 150000}, r["funnel"])
    l2 = {"commit_diff": {"total_divergence_points": 3,
                          "divergence_counts": {"reg_value": 3},
                          "first_errant_commit": {"seq": 90}}}
    b = LP.build_l3("addrpath", l2, full)
    check("full_status_complete",
          b["status"] == "complete" and b["method"] == "propagation_trace",
          b.get("status"))
    check("full_correlation_keys",
          b["correlation_keys"] == ["dynInstSeqNum", "request_id", "ptag"])
    ev = b["evidence"]
    check("full_path_complete", ev["path_complete"] is True)
    check("full_evidence_counts",
          ev["mem_requests"]["count"] == 1
          and ev["responses"]["count"] == 1
          and ev["tainted_regs"]["count"] == 1
          and ev["consumers"]["count"] == 1, ev)
    check("full_first_errant",
          ev["first_errant_commit"]["dyn_inst_seq"] == 90
          and ev["first_errant_commit"]["detail"]["trigger"]
          == "first_consumer", ev["first_errant_commit"])
    check("full_aux_not_evidence",
          "auxiliary_commit_footprint" in b
          and b["auxiliary_commit_footprint"]["first_errant_seq"] == 90
          and all("auxiliary" not in k for k in ev), b.get("auxiliary"))
    check("full_caveats_nonempty", len(b["caveats"]) >= 3, b["caveats"])

    # 2) 链早断
    cut = write_gz(tmp, "cut.csv.gz", EARLY_CUT)
    b2 = LP.build_l3("addrpath", {}, cut)
    check("cut_complete_but_incomplete_chain",
          b2["status"] == "complete"
          and b2["evidence"]["path_complete"] is False
          and b2["evidence"]["mem_requests"]["count"] == 0
          and b2["evidence"]["first_errant_commit"] is None,
          b2.get("evidence"))
    check("cut_funnel_none_caveat",
          b2["funnel"] is None
          and any("FUNNEL" in c for c in b2["caveats"]), b2["caveats"])

    # 3) 家族未覆盖
    for fam in ("lsqfwd", "prefetch", "exmon", "physreg"):
        b3 = LP.build_l3(fam, {}, full)
        check(f"uncovered_{fam}",
              b3["status"] == "unsupported" and b3["method"] is None
              and "不在传播链" in b3["reason"], b3)

    # 4) trace 缺失
    b4a = LP.build_l3("addrpath", {}, None)
    check("missing_path_none",
          b4a["status"] == "unsupported" and "无 prop_trace" in b4a["reason"],
          b4a)
    b4b = LP.build_l3("cache", {}, tmp / "nope.csv.gz")
    check("missing_path_file",
          b4b["status"] == "unsupported" and "缺失" in b4b["reason"], b4b)

    # 5) 空 trace
    empty_hdr = write_gz(tmp, "empty_hdr.csv.gz", HEADER)
    b5a = LP.build_l3("addrpath", {}, empty_hdr)
    check("empty_header_unsupported",
          b5a["status"] == "unsupported" and "0 节点" in b5a["reason"], b5a)
    zero = tmp / "zero.csv.gz"
    zero.write_bytes(b"")
    b5b = LP.build_l3("cache", {}, zero)
    check("zero_byte_unsupported",
          b5b["status"] == "unsupported" and "0 节点" in b5b["reason"], b5b)

    # 6) 截断流（无 trailer 前缀 = abort 真形态）
    trunc = write_gz(tmp, "trunc.csv.gz", FULL_CHAIN, finish=False)
    r6 = LP.parse_prop_trace(trunc)
    check("trunc_flag", r6["truncated"] is True, r6["truncated"])
    check("trunc_salvage_8_nodes", len(r6["nodes"]) == 8,
          f"{len(r6['nodes'])} nodes")
    check("trunc_funnel_survives",
          r6["funnel"] is not None and r6["funnel"]["attempted"] == 12,
          r6["funnel"])
    b6 = LP.build_l3("addrpath", {}, trunc)
    check("trunc_complete_with_caveat",
          b6["status"] == "complete" and b6["truncated"] is True
          and any("截断" in c for c in b6["caveats"]), b6["caveats"])
    # 截断早断形态：前缀只到 mem_req（abort 于响应之前）
    trunc2 = write_gz(tmp, "trunc2.csv.gz",
                      "".join(FULL_CHAIN.splitlines(keepends=True)[:4]),
                      finish=False)
    r6b = LP.parse_prop_trace(trunc2)
    check("trunc_mid_chain_salvage",
          r6b["truncated"] is True and len(r6b["nodes"]) == 3
          and r6b["nodes"][-1]["kind"] == "mem_req",
          [n["kind"] for n in r6b["nodes"]])

    # 7) inactive
    b7 = LP.build_l3("addrpath", {}, full, inactive=True)
    check("inactive_na",
          b7["status"] == "N/A(inactive_no_activation)", b7)

    # 8) FUNNEL 多行取最后 + malformed 不静默丢弃
    mf = write_gz(tmp, "mf.csv.gz", MULTI_FUNNEL)
    r8 = LP.parse_prop_trace(mf)
    check("multi_funnel_last_wins",
          r8["funnel"]["attempted"] == 2 and r8["funnel"]["node_id"] == 2,
          r8["funnel"])
    mm = write_gz(tmp, "mm.csv.gz", MALFORMED_MIX)
    r8b = LP.parse_prop_trace(mm)
    check("malformed_recorded",
          len(r8b["nodes"]) == 1 and len(r8b["malformed"]) == 1
          and "not,enough,columns" in r8b["malformed"][0], r8b)
    b8 = LP.build_l3("cache", {}, mm)
    check("malformed_caveat",
          any("格式不符" in c for c in b8["caveats"]), b8["caveats"])

    # cache 家族完整链（字段细节与 addrpath 不同，链判定相同）
    cache_chain = HEADER + (
        "0,1000,1,inj,,,ffff0000,,,family=cache;field=data;"
        "byte_offset=3;block_addr=ffff0000\n"
        "1,2000,1,mem_req,9,9,ffff0000,,,site=lsq_sendFragmentToTranslation;"
        "family=cache;size=8\n"
        "2,3000,1,resp,9,9,ffff0000,,,family=cache;size=8;"
        "data_fnv=deadbeefdeadbeef\n"
        "3,3001,1,taint_reg,9,9,ffff0000,7,3,class=int;dest_idx=0\n"
        "4,4000,1,consumer,15,,,7,3,class=int;src_idx=0;pc=9000\n"
        "5,4000,1,errant_commit,15,,,,,trigger=faulting_load_commit;"
        "pc=9000\n"
        "6,5000,0,funnel,,,,,,site=CHAOSCache;attempted=1;eligible=1;"
        "injected=1\n"
    )
    cc = write_gz(tmp, "cache.csv.gz", cache_chain)
    b9 = LP.build_l3("cache", {}, cc)
    check("cache_family_complete",
          b9["status"] == "complete" and b9["evidence"]["path_complete"]
          and b9["evidence"]["first_errant_commit"]["detail"]["trigger"]
          == "faulting_load_commit", b9["evidence"])
    check("cache_hitmiss_caveat",
          any("hit/miss" in c for c in b9["caveats"]), b9["caveats"])

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
