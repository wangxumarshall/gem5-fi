#!/usr/bin/env python3
"""test_lsu_tlb_pfn_candidate.py — [MDSPEC][R6-FIXC] T04 候选谓词契约。

根因（冻结二进制真机 3/3 seed 复现）：CHAOSArmTLB.cc 的
`pfn_to_mapped_page` 候选过滤只有 `!=entry && pfn != entry->pfn`，**缺
`it->valid`** ⇒ TLB 中大量 invalid/stale（pfn==0）槽位主导候选集
（真机 `candidates: 31`），`rng()%N` 抽中 pfn=0 → `new_pfn=0x0` →
PA `0xfa8` → guest level-0 翻译故障 → 内核 Oops。产出的是"错页 + 崩溃"
而非规格 §2.10 F5 的"静默读到错误的活页"。

本测试**真编译并运行**独立 C++ 单测（`chaos_tlb_pfn_candidate_test.cc`），
覆盖：invalid/stale/pfn=0 被排除；合法 live mapping 被选中；页大小不一致
被排除；选择确定可复现。另设**防漂移守卫**：`CHAOSArmTLB.cc` 必须真正
调用同一谓词（否则谓词形同虚设）。

用法：python3 tests/test_lsu_tlb_pfn_candidate.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
HARNESS = ROOT / "tests/chaos_tlb_pfn_candidate_test.cc"
ARM_CC = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc"
HDR = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def main():
    print("[1] 独立 C++ 单测：真实编译 + 真实运行")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "tlb_pfn_test"
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(HARNESS), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        ok = cc.returncode == 0
        check("harness compiles clean (-Wall -Wextra -Werror)", ok,
              (cc.stderr or "").strip()[:200])
        if ok:
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            print((r.stdout or "").rstrip())
            check("harness ALL PASS", r.returncode == 0
                  and "ALL PASS" in (r.stdout or ""),
                  (r.stdout or "").strip()[-120:])
        else:
            print("  (harness did not build; behavioral checks skipped)")

    print("[2] 防漂移守卫：注入器必须真正使用同一谓词")
    arm = ARM_CC.read_text()
    check("CHAOSArmTLB.cc includes chaos_tlb_pfn.hh",
          "CHAOSArmTLB/chaos_tlb_pfn.hh" in arm)
    check("CHAOSArmTLB.cc calls isSelectablePfnTarget(",
          "isSelectablePfnTarget(" in arm)
    check("CHAOSArmTLB.cc uses the deterministic selection helper",
          "selectPfnCandidateIndex(" in arm)
    # 旧缺陷谓词（仅 pfn 不等 / 无 valid）不得复活。
    check("no stale candidate filter lacking validity remains",
          not re.search(r"!= entry && it->pfn != entry->pfn", arm))

    print("[3] 谓词把 stale/invalid 槽位排除（源码级最小证据）")
    hdr = HDR.read_text() if HDR.exists() else ""
    check("predicate requires cand.valid", "cand.valid" in hdr)
    check("predicate excludes the zero frame", "pfn == 0" in hdr)
    check("predicate enforces page-size consistency",
          "page_size_bits" in hdr)

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
