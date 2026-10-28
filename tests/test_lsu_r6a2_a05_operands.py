#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A3] A05-a/b/c 真实 ISA 操作数钩子契约（先红后绿）。

本轮缺口（R6-A2-STATUS/A05）：A05-a/b/c 在 pushRequest 阶段不可表达
（microop 源操作数槽实测 SIGSEGV），当前一律 ineligible；旧 `a05_shift`
是最终 EA 低字节旋转（代理），禁止冒充。

本测试钉死真实实现必须满足的结构性契约：
  1. 新 ISA 钩子文件 `arch/arm/insts/chaos_agu_operands.{hh,cc}` 存在，
     且由 ISA 生成物（includes.isa）与 ARM SConscript 真正编译；
  2. ldr64/str64 的 register-offset EA 生成路径在 EA 计算前调用钩子，
     且改写的是**局部副本**（不得原地改 StaticInst 的 type/shiftAmt）；
  3. CHAOSAddrPath 实现三类真实变换（base/index 互换、UXTW<->SXTW、
     shift 合法值替换），并携带真实操作数到证据；
  4. 登记按 (seq, pc, staticInst) 身份交接，pushRequest 只 claim 一次；
     未 claim 的陈旧登记必须回收计数，不得跨指令串链；
  5. 证据登记使用真实旧 EA（lastPreFaultOldAddr），不是已故障的输入 addr；
  6. A05-c 的旧低字节旋转代理不得继续作为 a05_shift 的实现；
  7. A05-d pre/post 既有真实实现保持不变；
  8. campaign A05 正式路由仍是实测过的 a05_prepost（W3 无标量 reg-offset，
     a/b/c 由定向 canary 覆盖，不在 W3 上伪造覆盖）。

用法：python3 tests/test_lsu_r6a2_a05_operands.py （退出码 0=全 PASS）
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def exists(rel):
    return (ROOT / rel).exists()


def read(rel):
    p = ROOT / rel
    return p.read_text() if p.exists() else ""


def main():
    hh = read("CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.hh")
    cc = read("CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.cc")
    incl = read("CHAOS/gem5/src/arch/arm/isa/includes.isa")
    sc = read("CHAOS/gem5/src/arch/arm/SConscript")
    ldr = read("CHAOS/gem5/src/arch/arm/isa/insts/ldr64.isa")
    strr = read("CHAOS/gem5/src/arch/arm/isa/insts/str64.isa")
    cpp = read("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc")
    chh = read("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh")
    lsq = read("CHAOS/gem5/src/cpu/o3/lsq.cc")
    proxy = read("configs/se/lsu_proxy.py")
    camp = read("tools/lsu_campaign.py")

    print("[1] ISA operand hook files + build wiring")
    check("chaos_agu_operands.hh exists", exists(
        "CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.hh"))
    check("chaos_agu_operands.cc exists", exists(
        "CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.cc"))
    check("hook entry declared", "chaosAguRegOperands" in hh)
    check("hook setter declared", "setChaosAguOperandHook" in hh)
    check("includes.isa includes the hook header",
          "chaos_agu_operands.hh" in incl)
    check("ARM SConscript compiles the hook source",
          "insts/chaos_agu_operands.cc" in sc)

    print("[2] register-offset EA path calls the hook BEFORE EA")
    for tag, src, is_load in (("ldr64", ldr, "true"), ("str64", strr, "false")):
        check(f"{tag}: register-offset calls hook",
              "chaosAguRegOperands" in src)
        check(f"{tag}: passes is_load={is_load}",
              re.search(r"chaosAguRegOperands\([^;]*/\*is_load=\*/%s" % is_load,
                        src.replace("\n", " ")) is not None)
        check(f"{tag}: EA computed from LOCAL copies, not members",
              ("_chaosBase" in src or "_caBase" in src) and
              "EA = XBase + extendReg64(XOffset, type, shiftAmt, 64)" not in
              src)
        check(f"{tag}: never assigns StaticInst members in place",
              not re.search(r"^\s*type\s*=", src, re.M) and
              not re.search(r"^\s*shiftAmt\s*=", src, re.M))

    print("[3] real transforms in CHAOSAddrPath")
    check("hook implementation present",
          "maybeCorruptAguOperands" in cpp and
          "maybeCorruptAguOperands" in chh)
    check("A05-a swaps base/index",
          "a05_base_index" in cpp and "swap" in cpp.lower())
    check("A05-b swaps UXTW/SXTW with bit31 visibility gate",
          "a05_extend" in cpp and "UXTW" in cpp and "SXTW" in cpp
          and "31" in cpp)
    check("A05-c substitutes another legal shift",
          "a05_shift" in cpp and
          re.search(r"(?i)shift.*(log2|Legal|another)", cpp) is not None)
    check("a/b/c no longer fall through the old 'ineligible' branch",
          not re.search(r"if \(a05_b \|\| a05_e \|\| a05_s\) \{\s*a05_ok = false;",
                        cpp))
    check("old low-byte-rotate proxy is gone",
          "low-byte rotate" not in cpp and
          "a05_shift (shift-amount submodel: low-byte rotate" not in chh)

    print("[4] request-scoped identity + reclamation")
    check("pending record carries seq/pc/static inst identity",
          "staticInst" in cpp and ("pending_agu" in cpp or "agu_pending" in cpp))
    check("claim compares seq and pc",
          re.search(r"(seq|dyn_inst_seq).*(==|!=)", cpp) is not None)
    check("stale reclamation counter exists",
          "stale_reclaimed" in cpp)

    print("[5] evidence carries the REAL old EA")
    check("lastPreFaultOldAddr accessor", "lastPreFaultOldAddr" in chh)
    check("lsq.cc registers the real old EA",
          "lastPreFaultOldAddr()" in lsq)

    print("[6] A05-d pre/post behaviour preserved")
    check("a05_prepost real immediate inversion intact",
          "a05_pre ? (addr - im) : (addr + im)" in cpp)

    print("[7] config + campaign routing")
    check("proxy accepts a05_base_index/extend/shift",
          all(m in proxy for m in ("a05_base_index", "a05_extend",
                                   "a05_shift")))
    check("proxy requires the LSU trigger for a/b/c",
          re.search(r"a05_(base_index|extend|shift).*requires", proxy) is not None
          or "_A05_OPERAND_MODES" in proxy)
    check("A05 formal route stays a05_prepost (measured W3 carrier)",
          LC.MODEL_FLAGS["A05"][1][:2] == ["--agu_pre_mode", "a05_prepost"],
          str(LC.MODEL_FLAGS["A05"]))
    check("campaign does not fake a/b/c coverage on W3",
          "a05_base_index" not in camp and "a05_extend" not in camp)

    if FAILED:
        print(f"R6-A3 A05 OPERAND TEST: {len(FAILED)} FAILURE(S)")
        return 1
    print("R6-A3 A05 OPERAND TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
