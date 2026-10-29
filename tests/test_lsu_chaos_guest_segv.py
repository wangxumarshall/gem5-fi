#!/usr/bin/env python3
"""test_lsu_chaos_guest_segv.py — [R6-A-SEGV] 被注入的未映射地址在 SE 下
必须建模为真实 guest SEGV 并正常 teardown，而不是 gem5 panic abort。

缺陷（2026-10-28 A01-F0-W3 seed1 / A03-F5-W3 seeds1-3 实测）：
  注入的 EA 翻到未映射页 → `GenericPageTableFault::invoke` 走
  `panic_if(!handled && !trapToGdb(...))` → abort，stats.txt 0 字节、
  prop_evt gzip 无 trailer、campaign 判 EVIDENCE-TRUNCATED。真实机器上
  用户态访问未映射页会收到 SIGSEGV 并退出；SE 没有 OS，正确建模是
  结束仿真并以 guest SEGV 退出码收口。

本测试钉住：
  1) CHAOSAddrPath 在注入成功时把新 VA 记入 guest-fault 登记表；
  2) sim/faults.cc 的 GenericPageTableFault 在 panic 前消费该 VA 并
     exitSimLoop（不再 panic）。
  证据合同（给定 outdir）：崩溃样本的 prop_evt gzip 必须完整、stats.txt
  非空、chain_report.truncated=False。

用法：python3 tests/test_lsu_chaos_guest_segv.py [outdir]
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAULTS = ROOT / "CHAOS/gem5/src/sim/faults.cc"
ADDRPATH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc"
REGISTRY = ROOT / "CHAOS/gem5/src/base/chaos_guest_fault.hh"

FAILED = []


def fail(msg):
    FAILED.append(msg)
    print(f"FAIL: {msg}")


def check_source_contract():
    if not REGISTRY.exists():
        fail(f"{REGISTRY}: guest-fault registry header missing")
    else:
        txt = REGISTRY.read_text()
        for needle in ("noteInjectedGuestVa", "consumeInjectedGuestVa"):
            if needle not in txt:
                fail(f"{REGISTRY}: missing `{needle}`")

    ad = ADDRPATH.read_text()
    if "noteInjectedGuestVa(new_vaddr)" not in ad:
        fail("CHAOSAddrPath.cc: successful injection must register new_vaddr "
             "as an injected guest VA")

    ft = FAULTS.read_text()
    i = ft.find("GenericPageTableFault::invoke")
    if i < 0:
        fail(f"{FAULTS}: GenericPageTableFault::invoke not found")
        return
    body = ft[i:i + 1200]
    if "guestSegvArmed" not in body:
        fail("GenericPageTableFault::invoke must consult the chaos injected-VA "
             "registry before panicking")
    if "exitSimLoop" not in body:
        fail("GenericPageTableFault::invoke must exitSimLoop (guest SEGV) for "
             "injected VAs so stats/prop_evt are flushed")
    if body.find("guestSegvArmed") > body.find("panic_if"):
        fail("chaos injected-VA handling must run BEFORE panic_if")


def check_evidence(outdir):
    outdir = Path(outdir)
    td = None
    for cand in sorted(outdir.rglob("stats.txt")):
        if cand.stat().st_size > 0:
            td = cand.parent
            break
    if td is None:
        fail("no non-empty stats.txt (crash evidence was not flushed)")
        return
    cr_path = td / "chain_report.json"
    if not cr_path.exists():
        fail("chain_report.json missing")
        return
    cr = json.loads(cr_path.read_text())
    if cr.get("truncated"):
        fail("chain_report.truncated=True (prop_evt stream incomplete)")
    p = td / "prop_evt.txt.gz"
    if p.exists():
        try:
            with gzip.open(p, "rt") as f:
                for _ in f:
                    pass
        except Exception as e:
            fail(f"prop_evt gzip not intact: {e}")


if __name__ == "__main__":
    check_source_contract()
    if len(sys.argv) > 1:
        check_evidence(sys.argv[1])
    if FAILED:
        print(f"CHAOS GUEST SEGV TEST: {len(FAILED)} FAILURE(S)")
        sys.exit(1)
    print("CHAOS GUEST SEGV TEST: ALL PASSED")
