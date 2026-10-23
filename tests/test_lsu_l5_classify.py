#!/usr/bin/env python3
"""test_lsu_l5_classify.py — L5 结局记录缺口单测（L18-v2 / [R6-ORACLE] G1/G3/G4/G6/G7）。

审计缺陷（每条一测试组，RED→GREEN 证据在 plan 文件里）：
  G1 Crash 只记 crash_kind——无 detection_layer、无检测点（tick/PC/…）、
     无污染链关联。
  G3 缺 stdout → INCONCLUSIVE 早退于 activated 赋值之前（activated 丢失）。
  G4 activated=1 + RC=0 + 与 golden 相符 → Masked，且无 oracle_diff
     （禁止的"activated=1/RC=0 即 READY"泄漏源）。
  G6 只懂 16-hex/w1-fnv 校验和；非哈希 oracle（ARRAYHASH/ELEMDIFF/ULP）
     的运行 checksum=None → 误判 Crash。
  G7 Detected/Contained 硬编码 0（detected_na=True），五类分栏缺一类。

用法：python3 tests/test_lsu_l5_classify.py [--only SUBSTR]
退出码 0 = 全 PASS。
"""
import argparse
import gzip
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
TOOLS = WT / "tools"
L5 = TOOLS / "lsu_l5_classify.py"
sys.path.insert(0, str(TOOLS))
import lsu_l5_classify as L5C   # noqa: E402

FUNNEL = ("CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
          "injected=1 activated=1")
CKSUM = "0123456789abcdef"
GOLDEN = "0123456789abcdef"
OTHER = "fedcba9876543210"

# 注入日志行（s319 实测格式）+ FUNNEL 行
INJLINE = ("Tick: 887040, Site: lsq_sendFragmentToTranslation, "
           "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
           "new_vaddr=0x87ffffefd00, faults_injected: 1")
LOGFUNNEL = "FUNNEL: attempted=1 eligible=265143 injected=1"

PROP_HEADER = ("# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,"
               "request_id,addr,phys_reg,arch_reg,detail\n")
PROP_CHAIN = PROP_HEADER + (
    "0,123450,1,inj,77,,1a2b3000,,,site=lsq_pushRequest_PRE;family=addrpath\n"
    "1,124000,1,mem_req,77,77,1a2b3008,,,site=lsq_sendFragmentToTranslation\n"
    "2,130000,1,resp,77,77,1a2b3008,,,family=addrpath;data_fnv=0123\n"
    "3,130001,1,taint_reg,77,77,1a2b3008,42,5,class=int;dest_idx=0\n"
    "4,140000,1,errant_commit,90,,,,,trigger=first_consumer;pc=8f00\n"
)


def ns(tmp, stdout=None, stderr=None, golden=None, exit_code=0,
       timed_out=False, run_dir=None, injlog=None, prop_trace=None,
       extra=(), name="s"):
    """构造 classify(args) 的 Namespace（直接调用，快）。"""
    sp = ep = None
    if stdout is not None:
        sp = tmp / f"{name}.stdout"
        sp.write_text(stdout)
    if stderr is not None:
        ep = tmp / f"{name}.stderr"
        ep.write_text(stderr)
    rd = Path(run_dir) if run_dir else tmp
    if injlog is not None:
        rd.mkdir(parents=True, exist_ok=True)
        (rd / f"{name}_injections.log").write_text(injlog)
    ptp = None
    if prop_trace is not None:
        ptp = tmp / f"{name}_prop.csv.gz"
        with gzip.open(ptp, "wt") as f:
            f.write(prop_trace)
    a = argparse.Namespace(
        run_dir=str(rd), stdout=(str(sp) if sp else None),
        stderr=(str(ep) if ep else None), golden=golden,
        exit=exit_code, timed_out=timed_out, json=None,
        prop_trace=(str(ptp) if ptp else None),
        oracle_kind="exact_hash", oracle_tol=0,
        detected_layer=None, contained=False)
    for k, v in extra:
        setattr(a, k, v)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="l5cls_test_"))
    fails = []

    def check(name, cond, detail=""):
        if args.only and args.only not in name:
            return
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ---------- 基线：现有行为（回归护栏，必须继续成立） ----------
    r = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n", golden=GOLDEN,
                        name="base"))
    check("base_masked", r["outcome"] == "Masked" and r["activated"] == 1
          and r["conservation"] == "OK", str(r))
    r = L5C.classify(ns(tmp, FUNNEL + "\n" + OTHER + "\n", golden=GOLDEN,
                        name="base_sdc"))
    check("base_sdc", r["outcome"] == "SDC", str(r))

    # ================= G1: Crash 检测点/detection_layer/污染链 =================
    assert_out = (FUNNEL + "\n"
                  "gem5.opt: build/ARM/arch/arm/tlb.cc:512: Assertion "
                  "`pd != nullptr' failed.\n"
                  "exiting @ tick 1234567 because simulate() limit reached\n")
    assert_err = ("gem5.opt: build/ARM/arch/arm/tlb.cc:512: Assertion "
                  "`pd != nullptr' failed.\n")
    g1 = L5C.classify(ns(tmp, assert_out, assert_err, exit_code=134,
                         injlog=LOGFUNNEL + "\n" + INJLINE + "\n", name="g1"))
    check("g1_crash_kind_kept",
          g1["outcome"] == "Crash" and g1["crash_kind"] == "simulator_assert",
          str(g1))
    check("g1_detection_layer_present",
          g1.get("detection_layer") == "None",
          f"detection_layer={g1.get('detection_layer')!r}")
    dp = g1.get("detection_point") or {}
    check("g1_detection_point_tick_pc",
          dp.get("tick") == 1234567 and dp.get("kind") == "simulator_assert",
          str(dp))
    check("g1_detection_point_detail_nonempty",
          bool(dp.get("detail")) and "Assertion" in (dp.get("detail") or ""),
          str(dp))
    check("g1_fault_linkage",
          (g1.get("fault_linkage") or {}).get("injected_tick") == 887040
          and (g1.get("fault_linkage") or {}).get("injected_site")
          == "lsq_sendFragmentToTranslation",
          str(g1.get("fault_linkage")))
    check("g1_taint_chain_not_provided",
          (g1.get("taint_chain") or {}).get("status") == "not_provided",
          str(g1.get("taint_chain")))
    # 客人 trap → OS 检测层；trap 标记即检测点
    gt = L5C.classify(ns(tmp, FUNNEL + "\ntaking exception\n",
                         "Illegal instruction (kernel trap)\n", exit_code=1,
                         name="g1b"))
    check("g1_guest_trap_layer_os",
          gt["outcome"] == "Crash" and gt.get("detection_layer") == "OS"
          and (gt.get("detection_point") or {}).get("kind") == "arch_trap",
          str((gt.get("detection_layer"), gt.get("detection_point"))))
    # 给了 prop_trace → 污染链关联（taint 终点 + ptag）
    g1p = L5C.classify(ns(tmp, assert_out, assert_err, exit_code=134,
                          prop_trace=PROP_CHAIN, name="g1p"))
    tc = g1p.get("taint_chain") or {}
    check("g1_taint_chain_linked",
          tc.get("status") == "linked" and tc.get("terminal_kind")
          in ("errant_commit", "consumer", "taint_reg")
          and tc.get("ptag") == 1, str(tc))

    # ================= G3: 缺 stdout 不丢 activated =================
    missing = str(tmp / "does_not_exist.stdout")
    g3 = L5C.classify(ns(tmp, None, None, exit_code=0, name="g3",
                         injlog=LOGFUNNEL + "\n" + INJLINE + "\n"))
    g3["_missing_stdout"] = missing
    # 重来一次：显式给不存在的 stdout 路径
    a3 = ns(tmp, None, None, exit_code=0, name="g3",
            injlog=LOGFUNNEL + "\n" + INJLINE + "\n")
    a3.stdout = missing
    g3 = L5C.classify(a3)
    check("g3_inconclusive",
          g3["outcome"] == "INCONCLUSIVE" and bool(g3.get("error")), str(g3))
    check("g3_activated_recorded",
          g3.get("activated") == 1 and g3.get("injected") == 1,
          f"activated={g3.get('activated')} injected={g3.get('injected')}")
    check("g3_error_class",
          g3.get("error_class") == "input_incomplete", str(g3.get("error_class")))

    # ================= G4: oracle_diff + 无 golden 不得判 Masked =================
    g4m = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n", golden=GOLDEN,
                          name="g4m"))
    od = g4m.get("oracle_diff") or {}
    check("g4_oracle_diff_masked",
          od.get("compared") is True and od.get("match") is True
          and od.get("kind") == "exact_hash" and od.get("observed") == CKSUM,
          str(od))
    g4s = L5C.classify(ns(tmp, FUNNEL + "\n" + OTHER + "\n", golden=GOLDEN,
                          name="g4s"))
    check("g4_oracle_diff_sdc",
          g4s["outcome"] == "SDC"
          and (g4s.get("oracle_diff") or {}).get("match") is False,
          str(g4s.get("oracle_diff")))
    # 无 golden：RC=0 + 有 checksum——旧代码判 Masked（泄漏源）
    g4n = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n", golden=None,
                          name="g4n"))
    check("g4_no_golden_not_masked",
          g4n["outcome"] != "Masked"
          and (g4n.get("oracle_diff") or {}).get("compared") is False,
          f"outcome={g4n['outcome']} od={g4n.get('oracle_diff')}")
    check("g4_no_golden_loud",
          g4n["outcome"] == "INCONCLUSIVE" and bool(g4n.get("error")),
          str(g4n.get("error")))

    # ================= G6: 非哈希 oracle =================
    ah = "a" * 64
    g6a = L5C.classify(ns(tmp, FUNNEL + "\nARRAYHASH=" + ah + "\n",
                          golden=ah, exit_code=0, name="g6a"))
    check("g6_arrayhash_not_crash",
          g6a["outcome"] in ("Masked", "SDC") and g6a["outcome"] != "Crash",
          f"outcome={g6a['outcome']}")
    check("g6_arrayhash_kind_autodetected",
          (g6a.get("oracle_diff") or {}).get("kind") == "array_hash"
          and g6a.get("oracle_kind_source") == "auto_detected",
          str((g6a.get("oracle_diff"), g6a.get("oracle_kind_source"))))
    check("g6_arrayhash_masked",
          g6a["outcome"] == "Masked"
          and (g6a.get("oracle_diff") or {}).get("match") is True, str(g6a))
    g6b = L5C.classify(ns(tmp, FUNNEL + "\nELEMDIFF n=3 first=7 maxulp=0\n",
                          golden="0", exit_code=0, name="g6b"))
    check("g6_elemdiff_sdc",
          g6b["outcome"] == "SDC"
          and (g6b.get("oracle_diff") or {}).get("kind") == "per_element_diff",
          str(g6b.get("oracle_diff")))
    g6c = L5C.classify(ns(tmp, FUNNEL + "\nULP=2\n", golden="0", name="g6c",
                          extra=[("oracle_kind", "fp_ulp"),
                                 ("oracle_tol", 4)]))
    check("g6_ulp_within_tol_masked", g6c["outcome"] == "Masked", str(g6c))
    g6d = L5C.classify(ns(tmp, FUNNEL + "\nULP=9\n", golden="0", name="g6d",
                          extra=[("oracle_kind", "fp_ulp"),
                                 ("oracle_tol", 4)]))
    check("g6_ulp_over_tol_sdc", g6d["outcome"] == "SDC", str(g6d))
    # exit=0、无任何 oracle 行 → 响亮拒判（绝不判 Crash）
    g6e = L5C.classify(ns(tmp, FUNNEL + "\nno oracle here\n", golden="0",
                          exit_code=0, name="g6e"))
    check("g6_no_oracle_line_loud",
          g6e["outcome"] != "Crash" and g6e["outcome"] == "INCONCLUSIVE"
          and bool(g6e.get("error")), f"{g6e['outcome']} {g6e.get('error')}")

    # ================= G7: Detected/Contained 可被填充 =================
    sig = ("CHAOS_DETECT: layer=Hardware RAS contained=1 tick=99 ptag=7 "
           "reason=ECC_CE_corrected\n")
    g7 = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n" + sig,
                         golden=GOLDEN, name="g7"))
    check("g7_detected_contained_outcome",
          g7["outcome"] == "Detected/Contained"
          and g7["classes"]["Detected/Contained"] == g7["activated"],
          str((g7["outcome"], g7.get("classes"))))
    check("g7_detected_layer_from_signal",
          g7.get("detection_layer") == "Hardware RAS"
          and g7.get("detected_na") is False, str(g7.get("detection_layer")))
    check("g7_conservation_ok", g7["conservation"] == "OK", str(g7))
    # 无检测器信号 → n/a 显式（不得静默零）
    g7n = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n", golden=GOLDEN,
                          name="g7n"))
    check("g7_no_signal_na_explicit",
          g7n.get("detected_na") is True
          and "Detected/Contained" in (g7n.get("classes_na") or [])
          and g7n.get("detection_layer") is None,
          str((g7n.get("detected_na"), g7n.get("classes_na"),
               g7n.get("detection_layer"))))
    # 显式 CLI 检测层（驱动/未来接线可传）
    g7c = L5C.classify(ns(tmp, FUNNEL + "\n" + CKSUM + "\n", golden=GOLDEN,
                          name="g7c",
                          extra=[("detected_layer", "OS"),
                                 ("contained", True)]))
    check("g7_cli_detector",
          g7c.get("detection_layer") == "OS"
          and g7c["outcome"] == "Detected/Contained", str(g7c.get("outcome")))

    # ================= CLI 端到端冒烟（子进程，真参数解析） =================
    sp = tmp / "cli.stdout"
    sp.write_text(FUNNEL + "\n" + CKSUM + "\n")
    r = subprocess.run([sys.executable, str(L5), "--run-dir", str(tmp),
                        "--stdout", str(sp), "--golden", GOLDEN,
                        "--exit", "0"], capture_output=True, text=True)
    m = re.search(r"LSU_L5: (\{.*\})", r.stdout)
    check("cli_smoke_rc_and_json",
          r.returncode == 0 and m is not None
          and json.loads(m.group(1))["outcome"] == "Masked",
          f"rc={r.returncode} out={r.stdout[-200:]} rc_err={r.stderr[-200:]}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
