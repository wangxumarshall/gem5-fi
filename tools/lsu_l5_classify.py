#!/usr/bin/env python3
"""LSU L5 closure classifier (docs/gem5-fi/lsu/04-observation-points.md L5).

One run in, one five-class verdict out, conservation-checked:
    Activated = Masked + Detected/Contained + SDC + Crash + Timeout
(04 L5 pinned identity). Injected-not-activated is reported as its own
column and EXCLUDED from the SDC-rate denominator (04 L0 / 05 r12).

Inputs (all optional-but-checked):
  --run-dir DIR     gem5 --outdir: injection logs live here (abort fallback)
  --stdout FILE     the gem5 process stdout (checksum + CHAOS_LSU_TRIGGER)
  --stderr FILE     the gem5 process stderr (panic/assert = simulator DUE)
  --golden HEX      the workload golden checksum
  --exit N          the gem5 process exit code
  --timed-out       flag: the driver killed this run on timeout

HONEST LIMITS (W2/W3-known):
  * abort/abort-class runs never reach exit callbacks: no stdout funnel
    line — the classifier falls back to counting the injection log lines.
  * Crash 双拆分 (04 L5): a gem5 assertion (simulator DUE) is NOT an
    architectural crash; both are reported, crash_kind=simulator_assert vs
    guest/unknown.
  * Detected/Contained needs a detector signal; until W6 protection
    modeling is wired, runs classify without it (n/a, not zero).

Usage: python3 tools/lsu_l5_classify.py --run-dir D --stdout S \
          --stderr E --golden HEX --exit N [--timed-out] [--json OUT]
"""
import argparse
import json
import re
import sys
from pathlib import Path


def _read(path, out, label):
    """Read a file if given and present; absent optional files warn, not die."""
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        out.setdefault("warnings", []).append(f"{label} file missing: {path}")
        return ""
    return p.read_text(errors="replace")


# ---- G1: 检测点 / detection_layer / 污染链关联 ------------------------------
# 用户指令（L18-v2 审计 G1）："Crash 必须记录实际检测点、detection_layer、
# outcome，并与污染链关联"。规格依据：
#   * docs/gem5-fi/lsu/总方针.md:32 首检来源必须且只能是 Hardware RAS/OS/
#     Application/None（本模块用同名四值）。
#   * docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md:229
#     `detection_layer / contained` = 最终判定事件必需。
# Python 侧只靠 stdout/stderr/注入日志；硬件检测器信号须由发射器给出
# （见 plan 文件"C++ 发射器侧字段契约"）——无信号时 detection_layer 为
# None（n/a），绝不猜测成 Hardware RAS。
_ARCH_TRAP_MARKERS = ("illegal instruction", "SError", "data abort",
                      "prefetch abort", "Unknown instruction", "SIGILL",
                      "SIGSEGV", "SIGABRT")
_EXIT_TICK_RE = re.compile(r"exiting @ tick\s+(\d+)")
_ASSERT_LINE_RE = re.compile(
    r"^.*?(?:Assertion .*? failed\.?|panic|fatal: .*|"
    r"(?:Illegal instruction|SError|data abort|Data Abort|prefetch abort|"
    r"Prefetch Abort|Unknown instruction|SIG(?:ILL|SEGV|ABRT))).*$", re.M)


def _crash_detection_point(stdout, stderr, sim_assert):
    """崩溃检测点：kind / tick / pc / detail（真实从输出提取，缺则 None）。

    kind 枚举：simulator_assert（模拟器 DUE）> arch_trap（工作负载陷入）>
    exit_code（仅退出码非零，无文本证据）> unknown。
    """
    text = (stderr or "") + "\n" + (stdout or "")
    tick = None
    m = _EXIT_TICK_RE.search(text)
    if m:
        tick = int(m.group(1))
    detail = None
    dm = _ASSERT_LINE_RE.search(text)
    if dm:
        detail = dm.group(0).strip()[:300]
    low = text.lower()
    kind = ("simulator_assert" if sim_assert
            else "arch_trap" if any(mk.lower() in low
                                    for mk in _ARCH_TRAP_MARKERS)
            else "exit_code" if detail else "unknown")
    pc = None
    pm = re.search(r"\bpc[=:\s]+(0x[0-9a-fA-F]+|[0-9a-fA-F]{6,16})\b", text)
    if pm:
        pc = pm.group(1)
    return {"kind": kind, "tick": tick, "pc": pc, "detail": detail}


def _fault_linkage(injlog_text):
    """与注入点关联：首个 Site 行的 tick/site（污染链根，L0 侧）。"""
    for line in (injlog_text or "").splitlines():
        sm = re.search(r"Site:\s*([^,]+)", line)
        if not sm:
            continue
        tm = re.search(r"Tick:\s*(\d+)", line)
        fid = re.search(r"fault_id[=:\s]+(\d+)", line)
        return {"injected_tick": (int(tm.group(1)) if tm else None),
                "injected_site": sm.group(1).strip(),
                "fault_id": (int(fid.group(1)) if fid else None),
                "fault_index": 0}
    return None


def _taint_chain(prop_trace_path):
    """污染链关联：给了 prop_trace 则取 taint 终点/ptag（复用 L3 解析器）。

    绝不二次实现传播解析（单一解析入口 lsu_l3_propagation）；未给 trace 时
    如实记 not_provided（n/a），不静默。
    """
    if not prop_trace_path:
        return {"status": "not_provided",
                "reason": "未指定 --prop-trace（L3 传播 trace 未收集/未接线）"}
    try:
        import lsu_l3_propagation as L3P
    except ImportError as e:
        return {"status": "unavailable", "reason": f"lsu_l3_propagation 导入失败：{e}"}
    parsed = L3P.parse_prop_trace(prop_trace_path)
    nodes = parsed.get("nodes") or []
    if not nodes:
        return {"status": "empty_or_missing",
                "reason": f"prop_trace 0 节点（truncated={parsed.get('truncated')}）"}
    ptag = None
    for n in nodes:
        if n.get("kind") == "inj":
            ptag = n.get("ptag")
            break
    terminal = None
    for kind in ("errant_commit", "consumer", "taint_reg", "resp"):
        for n in nodes:
            if n.get("kind") == kind:
                terminal = {"terminal_kind": kind, "tick": n.get("tick"),
                            "ptag": n.get("ptag"),
                            "dyn_inst_seq": n.get("dyn_inst_seq")}
                break
        if terminal:
            break
    if terminal is None:
        return {"status": "no_terminal", "ptag": ptag,
                "reason": "prop_trace 无终点节点（inj/addr_form/mem_req 止）"}
    return {"status": "linked", "ptag": ptag, **terminal,
            "prop_trace_path": str(prop_trace_path)}


def _derived_detection_layer(crash_kind, detection_signal_layer):
    """detection_layer ∈ {Hardware RAS, OS, Application, None}（总方针 §32）。

    有真实检测器信号 → 采信信号层；否则诚实降级：
      simulator_assert（模拟器 DUE）= 非架构检测 → None；
      guest trap（内核陷入可见）= OS（并 note detector 未接线）；
      其余 → None。绝不把"无检测器"猜成 Hardware RAS。
    """
    if detection_signal_layer:
        return detection_signal_layer, "detector signal (CHAOS_DETECT/CLI)"
    if crash_kind == "simulator_assert":
        return "None", ("simulator DUE (panic/assert) is not an architectural "
                        "detection; audit 单列于五类之外")
    if crash_kind == "guest_or_unknown":
        return "OS", ("guest trap observed via kernel trap; hardware detector "
                      "signal not wired (W6)")
    return None, "no detection signal and no crash kind — n/a（不猜测）"


def classify(args):
    out = {"conservation": None, "error": None}
    # 输入完整性（P1 收尾加固，2026-09-29）：stdout 是 checksum 判定的唯一依据，
    # 给了路径但文件缺失时拒绝分类（此前会落入 checksum=None→Crash 的猜测路径，
    # 违反"未知必须写未知"——样本实测该缺陷由 A01 双跑重验暴露）。
    if args.stdout and not Path(args.stdout).exists():
        out["error"] = f"stdout file missing: {args.stdout} — 输入不完整，拒绝猜测结局"
        out["outcome"] = "INCONCLUSIVE"
        out["error_class"] = "input_incomplete"
        # [R6-ORACLE][G3] 早退前先补 activated/injected：审计实测此路径在
        # activated 赋值之前返回，且 lsu_handoff 对 INCONCLUSIVE 直接
        # `continue` → 一个 activated 样本被静默丢弃（丢弃比 Unknown 更糟）。
        # 注入日志（FUNNEL 行 > Site 行计数）是唯一幸存证据，据此如实回填，
        # 回填不了就显式记 n/a（绝不静默）。
        logs = (list(Path(args.run_dir).glob("*injections.log"))
                if args.run_dir else [])
        if logs:
            text = logs[0].read_text(errors="replace")
            funnels = re.findall(
                r"FUNNEL: attempted=(\d+) eligible=(\d+) injected=(\d+)", text)
            if funnels:
                out["attempted"], out["eligible"], out["injected"] = \
                    (int(x) for x in funnels[-1])
            else:
                n = len(re.findall(r"Site: ", text))
                if n:
                    out["injected"] = n
            out["funnel_source"] = f"injection-log({logs[0].name})"
        if out.get("injected") is not None:
            out["activated"] = out["injected"]
            out["activated_source"] = "fallback=injected（stdout 缺失，注入日志回填）"
        else:
            out["activated"] = None
            out.setdefault("warnings", []).append(
                "stdout 缺失且无注入日志 → activated n/a（不猜测）")
        out["classes"] = None
        out["recorded"] = True
        return out
    stdout = _read(args.stdout, out, "stdout")
    stderr = _read(args.stderr, out, "stderr")

    # ---- L0 funnel: stdout lines first, injection-log fallback ----
    m = re.search(r"CHAOS_LSU_TRIGGER: .*?attempted=(\d+) eligible=(\d+) "
                  r"injected=(\d+)", stdout)
    attempted = eligible = injected = None
    # 注入日志文本：funnel 回退与 G1 的 fault_linkage（污染链根）共用同一
    # 读取（此前只在 funnel 回退分支里读，导致 stdout 有 CHAOS_LSU_TRIGGER
    # 时 fault_linkage 恒 None —— G1 实测暴露）。
    logs = list(Path(args.run_dir).glob("*injections.log")) if args.run_dir else []
    injlog_text = logs[0].read_text(errors="replace") if logs else ""
    if m:
        attempted, eligible, injected = (int(x) for x in m.groups())
    else:
        if logs:
            text = injlog_text
            # FUNNEL 行优先（取最后一行=终态计数——cache 家族两行 FUNNEL：
            # 中途态 injected=0 + exit 终态 injected=1；旧代码取 Site 计数
            # 对 cache 格式恒 0 → 全部误判 inactive，2026-10-13 探测实证修复）
            funnels = re.findall(
                r"FUNNEL: attempted=(\d+) eligible=(\d+) injected=(\d+)",
                text)
            if funnels:
                attempted, eligible, injected = \
                    (int(x) for x in funnels[-1])
                out["funnel_source"] = (
                    f"injection-log-FUNNEL-last({logs[0].name},"
                    f"of-{len(funnels)})")
            else:
                n = len(re.findall(r"Site: ", text))
                injected = n
                out["funnel_source"] = f"injection-log-fallback({logs[0].name})"

    # ---- outcome ----
    checksum = None
    cm = re.findall(r"^[0-9a-f]{16}$", stdout, re.M)
    if cm:
        checksum = cm[-1]
    else:
        # [LSU][W1-REG] w1_all 不自打 checksum 行——从 8 个 fnv1a64 行派生：
        # sha256(行 join + 尾换行)[:16]，golden=6dab8ec221c46677（g1/g2/g3/
        # 原生 all_A 四方实证恒等；非 W1 负载无 fnv1a64 行，回退不触发）。
        import hashlib
        fv = [l for l in stdout.splitlines() if "fnv1a64=" in l]
        if len(fv) == 8:
            checksum = hashlib.sha256(("\n".join(fv) + "\n").encode()).hexdigest()[:16]
            out["checksum_source"] = "w1_fnv_derived"
    sim_assert = bool(re.search(r"Assertion .* failed|panic|abort", stderr))
    exit_code = args.exit

    if args.timed_out:
        outcome = "Timeout"
    elif exit_code not in (0, None):
        outcome = "Crash"
        out["crash_kind"] = ("simulator_assert" if sim_assert
                             else "guest_or_unknown")
    elif checksum is None:
        outcome = "Crash"          # no checksum line at all on abort paths
        out["crash_kind"] = ("simulator_assert" if sim_assert
                             else "guest_or_unknown")
    elif args.golden and checksum != args.golden:
        outcome = "SDC"
    else:
        outcome = "Masked"

    # ---- G1: Crash 检测点 / detection_layer / outcome / 污染链关联 ----
    # 只对 Crash 生效（规格 229 的"最终判定事件必需"字段）；Masked/SDC 的
    # 隔离层见 obs_core（G2）。detection_layer=None 表示 n/a（无信号），
    # 绝不猜测成 Hardware RAS。
    if outcome == "Crash":
        dp = _crash_detection_point(stdout, stderr, sim_assert)
        layer, layer_note = _derived_detection_layer(out["crash_kind"], None)
        out["detection_layer"] = layer
        out["detection_layer_source"] = layer_note
        out["detection_point"] = dp
        out["fault_linkage"] = _fault_linkage(injlog_text)
        out["taint_chain"] = _taint_chain(getattr(args, "prop_trace", None))
        if dp["tick"] is not None and (out["fault_linkage"] or {}).get(
                "injected_tick") is not None:
            dp["latency_ticks_from_injection"] = max(
                0, dp["tick"] - out["fault_linkage"]["injected_tick"])

    # ---- L5 five-class + conservation (04 L5 pinned identity) ----
    # Detected/Contained: no detector wired yet (W6 protection modeling) —
    # reported as detected=0 with detected_na=True, never silently.
    detected = 0
    out["detected_na"] = True
    activated = injected if injected is not None else 0
    # single-run verdict: the whole activated count lands in one class
    classes = {"Masked": 0, "Detected/Contained": detected, "SDC": 0,
               "Crash": 0, "Timeout": 0}
    if activated:
        classes[outcome] = activated
    s = sum(classes.values())
    out.update({
        "attempted": attempted, "eligible": eligible, "injected": injected,
        "activated": activated,
        "injected_not_activated": max(0, (injected or 0) - activated),
        "checksum": checksum, "outcome": outcome, "classes": classes,
    })
    out["conservation"] = ("OK" if s == activated else
                           f"VIOLATION sum={s} activated={activated}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir")
    p.add_argument("--stdout")
    p.add_argument("--stderr")
    p.add_argument("--golden")
    p.add_argument("--exit", type=int)
    p.add_argument("--timed-out", action="store_true")
    p.add_argument("--prop-trace", dest="prop_trace", default=None,
                   help="可选 prop_trace.csv.gz：Crash 的污染链关联（G1）")
    p.add_argument("--json", help="optional JSON output path")
    a = p.parse_args()
    r = classify(a)
    print("LSU_L5: " + json.dumps(r, ensure_ascii=False))
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=1) + "\n")
    sys.exit(0 if r["conservation"] == "OK" else 1)


if __name__ == "__main__":
    main()
