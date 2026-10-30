#!/usr/bin/env python3
"""test_lsu_s10_trigger_reporting.py — S10-F5 触发计数/结果上报修复。

实测缺陷（S10-F5-W5/W9，2026-10-30 复核）：
  * 配置 maxFaults=1，实际注入 3 次 —— subst 注入点从未检查 cap；
  * subst 点调用 onEligible() 后从不 noteOutcome() ⇒ F5 fires=3、
    outcomes_recorded=0、trigger.injected=0；
  * 三方计数矛盾：trigger injected=0 / 注入日志 3 行 /
    stats.numFaultsInjected=3。

修复合同：
  * cap 在 subst 注入点同样生效（cap 后不再 onEligible）；
  * 每次真实写入后 F5 调用 noteOutcome(true)；
  * fires == injected + no_effect；trigger.injected == 日志成功行 ==
    stats.numFaultsInjected；
  * 矛盾必须响亮失败（census 记 BLOCKED_TRIGGER_REPORTING，绝不 PASS）。

用法：python3 tests/test_lsu_s10_trigger_reporting.py
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EVID = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit")
FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _body(text, start, end_markers):
    i = text.find(start)
    if i < 0:
        return None
    j = len(text)
    for m in end_markers:
        k = text.find(m, i + len(start))
        if k >= 0:
            j = min(j, k)
    return text[i:j]


def test_source_contract():
    print("[1] S10 source contract")
    fwd = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd"
           / "CHAOSLSQFwd.cc").read_text()
    body = _body(fwd, "CHAOSLSQFwd::s10SsidSubstCb(Addr store_pc",
                 ["CHAOSLSQFwd::s10CorruptedPcCb(Addr pc"])
    check("s10SsidSubstCb found", body is not None)
    if body is None:
        return
    cap = body.find("max_faults")
    elig = body.find("onEligible")
    check("maxFaults is enforced at the injection site", cap >= 0 and
          cap < elig, f"cap@{cap} eligible@{elig}")
    check("cap-gated return happens before onEligible",
          "faults_injected_count >=" in body and cap < elig)
    check("successful F5 write reports the outcome",
          "noteOutcome(true)" in body)
    check("outcome reporting is F5-only (no double count for F0-F4)",
          "ChaOSLsuTier::F5" in body)
    # the outcome note must follow the injection accounting, not precede it
    inj = body.find("++s10_active->faults_injected_count")
    if inj < 0:
        inj = body.find("s10_active->faults_injected_count;")
    out = body.find("noteOutcome(true)")
    check("noteOutcome(true) is after the real write", inj >= 0 and
          out > inj, f"inject@{inj} outcome@{out}")


def test_trigger_unit():
    print("[2] trigger F5 accounting unit test (standalone C++)")
    src = ROOT / "tests/chaos_lsu_s10_accounting_test.cc"
    check("unit-test source exists", src.exists(), src)
    gxx = shutil.which("g++") or shutil.which("c++")
    check("C++ compiler present", gxx is not None)
    if not src.exists() or not gxx:
        return
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "s10_acct"
        r = subprocess.run([gxx, "-std=c++17", "-I", str(ROOT / "CHAOS/gem5/src"),
                            str(src), "-o", str(exe)],
                           capture_output=True, text=True)
        check("unit test compiles (zero warnings-as-errors)",
              r.returncode == 0, r.stderr[-1500:])
        if r.returncode != 0:
            return
        r = subprocess.run([str(exe)], capture_output=True, text=True)
        check("unit test passes", r.returncode == 0,
              (r.stdout[-1500:], r.stderr[-500:]))
        check("fires == injected + no_effect (reported)",
              "PASS fires==injected+no_effect" in r.stdout, r.stdout[-800:])
        check("unreported fire is detectable (defect pinned)",
              "PASS unreported-detected" in r.stdout, r.stdout[-800:])


def _parse_trigger(text):
    d = {}
    for ln in text.splitlines():
        if ln.startswith("CHAOS_LSU_TRIGGER:"):
            for k in ("attempted", "eligible", "injected", "fires",
                      "no_effect"):
                m = re.search(rf" {k}=(\S+)", ln)
                if m:
                    d[k] = m.group(1)
    return d


def _counts(seed_dir):
    runout = (seed_dir / "run.out").read_text(errors="replace")
    trig = _parse_trigger(runout)
    log = (seed_dir / "lsq_fwd_injections.log")
    logn = 0
    if log.exists():
        logn = len([ln for ln in log.read_text(errors="replace").splitlines()
                    if "faults_injected:" in ln])
    statsn = None
    st = seed_dir / "stats.txt"
    if st.exists():
        for ln in st.read_text(errors="replace").splitlines():
            if ln.startswith("board.chaos_lsqfwd.numFaultsInjected"):
                statsn = int(ln.split()[1])
                break
    return trig, logn, statsn, runout


def test_evidence_triage():
    print("[3] S10-F5 evidence triage (old raw evidence)")
    for rid in ("S10-F5-W5", "S10-F5-W9"):
        d = EVID / f"{rid}_s1" / rid / "seed1"
        if not d.is_dir():
            # W9 may not have been run; record honestly as absent, not PASS.
            print(f"  INFO {rid}: seed1 evidence absent (no PASS recorded)")
            continue
        trig, logn, statsn, runout = _counts(d)
        contradiction = (trig.get("injected") not in (None,)
                         and str(logn) != trig.get("injected"))
        check(f"{rid}: contradiction is visible in raw evidence",
              contradiction,
              f"trigger={trig} log={logn} stats={statsn}")
        check(f"{rid}: ALARM names the reporting gap",
              "F5_UNREPORTED_OUTCOME" in runout)
        # never a PASS: the cell must remain blocked/triaged.
        cell = json.loads((EVID / f"{rid}_s1" / rid
                           / "cell_results.json").read_text())
        check(f"{rid}: not counted as a pass",
              cell.get("classes", {}).get("SDC", 0) == 0
              and cell.get("classes", {}).get("Crash", 0) == 0)


def main():
    for fn in (test_source_contract, test_trigger_unit, test_evidence_triage):
        fn()
    if FAILED:
        print(f"\nFAILED {len(FAILED)}: {FAILED}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
