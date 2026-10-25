#!/usr/bin/env python3
"""[R6-F6APP] T04-F6-W4 收口：模型可应用性属于 eligibility。

原始事实（runs/lsu/r6_c7_T04-F6-W4_s1，binary a9b2c236，seed1）：
  CHAOS_LSU_TRIGGER attempted=66310644 eligible=1 injected=1
  stats board.chaos_armtlb.numFaultsInjected 0
  armtlb_injections.log 只有 arm_tlb_lookup_tier 诊断行
  cell_results.count_contradiction=true / admission=NO-ACTIVATION
根因：maybeCorrupt 在候选扫描**之前**就调 onF6Event，第一个（无合法候选的）
TLB hit 便消费了 F6 唯一机会。

本测试：
  [1] 真编译 + 真运行 tests/chaos_tlb_f6_applicability_test.cc（红→绿承载）
  [2] 真编译 + 真运行 tests/chaos_tlb_pfn_candidate_test.cc（既有谓词不回归）
  [3] CHAOSArmTLB.cc 调用顺序契约：attempt → 只读候选扫描 → 无候选诚实返回
      → tier 放行 → 应用
  [4] F0 legacy 分支逐字节不变契约

用法：python3 tests/test_lsu_r6_f6_applicability.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
TLB = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB"
ARM_CC = TLB / "CHAOSArmTLB.cc"
ARM_HH = TLB / "CHAOSArmTLB.hh"
PFN_HH = TLB / "chaos_tlb_pfn.hh"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def build_and_run(harness):
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / harness.stem
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(harness), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        if cc.returncode != 0:
            return False, (cc.stderr or "").strip()[:300]
        r = subprocess.run([str(exe)], capture_output=True, text=True)
        return (r.returncode == 0 and "ALL PASS" in (r.stdout or "")), \
               (r.stdout or "").strip()


def main():
    print("[1] 独立 C++ 单测：F6/F2/F5 的 phantom 消除（真编译 + 真运行）")
    ok, out = build_and_run(ROOT / "tests/chaos_tlb_f6_applicability_test.cc")
    print(out)
    check("f6_applicability harness ALL PASS", ok, out[-160:])
    if not ok and "error:" in out:
        check("f6_applicability harness compiles clean", False, out[:200])

    print("[2] 既有候选谓词单测不回归")
    ok2, out2 = build_and_run(ROOT / "tests/chaos_tlb_pfn_candidate_test.cc")
    print(out2)
    check("pfn_candidate harness ALL PASS", ok2, out2[-160:])

    print("[3] 调用顺序契约：CHAOSArmTLB.cc 必须 attempt → 扫描 → gate → 应用")
    arm = ARM_CC.read_text()
    hh = ARM_HH.read_text()
    pfn = PFN_HH.read_text()

    check("chaos_tlb_pfn.hh defines the applicability rule",
          "pfnHookAction" in pfn and "PfnHookAction" in pfn)
    check("chaos_tlb_pfn.hh keeps the rule dependency-free (no gem5 includes)",
          "chaos_lsu_trigger.hh" not in pfn)

    check("header splits the tier poll into book-attempt + fires",
          "lookupTierBookAttempt" in hh and "lookupTierFires" in hh)
    check("the bundled attempt+poll method is gone",
          "lookupTierAllowsInjection" not in hh and
          "lookupTierAllowsInjection" not in arm)
    check("the read-only candidate scan is a declared shared helper",
          "collectPfnCandidates" in hh and arm.count("collectPfnCandidates") >= 2)

    # The one ordering that matters: inside maybeCorrupt, on the tiered path,
    # the candidate scan + AttemptOnly early-return precede the tier poll.
    i_tier = arm.find("if (lookupTierMounted()) {")
    i_else = arm.find("} else {", i_tier + 1) if i_tier >= 0 else -1
    i_skip = arm.find("if (events_to_skip > 0) { --events_to_skip; return; }",
                      i_else + 1) if i_else >= 0 else -1
    check("the tiered/legacy block boundaries are locatable",
          i_tier >= 0 and i_else > i_tier and i_skip > i_else,
          f"tier@{i_tier} else@{i_else} skip@{i_skip}")
    tiered = arm[i_tier:i_else] if i_else > i_tier > -1 else ""
    i_scan = tiered.find("collectPfnCandidates(entry, pfn_candidates)")
    i_gate = tiered.find("PfnHookAction::AttemptOnly")
    i_fires = tiered.find("lookupTierFires(/*is_hit=*/true)")
    check("tiered path scans candidates before it polls the tier",
          0 <= i_scan < i_fires, f"scan@{i_scan} fires@{i_fires}")
    check("the empty-candidate early return sits between them",
          0 <= i_scan < i_gate < i_fires,
          f"scan@{i_scan} gate@{i_gate} fires@{i_fires}")
    check("attempt is booked before the scan",
          0 <= tiered.find("lookupTierBookAttempt()") < i_scan)
    check("the pre-fix bundled poll is not called from maybeCorrupt",
          "lookupTierAllowsInjection(" not in arm)

    print("[4] F0 legacy 分支逐字节不变契约")
    legacy_end = i_skip + len("if (events_to_skip > 0) { --events_to_skip; return; }")
    legacy = arm[i_else:legacy_end] if i_skip > i_else >= 0 else ""
    check("legacy F0 block located after the tiered block", legacy != "")
    check("legacy F0 gate sequence unchanged (attempted→cap→prob→eligible→skip)",
          all(f in legacy for f in (
              "++legacy_attempted;",
              "if (max_faults != 0 && faults_injected_count >= max_faults) return;",
              "if (probDist(rng) > probability) return;",
              "++legacy_eligible;",
              "if (events_to_skip > 0) { --events_to_skip; return; }")))
    for frag in ("++legacy_attempted;",
                 "if (max_faults != 0 && faults_injected_count >= max_faults) return;",
                 "if (probDist(rng) > probability) return;",
                 "++legacy_eligible;",
                 "if (events_to_skip > 0) { --events_to_skip; return; }"):
        check(f"legacy fragment present: {frag[:40]}", frag in legacy)
    check("the legacy block does NOT consult the applicability gate",
          "pfnHookAction" not in legacy and
          "collectPfnCandidates" not in legacy)

    print()
    if failed:
        print("FAILED (%d): %s" % (len(failed), ", ".join(failed)))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
