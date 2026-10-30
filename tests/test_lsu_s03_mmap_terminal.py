#!/usr/bin/env python3
"""S03-F5：故障后非法 mmap 必须返回 guest-visible ENOMEM，而不是 gem5 断言。

实证（r6_s_repair2b/S03-F5-W5_s1，2026-10-30）：
  guest 在 errant commit 后调用
    mmap2(0, 4611686018427392000, 3, 34, -1, 0)
  （length = 2^62 + 4096，被故障数据污染）。gem5 的 extendMmap 令
  start = _mmapEnd - length，start+length 回绕：mmap range 打印为
  start 0xc000003fffeff000 - end 0x3fffefffff，随后
  VMA::sanityCheck 断言 `start < end` 失败 → SIGABRT、stats/gzip 截断。

正确语义：Linux 对无法放入地址空间的 length 返回 ENOMEM。修复必须在
mmap 入口拒绝溢出长度，且不得把 _mmapEnd 更新为回绕值；这不是“任意
abort 归类为 Crash”，也不是放宽准入。

用法：python3 tests/test_lsu_s03_mmap_terminal.py   退出码 0=全 PASS。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    ms = src("CHAOS/gem5/src/sim/mem_state.cc")
    se = src("CHAOS/gem5/src/sim/syscall_emul.hh")
    vma = src("CHAOS/gem5/src/sim/vma.cc")

    print("[1] extendMmap rejects an unmappable length before updating state")
    body = ms[ms.index("MemState::extendMmap"):
             ms.index("MemState::printVmaList")]
    check("rejects length 0", "if (length == 0)" in body)
    check("rejects grows-down underflow", "if (length > _mmapEnd)" in body)
    check("rejects grows-up overflow", "if (length > MaxAddr - _mmapEnd)" in body)
    check("failure sentinel is 0 (caller maps ENOMEM)",
          body.count("return 0;") >= 2, body.count("return 0;"))
    check("_mmapEnd is only updated after the guards",
          body.index("if (length > MaxAddr - _mmapEnd)")
          < body.index("_mmapEnd ="))

    print("[2] mmapFunc validates the range and returns ENOMEM")
    mf = se[se.index("mmapFunc(SyscallDesc *desc"):
            se.index("munmapFunc")]
    check("hint overflow rejected with ENOMEM",
          "if (start && length > MaxAddr - start)" in mf
          and "return -ENOMEM;" in mf)
    check("extendMmap failure rejected with ENOMEM",
          "if (!start || length > MaxAddr - start)" in mf)
    check("no mapRegion after a rejected range",
          mf.index("return -ENOMEM;") < mf.index("p->memState->mapRegion"))
    check("real Linux semantics named in the guard",
          "ENOMEM" in mf)

    print("[3] the VMA invariant is untouched (not weakened)")
    check("VMA still asserts start < end",
          "assert(_addrRange.start() < _addrRange.end())" in vma)
    check("VMA still asserts non-empty",
          "assert(_addrRange.start() != _addrRange.end())" in vma)

    print("[4] an internal abort still cannot be admitted as evidence")
    sys.path.insert(0, str(ROOT / "tools"))
    import lsu_chain_check as CC  # noqa: E402
    # A full-looking chain whose stream is marked truncated must not admit.
    ev = [{
        "kind": "inj", "fault_id": "1", "event_id": "0",
        "parent_event_id": "", "tick": "1", "cycle": "0",
        "dyn_inst_seq": "1", "va": "1000", "corr": "origin",
        "field": "", "detection_layer": "", "contained": "",
        "outcome": "", "before": "", "after": "", "state_before": "",
        "state_after": "", "sq_idx": "", "request_id": "",
        "store_dyn_inst_seq": "", "phys_reg": "", "arch_reg": "", "pa": "",
    }]
    r = CC.check_admission({
        "run_id": "S03-F5-W5", "activated": 1, "events": ev, "rc": -6,
        "oracle_outcome": "Crash", "containment": None, "truncated": True,
    })
    check("truncated internal abort is refused", r["admitted"] is False,
          (r["admitted"], r["violations"]))

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
