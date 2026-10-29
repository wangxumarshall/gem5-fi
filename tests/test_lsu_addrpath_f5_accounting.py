#!/usr/bin/env python3
"""test_lsu_addrpath_f5_accounting.py — [R6-A-F5COUNT] CHAOSAddrPath 的 F5
注入必须逐次回报结果（noteOutcome），否则 trigger.injected 结构性为 0。

缺陷（2026-10-28 只读审计，A03/* 全部受影响）：
  `chaos_lsu_trigger.hh` 的 F5 分支只 `++fires`，`injected` 由注入器经
  `noteOutcome(effective)` 回报；`CHAOSArmTLB` 已接（:832/:865），但
  `CHAOSAddrPath::maybeCorrupt` 从未调用 —— 真实写入了故障（日志/ L0
  funnel / faults_injected_count 都在涨），而 trigger.injected 恒 0，
  于是 summary / CHAOS_L0_DECLINE / L5 三处都把 F5 看成“没有注入”。

本测试两部分：
  1) 源码合同（离线，必跑）：F5 的 fire 与 outcome 必须分离，且
     CHAOSAddrPath 在 fire 后的三条出口（成功 / nochange / geometry
     decline）都回报；trigger 构造函数对 F5 置 require_outcome_accounting。
  2) 证据合同（给定 outdir 时）：三源一致
     trigger.injected == 注入日志成功行数 == stats.numFaultsInjected，
     且 fires == injected + no_effect。

用法：
  python3 tests/test_lsu_addrpath_f5_accounting.py            # 源码合同
  python3 tests/test_lsu_addrpath_f5_accounting.py <outdir>   # + 证据合同
退出码 0 = 全 PASS。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc"
TRIG = ROOT / "CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh"

FAILED = []


def fail(msg):
    FAILED.append(msg)
    print(f"FAIL: {msg}")


def function_body(text, signature):
    """从 signature 起截到下一条同缩进的类成员函数定义（4 空格缩进）。"""
    i = text.find(signature)
    if i < 0:
        return None
    j = text.find("\n    CHAOSAddrPath::", i + len(signature))
    if j < 0:
        j = len(text)
    return text[i:j]


def check_source_contract():
    cc = SRC.read_text()
    trig = TRIG.read_text()

    body = function_body(cc, "CHAOSAddrPath::maybeCorrupt")
    if body is None:
        fail(f"{SRC}: maybeCorrupt not found")
        return
    for needle, why in (
        ("noteOutcome(true)", "successful F5 write must report effective"),
        ("noteOutcome(false)", "F5 decline/no-op must report no_effect"),
    ):
        if needle not in body:
            fail(f"CHAOSAddrPath::maybeCorrupt missing `{needle}` ({why})")
    # three exits: geometry decline, nochange, success
    if body.count("noteOutcome(") < 3:
        fail("maybeCorrupt must report exactly once on each F5 exit "
             "(geometry decline / no-change / success) — found "
             f"{body.count('noteOutcome(')} call(s)")

    ctor = function_body(trig, "ChaOSLsuTrigger(ChaOSLsuTier t")
    if ctor is None:
        fail(f"{TRIG}: ChaOSLsuTrigger ctor not found")
        return
    if "require_outcome_accounting" not in ctor:
        fail("ChaOSLsuTrigger ctor must set require_outcome_accounting for F5 "
             "(otherwise a reporting injector is never audited)")


def last(pattern, text):
    m = re.findall(pattern, text)
    return m[-1] if m else None


def assert_addrpath_f5_consistency(outdir):
    """返回违规字符串列表（空 = 通过）。"""
    outdir = Path(outdir)
    bad = []
    td = None
    for cand in sorted(outdir.rglob("stats.txt")):
        if cand.stat().st_size > 0:
            td = cand.parent
            break
    if td is None:
        return ["no non-empty stats.txt found"]
    stdout = ((td / "run.out").read_text(errors="replace")
              if (td / "run.out").exists() else "")
    trig = last(r"CHAOS_LSU_TRIGGER:\s*injector=CHAOSAddrPath\s+tier=F5\s+"
                r"attempted=\d+\s+eligible=\d+\s+injected=(\d+).*?"
                r"fires=(\d+)\s+no_effect=(\d+)", stdout)
    if trig is None:
        return ["CHAOS_LSU_TRIGGER injector=CHAOSAddrPath tier=F5 line not found"]
    t_inj, t_fires, t_noeff = map(int, trig)
    if t_fires != t_inj + t_noeff:
        bad.append(f"trigger: fires({t_fires}) != injected({t_inj}) + "
                   f"no_effect({t_noeff})")
    if t_fires == 0:
        bad.append("trigger.fires == 0 (no F5 fire at all — NO_FIRE)")

    logf = td / "addrpath_injections.log"
    logged = 0
    if logf.exists():
        for line in logf.open(errors="replace"):
            if "Site: lsq_sendFragmentToTranslation" in line \
                    and "old_vaddr=0x" in line and "new_vaddr=0x" in line \
                    and "REJECT" not in line:
                logged += 1
    else:
        bad.append("addrpath_injections.log missing")
    if logged != t_inj:
        bad.append(f"injection-log successful rows({logged}) != "
                   f"trigger.injected({t_inj})")

    stats = None
    for line in (td / "stats.txt").read_text(errors="replace").splitlines():
        m = re.match(r"board\.chaos_addrpath\.numFaultsInjected\s+(\d+)", line)
        if m:
            stats = int(m.group(1))
    if stats is None:
        bad.append("stats.txt missing board.chaos_addrpath.numFaultsInjected")
    elif stats != t_inj:
        bad.append(f"stats.numFaultsInjected({stats}) != trigger.injected({t_inj})")
    return bad


if __name__ == "__main__":
    check_source_contract()
    if len(sys.argv) > 1:
        for v in assert_addrpath_f5_consistency(sys.argv[1]):
            fail(v)
    if FAILED:
        print(f"ADDRPATH F5 ACCOUNTING TEST: {len(FAILED)} FAILURE(S)")
        sys.exit(1)
    print("ADDRPATH F5 ACCOUNTING TEST: ALL PASSED")
