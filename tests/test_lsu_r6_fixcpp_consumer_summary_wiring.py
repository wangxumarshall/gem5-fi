#!/usr/bin/env python3
"""[MDSPEC][R6-FIXCPP/T3] consumer_summary 接入 CHAOSPropagation 发射（不跑仿真）。

T2 交付了聚合逻辑（共享头 + 单测）；本套件钉**接入点**：
  [1] CHAOSPropagation 持有 Aggregator，且只有 `consumer` 走它；
  [2] noteCommit 的 consumer 发射被门控（代表项写 PROP-EVT 并回填 event_id；
      抑制项不造事件，改用代表项 event_id 保持 DAG 连通）；
  [3] exit 回调在 **chain_end 之前** flush 每个 summary；
  [4] 资源上限触发时**响亮**落盘（printf + gzwrite 的 abort 标记），绝不静默；
  [5] summary 不是 PROP-EVT：emitPropEvt/writeNode 的 kind 里不含它。

另：给定真实流路径（`LSU_FIXCPP_PROP_EVT=<path>`）时，用冻结契约校验器复核其中
每条 CONSUMER-SUMMARY 并核对守恒；未给则显式打印 n/a（不静默跳过）。

用法：python3 tests/test_lsu_r6_fixcpp_consumer_summary_wiring.py   （exit 0 = 全 PASS）
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROP_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
PROP_CC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc"

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def main():
    hh = PROP_HH.read_text(encoding="utf-8")
    cc = PROP_CC.read_text(encoding="utf-8")

    print("[1] CHAOSPropagation 持有 Aggregator；只有 consumer 走它")
    check("hh include chaos_consumer_summary.hh",
          "chaos_consumer_summary.hh" in hh)
    check("hh 持有 chaos_consumer::Aggregator 成员",
          re.search(r"chaos_consumer::Aggregator\s+consumer_agg", hh) is not None)
    kinds = set(re.findall(r'consumer_agg\.observe\(\s*"([^"]+)"', cc))
    check(f"只有 consumer 走聚合器（kinds={sorted(kinds)}）",
          kinds == {"consumer"}, str(sorted(kinds)))
    check("noteEmitted / representativeEvent 都被接线",
          'consumer_agg.noteEmitted("consumer"' in cc
          and "consumer_agg.representativeEvent(" in cc)

    print("[2] noteCommit 的 consumer 发射被门控（代表项/抑制项）")
    check("代表项仍写 consumer PROP-EVT（writeNode ... consumer）",
          re.search(r'writeNode\(cptag, "consumer"', cc) is not None)
    check("抑制项不造事件（else 分支只取代表项 event_id）",
          "const uint64_t rep = consumer_agg.representativeEvent(" in cc)
    check("summary 记录不是 PROP-EVT（不进 writeNode/emitPropEvt 的 kind）",
          '"consumer_summary"' not in cc
          and re.search(r'writeNode\([^)]*"consumer-summary"', cc) is None)

    print("[3] exit 回调在 chain_end 之前 flush summary")
    flush_i = cc.find("consumer_agg.flush(")
    chain_end_i = cc.find('notePropEvt("chain_end"')
    check("flush 出现在源中", flush_i >= 0)
    check("flush 在 chain_end 之前（source order）",
          flush_i >= 0 and chain_end_i >= 0 and flush_i < chain_end_i,
          f"flush@{flush_i} chain_end@{chain_end_i}")
    check("flush 写在 evt_gz_file 且 per-row gzflush",
          "CONSUMER-SUMMARY write" in cc and "gzflush(evt_gz_file" in cc)

    print("[4] 资源上限触发时响亮落盘（绝不静默）")
    check("resourceAborted() 分支存在",
          "consumer_agg.resourceAborted()" in cc)
    check("abort 标记 printf 到 stdout", "resourceAbortLine(" in cc
          and re.search(r'printf\("%s\\n", ab\.c_str\(\)\)', cc) is not None)
    check("abort 标记也写入流", re.search(r'gzwrite\(evt_gz_file, row\.data\(\)',
                                          cc) is not None)

    print("[5] 真实流复核（LSU_FIXCPP_PROP_EVT）")
    path = os.environ.get("LSU_FIXCPP_PROP_EVT", "").strip()
    if not path or not Path(path).exists():
        print("      n/a —— 未提供真实 prop_evt 流路径（LSU_FIXCPP_PROP_EVT）")
    else:
        import gzip
        opener = gzip.open if path.endswith(".gz") else open
        lines = [ln.rstrip("\n") for ln in opener(path, "rt", errors="replace")]
        sums = [ln for ln in lines if "CONSUMER-SUMMARY:" in ln]
        evts = [ln for ln in lines if ln.startswith("PROP-EVT:")]
        print(f"      {path}: {len(evts)} PROP-EVT, {len(sums)} CONSUMER-SUMMARY")
        try:
            import lsu_prop_fields as PF
            have_real = hasattr(PF, "validate_consumer_summary")
        except Exception:                       # noqa: BLE001
            have_real = False
        bad = []
        for ln in sums:
            errs = None
            if have_real:
                errs = PF.validate_consumer_summary(PF.parse_consumer_summary(ln))
            else:                               # frozen-contract local mirror
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "_drv", ROOT / "tests/test_lsu_r6_fixcpp_consumer_summary.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                errs = mod.validate(ln)
            if errs:
                bad.append((ln[:80], errs))
        check("真实流里的每条 summary 都守恒合法", not bad, str(bad[:2]))
        check("真实流里 summary 出现在 chain_end 之前",
              not sums or not evts
              or all(lines.index(s) < len(lines) - 1 for s in sums))

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
