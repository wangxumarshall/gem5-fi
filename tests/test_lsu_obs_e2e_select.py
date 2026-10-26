#!/usr/bin/env python3
"""test_lsu_obs_e2e_select.py — E2E kit 单测（OBS 计划 T5a，Subagent-C；
v2 适配 2026-10-13：夹具经 OC.build_l3(prop_trace_path)/OC.build_observation
产出 observation v2——masked/SDC 真实 L3 完整链、crash 截断传播链）。

覆盖：
  1  --select 对真实主树 pilot/AGU（+pilot_w1 嵌套布局）只读扫描：
     至少 1 个 Masked/SDC 与 1 个 Crash 候选、activated>0、checklist 载体
     优先、simulator_assert 优先、selection.json 只落 --record-out（绝不写
     pilot 根）；引用真实选择输出。
  2  --validate 判定逻辑（合成 campaign 树，fixtures 复用 lsu_obs_e2e 的
     _sc_build_sample/_sc_build_golden）五情形：
     (a) golden 完整 + 两样本完好 → B/D/E/F 全 PASS（CLI 退出码 0）；
         夹具真实性：masked L3=complete+propagation_trace+path_complete、
         crash L3=截断前缀（path_complete=False + 截断 caveat，仍
         complete/propagation_trace——崩溃截断语义）
     (b) masked 样本缺 fault trace（删 micro_snap.csv.gz）→ D FAIL、F FAIL，
         B/E 仍 PASS
     (c) crash 样本截断 fault ctrace 被篡改为 no_divergence → E FAIL（误报
         检出）、F FAIL，B/D 仍 PASS（CLI 退出码 1）
     (d) selection 历史 outcome 与样本 outcome 不符（同 seed 重放确定性
         不成立）→ D FAIL
     (e) masked 样本 L3 被降级为 unsupported（v1 夹具形态）→ D FAIL（kit
         侧 L3 断言 + audit v2 R1）、F FAIL，B/E 仍 PASS
  3  --self-check：篡改 files sha + chain_complete → lsu_audit 判 FAIL
     （完整性检查器有效性证明，CLI；基准样本 v2 合规，篡改检出无 R1 噪声）。
  4  同 ITEM / 不同 ITEM 的 driver 调用构造（一次调用带两个 --samples /
     两次调用）。
  5  --report：handoff_e2e.json 含 chain_complete_count/
     chain_incomplete_count（样本顶层直读）与 L3 摘要字段。

注意：真实 pilot/AGU 正被生产 campaign 并发写入——树内容会在测试期间自然
变化，故只读性以"select 代码路径仅读 + 产物仅落 record-out + pilot 根内无
selection.json"判定，不做整树前后快照（生产写入会造成假阳性）。
绝不起 gem5（全部合成/只读）。

用法：python3 tests/test_lsu_obs_e2e_select.py   （退出码 0=全 PASS）
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_obs_core as OC      # noqa: E402
import lsu_obs_e2e as E2E      # noqa: E402

ITEM = "ITEM-990"
KEY = "e" * 32
GEM5_SHA = "b" * 64
CAMPAIGN = "e2e_test"

L5_SDC = {"outcome": "SDC", "activated": 1, "injected": 1, "crash_kind": None,
          "detected_na": True, "checksum": "x", "classes": {},
          "conservation": "OK"}
L5_CRASH = {"outcome": "Crash", "activated": 1, "injected": 1,
            "crash_kind": "simulator_assert", "detected_na": True,
            "checksum": None, "classes": {}, "conservation": "OK"}


def make_selection(hist_outcome="SDC"):
    return {
        "masked_or_sdc": {"item": ITEM, "sample": 0, "outcome": hist_outcome,
                          "crash_kind": None, "activated": 1,
                          "verdict_path": "synthetic", "carrier": "se:gap_bfs",
                          "runid": "A01-F0-W9", "reason": "test"},
        "crash": {"item": ITEM, "sample": 1, "outcome": "Crash",
                  "crash_kind": "simulator_assert", "activated": 1,
                  "verdict_path": "synthetic", "carrier": "se:gap_bfs",
                  "runid": "A01-F0-W9", "reason": "test"},
        "same_item": True,
    }


def make_campaign(tmp, name, *, tamper=None):
    """合成 campaign：<tmp>/<name>/golden/<KEY> + <tmp>/<name>/<CAMPAIGN>/<ITEM>/。
    tamper: None | "missing_trace" | "misreport_no_divergence"
            | "l3_unsupported"（masked 样本 L3 降级为 v1 夹具形态）"""
    outdir = tmp / name
    E2E._sc_build_golden(outdir / "golden", KEY, GEM5_SHA)
    item_dir = outdir / CAMPAIGN / ITEM
    E2E._sc_build_sample(item_dir, ITEM, 0, L5_SDC)
    E2E._sc_build_sample(item_dir, ITEM, 1, L5_CRASH, crash_truncated=True)
    if tamper == "missing_trace":
        (item_dir / f"{ITEM}_s0" / "micro_snap.csv.gz").unlink()
    if tamper == "misreport_no_divergence":
        d = item_dir / f"{ITEM}_s1"
        obs = json.loads((d / "observation.json").read_text())
        obs["L2"]["commit_diff"]["verdict"] = "no_divergence"  # 误报
        (d / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        comp = json.loads((d / "COMPLETE").read_text())
        comp["observation_sha256"] = OC.sha256_file(d / "observation.json")
        (d / "COMPLETE").write_text(json.dumps(comp, indent=1) + "\n")
    if tamper == "l3_unsupported":
        # masked 样本 L3 降级为 v1 夹具形态（无传播证据）——存储侧四状态
        # 同步重算保持一致（chain_complete=False / missing_levels=[L3]），
        # 使 D 的失败只来自 kit 侧 L3 断言 + audit v2 R1，而非状态自相矛盾
        d = item_dir / f"{ITEM}_s0"
        obs = json.loads((d / "observation.json").read_text())
        obs["L3"] = {"status": "unsupported", "method": None,
                     "reason": "合成 v1 降级夹具：无传播证据"
                               "（非 propagation_trace）"}
        ok_, why = OC.chain_complete(obs)
        obs["chain_complete"], obs["chain_status_reason"] = ok_, why
        obs["missing_levels"] = OC.missing_levels(obs)
        obs["needs_backfill"] = bool(obs["missing_levels"])
        (d / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        comp = json.loads((d / "COMPLETE").read_text())
        comp["observation_sha256"] = OC.sha256_file(d / "observation.json")
        (d / "COMPLETE").write_text(json.dumps(comp, indent=1) + "\n")
    return outdir


def run_cli(*argv):
    return subprocess.run([sys.executable, str(WT / "tools/lsu_obs_e2e.py"),
                           *argv], capture_output=True, text=True, cwd=str(WT))


def _external_deps_missing():
    """本套件主体依赖的**真实外部产物**是否缺席（缺则诚实 SKIP，绝不谎报 PASS）。

    1) 主树真实 pilot verdict 树 runs/lsu/pilot/AGU(±pilot_w1)：--select 段
       只有它才有 Masked/SDC/Crash 候选；
    2) 冻结 gem5.opt（sha256=FROZEN_GEM5_SHA）：report 段环境指纹的复核对象。
    二者均非任何 checkout 内的可再生内容：pilot 树与主树 repo 根 build/ 同名件
    已由 R4-10 磁盘审计移除。缺任一个都无法判定 → 返回缺失物清单。"""
    missing = []
    for name, p in (("PILOT_CHECKLIST_ROOT", E2E.PILOT_CHECKLIST_ROOT),
                    ("PILOT_W1_ROOT", E2E.PILOT_W1_ROOT)):
        if not p.is_dir():
            missing.append(f"{name}={p}（目录不存在）")
    try:
        got = E2E._sha256_file(E2E.gem5_bin())
    except SystemExit as e:      # 解析到的 gem5 二进制本身缺席（高声失败）
        missing.append(f"冻结 gem5.opt 不可达：{e}")
        return missing
    if got != E2E.FROZEN_GEM5_SHA:
        missing.append(f"冻结 gem5.opt sha256={E2E.FROZEN_GEM5_SHA[:16]}… 与"
                       f"解析件 sha256={got[:16]}… 不一致")
    return missing


def main():
    missing = _external_deps_missing()
    if missing:
        for m in missing:
            print(f"[SKIP-reason] {m}")
        print(f"SKIPPED (honest, external data dependency missing): "
              f"{len(missing)} 项缺失 → 无法判定")
        return 0

    tmp = Path(tempfile.mkdtemp(prefix="lsu_e2e_test_"))
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ================= 1) --select 真实主树只读扫描 =================
    sel, cands = E2E.select_candidates()
    ms, cr = sel.get("masked_or_sdc"), sel.get("crash")
    print(f"[real-select] masked_sdc 候选 {len(cands['masked_sdc'])} 个, "
          f"crash 候选 {len(cands['crash'])} 个")
    for c in (ms, cr):
        if c:
            print(f"[real-select] ({c['item']}, s{c['sample']}, "
                  f"{c['outcome']}, {c['verdict_path']}, {c['carrier']})")
    check("select_finds_masked_or_sdc",
          ms is not None and ms["outcome"] in ("Masked", "SDC")
          and ms["activated"] and ms["sample"] >= 0, str(ms))
    check("select_finds_crash",
          cr is not None and cr["outcome"] == "Crash" and cr["activated"],
          str(cr))
    check("select_prefers_checklist_carrier",
          ms["root_kind"] == "checklist" and cr["root_kind"] == "checklist",
          f"{ms['root_kind']} {cr['root_kind']}")
    check("select_crash_prefers_simulator_assert",
          cr["crash_kind"] == "simulator_assert", str(cr["crash_kind"]))
    check("select_verdict_paths_exist",
          Path(ms["verdict_path"]).exists() and Path(cr["verdict_path"]).exists(),
          f"{ms['verdict_path']} {cr['verdict_path']}")
    check("select_same_item_flag_present", isinstance(sel.get("same_item"), bool))
    check("select_runid_family_resolved",
          ms.get("runid") and ms.get("family"), str(ms))

    # CLI --select --record-out（绝不写 pilot 根；记录只落 tmp）
    rec = tmp / "sel_record.json"
    r = run_cli("--select", "--campaign", "e2e_select_test",
                "--record-out", str(rec))
    check("select_cli_rc0", r.returncode == 0,
          f"rc={r.returncode} {r.stderr[-300:]}")
    check("select_cli_prints_real_choice",
          "选择[Masked/SDC" in r.stdout and "选择[Crash" in r.stdout
          and "载体" in r.stdout, r.stdout[-600:])
    sel_file = json.loads(rec.read_text())
    check("select_record_consistent",
          sel_file["masked_or_sdc"]["item"] == ms["item"]
          and sel_file["masked_or_sdc"]["sample"] == ms["sample"]
          and sel_file["crash"]["item"] == cr["item"]
          and sel_file["crash"]["sample"] == cr["sample"],
          str(sel_file)[:300])
    check("select_no_write_into_pilot_roots",
          not any(Path(p, "selection.json").exists()
                  for p in (E2E.PILOT_CHECKLIST_ROOT, E2E.PILOT_W1_ROOT)),
          "pilot 根内出现 selection.json")
    check("select_pilot_w1_nested_layout_scanned",
          any("嵌套" in v for v in sel["scan_roots"].values()),
          str(sel["scan_roots"]))

    # ================= 4) driver 调用构造 =================
    argv = E2E.driver_argv(CAMPAIGN, tmp, ITEM, [0, 1])
    argv_real = E2E.driver_argv(CAMPAIGN, E2E.OUTDIR_ROOT, ITEM, [0, 1])
    check("driver_argv_shape",
          "--samples" in argv and "0" in argv and "1" in argv
          and "--replay-policy" in argv and "per_sample" in argv
          and "--phase" in argv and "screening" in argv
          and "--outdir-root" in argv and str(tmp) in argv,
          " ".join(argv))
    check("driver_argv_default_outdir_is_main_obs",
          str(E2E.OUTDIR_ROOT) in " ".join(argv_real)
          and str(WT / "tools/lsu_obs_driver.py") in " ".join(argv_real),
          " ".join(argv_real))
    # 同 ITEM 一次调用两个样本；不同 ITEM 两次调用（构造校验）
    sel2 = make_selection()
    plans_same = [([sel2["masked_or_sdc"]["item"]],
                   [sel2["masked_or_sdc"]["sample"],
                    sel2["crash"]["sample"]])]
    check("plan_same_item_single_call",
          len(plans_same) == 1 and len(plans_same[0][1]) == 2)
    sel3 = make_selection()
    sel3["crash"] = dict(sel3["crash"], item="ITEM-991")
    plans_diff = [([sel3["masked_or_sdc"]["item"]],
                   [sel3["masked_or_sdc"]["sample"]]),
                  ([sel3["crash"]["item"]], [sel3["crash"]["sample"]])]
    check("plan_diff_item_two_calls", len(plans_diff) == 2)

    # ================= 2) --validate 合成 campaign 四情形 =================
    def vrun(outdir, selection):
        lines, ok = E2E.validate_campaign(CAMPAIGN, outdir, GEM5_SHA, selection)
        return {l["class"]: l for l in lines}, ok

    # (a) golden 完整 → 全 PASS
    out_a = make_campaign(tmp, "case_a")
    la, ok_a = vrun(out_a, make_selection())
    check("caseA_all_pass", ok_a and all(l["pass"] for l in la.values()),
          json.dumps({k: v["detail"] for k, v in la.items()}, ensure_ascii=False))
    check("caseA_D_detail", "outcome=SDC" in la["D"]["detail"]
          and "replay=verified" in la["D"]["detail"]
          and "L3=complete(propagation_trace)" in la["D"]["detail"],
          la["D"]["detail"])
    check("caseA_E_honest_truncation",
          "not_observed_before_crash" in la["E"]["detail"]
          and "truncated_no_divergence_in_prefix" in la["E"]["detail"]
          and "L3=propagation_trace" in la["E"]["detail"]
          and "path_complete=False" in la["E"]["detail"],
          la["E"]["detail"])
    # v2 夹具真实性：masked=真实 L3 完整链 / crash=截断传播链（崩溃截断
    # 语义：path_complete=False + 截断 caveat，仍 complete/propagation_trace）
    obs_ms = json.loads((out_a / CAMPAIGN / ITEM / f"{ITEM}_s0"
                         / "observation.json").read_text())
    obs_cr = json.loads((out_a / CAMPAIGN / ITEM / f"{ITEM}_s1"
                         / "observation.json").read_text())
    check("fixture_masked_l3_real",
          obs_ms["schema"] == "lsu-observation-v2"
          and obs_ms["L3"]["status"] == "complete"
          and obs_ms["L3"]["method"] == "propagation_trace"
          and obs_ms["L3"]["evidence"]["path_complete"] is True
          and obs_ms["chain_complete"] is True
          and any(f["name"] == "prop_trace.csv.gz" for f in obs_ms["files"]),
          json.dumps(obs_ms.get("L3"), ensure_ascii=False)[:300])
    check("fixture_crash_l3_truncation_semantics",
          obs_cr["schema"] == "lsu-observation-v2"
          and obs_cr["L3"]["status"] == "complete"
          and obs_cr["L3"]["method"] == "propagation_trace"
          and obs_cr["L3"]["truncated"] is True
          and obs_cr["L3"]["evidence"]["path_complete"] is False
          and obs_cr["L3"]["evidence"]["first_errant_commit"] is None
          and any("截断" in c for c in obs_cr["L3"]["caveats"])
          and obs_cr["chain_complete"] is False,  # 二轮规则 1：crash 截断 path_complete=False → chain=false
          json.dumps(obs_cr.get("L3"), ensure_ascii=False)[:300])

    # (b) masked 缺 fault trace → D/F FAIL，B/E PASS
    out_b = make_campaign(tmp, "case_b", tamper="missing_trace")
    lb, ok_b = vrun(out_b, make_selection())
    check("caseB_overall_fail", not ok_b)
    check("caseB_D_fail_missing_trace",
          not lb["D"]["pass"] and ("msnap" in lb["D"]["detail"]
                                   or "audit FAIL" in lb["D"]["detail"]),
          lb["D"]["detail"])
    check("caseB_B_E_still_pass", lb["B"]["pass"] and lb["E"]["pass"],
          f"B={lb['B']['detail']} E={lb['E']['detail']}")
    check("caseB_F_fail_audit", not lb["F"]["pass"]
          and "audit FAIL" in lb["F"]["detail"], lb["F"]["detail"])

    # (c) crash 截断被误报 no_divergence → E/F FAIL，B/D PASS
    out_c = make_campaign(tmp, "case_c", tamper="misreport_no_divergence")
    lc, ok_c = vrun(out_c, make_selection())
    check("caseC_overall_fail", not ok_c)
    check("caseC_E_fail_misreport",
          not lc["E"]["pass"] and "no_divergence" in lc["E"]["detail"],
          lc["E"]["detail"])
    check("caseC_B_D_still_pass", lc["B"]["pass"] and lc["D"]["pass"],
          f"B={lc['B']['detail']} D={lc['D']['detail']}")
    check("caseC_F_fail", not lc["F"]["pass"], lc["F"]["detail"])

    # (d) 历史 outcome 不符（同 seed 重放确定性不成立）→ D FAIL
    out_d = make_campaign(tmp, "case_d")
    ld, ok_d = vrun(out_d, make_selection(hist_outcome="Masked"))
    check("caseD_outcome_mismatch_fails_D",
          not ok_d and not ld["D"]["pass"]
          and "历史 verdict" in ld["D"]["detail"], ld["D"]["detail"])

    # (e) masked 样本 L3 降级为 unsupported（v1 夹具形态）→ D FAIL（kit 侧
    # L3 断言 + audit v2 R1）、F FAIL，B/E 仍 PASS
    out_e = make_campaign(tmp, "case_e", tamper="l3_unsupported")
    le, ok_e = vrun(out_e, make_selection())
    check("caseE_overall_fail", not ok_e)
    check("caseE_l3_degraded_fails_D",
          not le["D"]["pass"] and "L3" in le["D"]["detail"]
          and "propagation_trace" in le["D"]["detail"]
          and "audit FAIL" in le["D"]["detail"], le["D"]["detail"])
    check("caseE_B_E_still_pass", le["B"]["pass"] and le["E"]["pass"],
          f"B={le['B']['detail']} E={le['E']['detail']}")
    check("caseE_F_fail_r1", not le["F"]["pass"]
          and "L3_unsupported_for_activated_sample" in le["F"]["detail"],
          le["F"]["detail"])

    # CLI --validate：case_a 退出码 0 / case_c 退出码 1（需 selection.json）
    for outdir, expect_rc, tag in ((out_a, 0, "caseA"), (out_c, 1, "caseC")):
        (outdir / CAMPAIGN).mkdir(parents=True, exist_ok=True)
        (outdir / CAMPAIGN / "selection.json").write_text(
            json.dumps(make_selection(), ensure_ascii=False, indent=1))
        rv = run_cli("--validate", "--campaign", CAMPAIGN,
                     "--outdir-root", str(outdir),
                     "--expect-gem5-sha", GEM5_SHA)
        check(f"validate_cli_{tag}_rc{expect_rc}",
              rv.returncode == expect_rc,
              f"rc={rv.returncode} {rv.stdout[-400:]}")
        check(f"validate_cli_{tag}_four_lines",
              all(f"验收 {c}:" in rv.stdout for c in "BDEF"), rv.stdout[-400:])

    # --report（case_a）：handoff 落盘
    rr = run_cli("--report", "--campaign", CAMPAIGN, "--outdir-root",
                 str(out_a), "--expect-gem5-sha", GEM5_SHA)
    hj, hm = out_a / CAMPAIGN / "handoff_e2e.json", \
        out_a / CAMPAIGN / "handoff_e2e.md"
    check("report_cli_writes_handoff",
          rr.returncode == 0 and hj.exists() and hm.exists(),
          rr.stdout[-300:])
    doc = json.loads(hj.read_text())
    # 环境指纹：真实 gem5 二进制 sha 恒被记录；本合成用例 expect="b"*64
    # ≠ 真实二进制 → matches_frozen 诚实为 False（生产 expect=冻结 sha 时 True）
    check("report_contents",
          doc["acceptance_all_pass"] is True
          and doc["selection"]["masked_or_sdc"]["item"] == ITEM
          and doc["samples"]["masked_or_sdc"]["outcome"] == "SDC"
          and doc["samples"]["crash"]["L2_status"]
          == "not_observed_before_crash"
          and doc["samples"]["masked_or_sdc"]["L3_status"] == "complete"
          and doc["samples"]["masked_or_sdc"]["L3_method"]
          == "propagation_trace"
          and doc["samples"]["masked_or_sdc"]["L3_path_complete"] is True
          and doc["samples"]["crash"]["L3_method"] == "propagation_trace"
          and doc["samples"]["crash"]["L3_path_complete"] is False
          and doc["chain_complete_count"] == 1  # 二轮规则 1 后：仅 Masked（errant 抵达）计 true
          and doc["chain_incomplete_count"] == 1  # crash 截断 path_complete=False → false（二轮规则 1）
          and doc["environment"]["gem5_opt_sha256"] == E2E.FROZEN_GEM5_SHA
          and doc["environment"]["gem5_sha_matches_frozen"] is False
          and doc["environment"]["expect_gem5_sha256"] == GEM5_SHA,
          json.dumps(doc, ensure_ascii=False)[:400])

    # 样本 COMPLETE 判定（driver rc=0 不代表完成——GUARD_FAILURE 仍退 0）
    done_a, miss_a = E2E._samples_complete(out_a, CAMPAIGN, make_selection())
    check("samples_complete_detects_done", done_a and miss_a is None,
          str(miss_a))
    empty_out = tmp / "case_empty"          # 空 campaign：无任何 COMPLETE 样本
    (empty_out / CAMPAIGN / ITEM).mkdir(parents=True, exist_ok=True)
    done_e, miss_e = E2E._samples_complete(empty_out, CAMPAIGN,
                                           make_selection())
    check("samples_complete_detects_missing",
          done_e is False and miss_e is not None
          and miss_e.name == f"{ITEM}_s0", str(miss_e))

    # ================= 3) --self-check CLI =================
    rs = run_cli("--self-check")
    check("selfcheck_cli", rs.returncode == 0
          and "SELF-CHECK: PASS" in rs.stdout
          and "tampered_sample_fails_audit" in rs.stdout,
          f"rc={rs.returncode} {rs.stdout[-400:]}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
