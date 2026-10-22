#!/usr/bin/env python3
"""test_lsu_a06_loadsize.py — [MDSPEC][R4-6-A06] A06 load 侧 size 注入 +
A06-b byte-enable 观测/注入 的契约测试（纯 Python，不需要 gem5 二进制）。

分三层，每层都标明**证据类型**（诚实标注，不把静态检查说成实证）：

  A. 源码契约（静态）：把 A06-a load leg 的合法包络、A06-b 的载体判定、
     接线点、日志/stdout 证据字段、被拒别名 —— 以精确字符串/行模式钉死在
     源码里；任何后续削弱（例如放开 shrink、去掉 panic、把 load 重新整体
     拒斥）都会让本层失败。**这不等于行为已被实证**（行为需 gem5 跑，
     见报告里的 spike 命令）。
  B. 载体（真实执行）：workloads/directed/a06_size_be.c 以
     `gcc -O2 -static -Wall -Wextra` 编译（零告警）并两次运行输出逐字节
     一致（确定性），canary 判定为 1（未污染）。这是本测试唯一的真跑项。
  C. 路由（静态 + import 真值）：campaign 的 A06 路由含规格模式名 a06_size
     与 load widen 目标；MODEL_BLOCKED 仍有 A06 且理由提到 load；A06S 不得
     泄入任何模型字典；lsu_proxy 的 --agu_pre_mode choices 不含被拒别名。

用法：python3 tests/test_lsu_a06_loadsize.py   （退出码 0 = 全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_campaign as lc   # noqa: E402

SRC = ROOT / "CHAOS" / "gem5" / "src" / "cpu" / "o3"
CC = SRC / "CHAOSAddrPath" / "CHAOSAddrPath.cc"
HH = SRC / "CHAOSAddrPath" / "CHAOSAddrPath.hh"
PY = SRC / "CHAOSAddrPath" / "CHAOSAddrPath.py"
LSQ = SRC / "lsq.cc"
LSQ_UNIT = SRC / "lsq_unit.cc"
DYNINST = SRC / "dyn_inst.hh"
PROXY = ROOT / "configs" / "se" / "lsu_proxy.py"
CARRIER = ROOT / "workloads" / "directed" / "a06_size_be.c"


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name
              + ("   <- " + str(detail) if not cond else ""))
        if not cond:
            fails.append(name)

    cctxt = CC.read_text()
    hhtxt = HH.read_text()
    pytest_txt = PY.read_text()
    lsqtxt = LSQ.read_text()
    proxytxt = PROXY.read_text()

    # ---------------- A. 源码契约（静态） ----------------
    # A1 load 侧不再是"整体拒斥"：a06_size 已从 pre_store_only 名单移除。
    m = re.search(r"pre_store_only = \((.*?)\);", cctxt, re.S)
    check("A1_a06_not_in_pre_store_only",
          m is not None and "a06_size" not in m.group(1),
          m.group(1) if m else "pre_store_only not found")

    # A2 [R4-8-A06] load 侧包络 = 另一合法值 {1,2,4,8,16}（widen 或 shrink），
    #    不再"只准 widen"；护栏是 target==原值不写（NoChange）与越 64B 行拒斥
    #    （Geometry）。shrink 之所以安全，靠的是定宽完成合同的**缓冲下限**
    #    （DynInst::chaosA06BufBytes），而不是禁掉该故障方向。
    check("A2_load_envelope_widen_or_shrink",
          "a06LoadSize" in cctxt
          and "A06LoadVerdict::NoChange" in cctxt
          and "ShrinkOrEqual" not in cctxt
          and "(addr & 63) + agu_size_to_load > 64" in cctxt,
          "load envelope / no-change guard not pinned")
    # A2b 定宽完成合同的载体必须三处齐备：字段声明（dyn_inst.hh）、
    #     设置点（lsq.cc 只在 **shrink** 时写）、两个分配点下限（lsq_unit.cc）。
    dictxt = DYNINST.read_text()
    lsqunittxt = LSQ_UNIT.read_text()
    check("A2b_shrink_carrier_wired",
          "unsigned chaosA06BufBytes = 0;" in dictxt
          and "inst->chaosA06BufBytes = pre_old_size;" in lsqtxt
          and lsqunittxt.count("chaosA06BufBytes") >= 2
          and lsqunittxt.count("new uint8_t[a06_buf]") >= 2,
          "A06 load-shrink buffer floor carrier not wired")
    # A2c 载体必须在**非 shrink** 时保持 0 => 非 A06 运行字节不变
    #     （field 默认 0 + 仅在 shrink 的 load 上赋值）。
    check("A2c_carrier_inert_by_default",
          "unsigned chaosA06BufBytes = 0;" in dictxt
          and "if (isLoad && size < pre_old_size)" in lsqtxt,
          "carrier not gated to the shrink case")

    # A3 几何约束（同 P4-FIX-GEOM 的 64B packet-offset 不变量）。
    check("A3_widen_block_geometry_guard",
          "(addr & 63) + agu_size_to_load > 64" in cctxt,
          "64B-line geometry guard missing")

    # A4 合法目标集合 = {1,2,4,8,16}（与规格的合法 size 域一致）。
    check("A4_legal_target_set",
          re.search(r"isLegalAguSize.*?\n.*?return s == 1 \|\| s == 2 \|\| s == 4 "
                    r"\|\| s == 8 \|\| s == 16;", cctxt) is not None,
          "isLegalAguSize definition not pinned")

    # A5 load 侧合法性判定在 trigger 决策之前（F-049：不合格 load 不得吃掉
    #    F6 的一次性 shot）。判据：verdict 计算块出现在 `if (lsuTrigger)` 之前。
    i_verdict = cctxt.find("A06-a load-leg verdict")
    i_trigger = cctxt.find("if (lsuTrigger) {", cctxt.find("maybeCorruptPre"))
    check("A5_load_verdict_before_trigger",
          i_verdict > 0 and i_trigger > 0 and i_verdict < i_trigger,
          f"verdict@{i_verdict} trigger@{i_trigger}")
    # A5b [R4-8-A06] 逐因计数在 **tier 路径** 也必须可达（历史上只在 legacy
    #     路径可达 ⇒ F0/F2/F6 的 campaign 路由看不见护栏，这正是 R4-6-A06
    #     真机复现不出 load_shrink 的原因）。判据：opclass 过滤块内出现
    #     per-reason switch + 明确注释。
    i_switch = cctxt.find("per-reason observability under the TIER")
    i_opclass_ret = cctxt.find("return size;   // op class not eligible "
                               "for this model")
    check("A5b_per_reason_counting_in_tier_path",
          i_switch > 0 and i_opclass_ret > 0 and i_switch < i_opclass_ret
          and cctxt.count("case A06LoadVerdict::NoChange:") >= 2,
          f"switch@{i_switch} opclass_ret@{i_opclass_ret}")

    # A6 A06-b：载体不可注入的部分显式拒斥 + 计数（load 侧 / size 已消费）。
    check("A6_be_decline_counted",
          "obs_be_declined" in cctxt and "obs_be_declined" in hhtxt
          and "else if (!isLoad && be_len == size && size >= 2)" in cctxt,
          "A06-b decline path not pinned")

    # A7 A06-b 掩码是"内部位清零"（尾部无 0 -> 不触发 addReq 尾部裁剪 ->
    #    size 不变 -> 不触 load 定宽合同）。判据：索引表达式 + 该论证注释。
    check("A7_be_mask_interior_only",
          "byte_enable[(size - 1) / 2] = false;" in cctxt
          and "inactiveTailSize" in cctxt,
          "interior-cleared mask substitution not pinned")

    # A8 be_mode 响亮拒绝（未知值 panic；非 a06_size 的 pre_mode panic）。
    check("A8_be_mode_loud_refusal",
          "unknown be_mode" in cctxt and "panic(" in cctxt
          and 'be_mode != "off" && pre_mode != "a06_size"' in cctxt,
          "be_mode validation missing")

    # A9 被拒别名仍在（不得私改模型 ID）：.cc 一次性 warn + 不注入。
    check("A9_rejected_alias_intact",
          'else if (pre_mode == "a06s_store_size")' in cctxt
          and "'a06s_store_size' is a rejected " in cctxt
          and "a06s_retired_warned" in cctxt,
          "a06s_store_size alias guard removed")

    # A10 证据字段：PRE 日志尾部自描述 + 新 stdout 汇总行。
    check("A10_evidence_fields",
          ", fault_field=" in cctxt and ", be_len=" in cctxt
          and ", be_ones=" in cctxt and ", be_subst=" in cctxt
          and "CHAOS_L0_A06:" in cctxt,
          "A06 evidence fields / summary line missing")
    # A10c [R4-8-A06] 汇总行新增 load_nochange、且 widen/shrink 分向计数
    #      （三者必须在 .hh 计数器、.cc 分支与 .cc 汇总行同时存在）。
    check("A10c_load_direction_counters",
          "obs_pre_a06_load_nochange" in hhtxt
          and "obs_pre_a06_load_nochange" in cctxt
          and "load_nochange=%lu" in cctxt
          and "if (a06_load_tgt > size) ++obs_pre_a06_load_widen;"
              in cctxt
          and "++obs_pre_a06_load_shrink;" in cctxt,
          "widen/shrink/nochange counters not pinned")
    # 日志改动必须是**尾部追加**（lsu_phantom_audit.py 的 PRE_LINE_RE 依赖
    # mode/old_addr/new_addr/old_size/new_size/faults_injected 的前缀顺序）。
    i_faults = cctxt.find('", faults_injected: " << faults_injected_count')
    i_field = cctxt.find('", fault_field="')
    check("A10b_log_tail_appended",
          i_faults > 0 and i_field > i_faults,
          f"faults_injected@{i_faults} fault_field@{i_field}")

    # A11 lsq.cc 接线：可变副本传入钩子 + _byteEnable 由该副本重建。
    check("A11_lsq_wiring",
          "std::vector<bool> pre_byte_enable(byte_enable);" in lsqtxt
          and "maybeCorruptPre(addr, size, isLoad,\n"
              "                                                      flags, "
              "inst->seqNum,\n"
              "                                                      "
              "pre_byte_enable)" in lsqtxt
          and "(pre_byte_enable.size() == size)" in lsqtxt,
          "lsq.cc PRE-hook byte-enable wiring not pinned")

    # A12 签名三处一致（.hh 声明 / .cc 定义 / lsq.cc 调用点参数个数）。
    check("A12_signature_consistent",
          "std::vector<bool>& byte_enable);" in hhtxt
          and "std::vector<bool>& byte_enable)" in cctxt
          and hhtxt.count("std::vector<bool>& byte_enable") >= 1,
          "maybeCorruptPre signature mismatch")

    # A13 参数全链路（SimObject.py -> .hh -> .cc -> lsu_proxy.py）。
    check("A13_param_aguSizeToLoad_wired",
          "aguSizeToLoad = Param.UInt64" in pytest_txt
          and "agu_size_to_load = 0" in hhtxt
          and "aguSizeToLoad=args.agu_size_to_load" in proxytxt
          and "agu_size_to_load(p.aguSizeToLoad)" in cctxt,
          "aguSizeToLoad not wired everywhere")
    check("A13_param_beMode_wired",
          "beMode = Param.String" in pytest_txt
          and 'be_mode = "off"' in hhtxt
          and "beMode=args.agu_be_mode" in proxytxt
          and "be_mode(p.beMode)" in cctxt,
          "beMode not wired everywhere")

    # A14 声明顺序 = ctor 初始化顺序（-Wreorder：agu_size_to_load/be_mode 必须
    #     紧跟在 agu_size_to 之后，且 .cc 初始化列表同序）。
    i_decl = hhtxt.find("uint64_t agu_size_to_load = 0;")
    i_bem = hhtxt.find('std::string be_mode = "off";')
    i_decl_agu = hhtxt.find("uint64_t agu_size_to = 0;")
    i_init = cctxt.find("agu_size_to_load(p.aguSizeToLoad),")
    i_init_be = cctxt.find("be_mode(p.beMode),")
    check("A14_member_and_init_order",
          i_decl_agu < i_decl < i_bem and 0 < i_init < i_init_be,
          f"decl {i_decl_agu}/{i_decl}/{i_bem} init {i_init}/{i_init_be}")

    # ---------------- B. 载体（真实执行） ----------------
    check("B0_carrier_exists", CARRIER.is_file(), str(CARRIER))
    if CARRIER.is_file():
        with tempfile.TemporaryDirectory() as td:
            exe = Path(td) / "a06_size_be"
            cp = subprocess.run(
                ["gcc", "-O2", "-static", "-Wall", "-Wextra",
                 "-o", str(exe), str(CARRIER)],
                capture_output=True, text=True, timeout=300)
            warn = (cp.stdout + cp.stderr).strip()
            check("B1_carrier_builds_clean", cp.returncode == 0 and warn == "",
                  f"rc={cp.returncode} out={warn[:300]}")
            if cp.returncode == 0:
                r1 = subprocess.run([str(exe)], capture_output=True, text=True,
                                    timeout=120)
                r2 = subprocess.run([str(exe)], capture_output=True, text=True,
                                    timeout=120)
                check("B2_carrier_deterministic",
                      r1.returncode == 0 and r1.stdout == r2.stdout
                      and r1.stdout.strip() != "",
                      f"rc={r1.returncode} out={r1.stdout[:80]!r}")
                lines = r1.stdout.strip().splitlines()
                check("B3_carrier_oracle_lines",
                      len(lines) == 2
                      and re.fullmatch(r"[0-9a-f]{16}", lines[0]) is not None
                      and lines[1] == "canary=" + "0" * 15 + "1",
                      f"lines={lines}")

    # ---------------- C. 路由 / 配置（静态 + import 真值） ----------------
    family, extra = lc.MODEL_FLAGS["A06"]
    check("C1_a06_route_spec_mode",
          family == "addrpath" and "--agu_pre_mode" in extra
          and "a06_size" in extra,
          f"family={family} extra={extra}")
    check("C2_a06_route_has_load_target",
          "--agu_size_to_load" in extra and "--agu_size_to" in extra,
          f"extra={extra}")
    check("C3_a06_still_blocked",
          "A06" in lc.MODEL_BLOCKED
          and "load" in str(lc.MODEL_BLOCKED["A06"]).lower(),
          str(lc.MODEL_BLOCKED.get("A06"))[:120])
    # C3b [R4-8-A06] BLOCKED 理由必须**具体且可跑**（不是空话）：点名 load 侧
    #     shrink、点名 COMPILE-UNVERIFIED 这条真实原因；且 6 个 A06 RunID 都
    #     仍在 MODEL_BLOCKED 里（逐个断言，不是"存在 A06 就行"）。
    a06_rows = [f"A06-F0-W3", "A06-F0-W5", "A06-F2-W3", "A06-F2-W5",
                "A06-F6-W3", "A06-F6-W5"]
    reason = str(lc.MODEL_BLOCKED.get("A06", ""))
    check("C3b_blocked_reason_specific",
          "SHRINK" in reason.upper()
          and "COMPILE-UNVERIFIED" in reason.upper(),
          reason[:160])
    # 6 个 RunID 的 model 前缀都必须落在 MODEL_BLOCKED（campaign 以 model
    # 为单位封锁；RunID 级封锁由该 model 条目派生）。
    check("C3c_all_six_a06_runids_blocked",
          all(r.split("-")[0] in lc.MODEL_BLOCKED for r in a06_rows),
          f"rows={a06_rows} blocked={sorted(lc.MODEL_BLOCKED)[:12]}")
    # C3d 反向：A06 必须在 MODEL_BLOCKED **且不在** MODEL_FLAGS 的可跑集合之外
    #     —— A06 有路由（MODEL_FLAGS）但同时被 BLOCKED 是允许的（RULING 家族），
    #     但没有路由才是回归。
    check("C3d_a06_has_route_but_blocked",
          "A06" in lc.MODEL_FLAGS and "A06" in lc.MODEL_BLOCKED,
          f"flags={'A06' in lc.MODEL_FLAGS} blocked={'A06' in lc.MODEL_BLOCKED}")
    check("C4_no_a06s_model_id",
          not any(k.startswith("A06S") for k in lc.MODEL_FLAGS)
          and not any(k.startswith("A06S") for k in lc.MODEL_BLOCKED),
          f"flags={[k for k in lc.MODEL_FLAGS if k.startswith('A06S')]}")
    # C5 只判 **choices 列表本身**：帮助文本里提到被拒别名是允许的
    # （"REMOVED (rejected alias …)"），把它混进 choices 才是回归。
    mchoice = re.search(r'"--agu_pre_mode", default="off",\s*\n\s*choices=\[(.*?)\]',
                        proxytxt, re.S)
    choices = mchoice.group(1) if mchoice else ""
    check("C5_alias_absent_from_proxy_choices",
          '"a06_size"' in choices and "a06s_store_size" not in choices,
          f"choices={choices[:200]!r}")
    check("C6_be_mode_choices_declared",
          '"off","observe","shift_mid"' in proxytxt.replace(" ", ""),
          "agu_be_mode choices missing")
    check("C7_proxy_be_mode_validation",
          'args.agu_be_mode != "off" and args.agu_pre_mode != "a06_size"'
          in proxytxt,
          "config-time be_mode validation missing")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
