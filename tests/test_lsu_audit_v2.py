#!/usr/bin/env python3
"""test_lsu_audit_v2.py — 审计器 v2 规则集专测（OBS 纠偏轮 Subagent-C，
中央纠偏指令 2026-10-13）。

六条强制 FAIL 规则 + R7/R8/R9 附加规则的**双向**用例（每规则一个违规
样本断言 FAIL+token，配一个合规样本断言不触发——证明检查器不是无条件
FAIL）+ v1/v2 模式切换 + schema 版本规则。

fixture 纪律：全部手工按 v2 契约合成（顶层 schema/execution_complete/
evidence_complete/needs_backfill/missing_levels + L3 {complete,
propagation_trace} + L4 detector=not_present + L0 四字段）——**不 import
B 并行实现的 obs_core v2**；轨迹文件是真实 gzip（审计器现场 gz_probe
复核的对象），COMPLETE 标记 observation_sha256 对齐。全部建在系统临时
目录，绝不触碰真实 runs/，不跑 gem5。

样本表（camp/ITEM-902）：
  s0  合规 full v2（L3 complete+propagation_trace）→ v2 PASS（全规则的
      PASS 侧：无任何规则 token）
  s1  合规 inactive v2（L1-L4 N/A(inactive)，L3.method=None，L4 无
      detector 键）→ v2 PASS
  s2  R1 违规：L3 unsupported/method=None（activated=1）→ FAIL
      L3_unsupported_for_activated_sample（且仅此规则触发——精确性）
  s3  R2 违规：L0.attempted=None → FAIL L0_funnel_incomplete
  s4  R3 违规：commit_trace.csv.gz 现场清空（L2.status=complete，
      files sha 重对齐）→ FAIL evidence_trace_unreadable（现场复核
      独立于记录态证据——记录态 probe error 仍是 None）
  s5  R3 例外（双向）：L2.status=not_observed_before_crash + 空 fault
      trace + L5 Crash → v2 **PASS** + note（W2.1 批量 flush 契约的
      诚实结果，v1 已有此例外，保留）
  s6  R4 违规：记录态 L2.fault rows=0（error=None）+ commit_diff
      diverged/points=3 → FAIL empty_trace_fake_divergence（BUG-4
      类：空 trace 报真实 divergence；磁盘文件完好以隔离 R3）
  s7  R5a 违规：L5.classes['Detected/Contained']=1 且 detected_na=True
      → FAIL detector_na_counted_as_detected
  s8  R5b 违规：L4.detected=True 且 detector='not_present' → FAIL
      detector_na_counted_as_detected
  s9  R6 条款1违规：chain_complete=True 且 missing_levels=['L4'] →
      FAIL chain_complete_with_degraded_layer（重算仍一致——只此规则）
  s10 R6 条款3违规：chain_complete=True 且 L3.method='proxy' → FAIL
      chain_complete_with_degraded_layer（R1/recompute mismatch 必然
      共触发——内部矛盾样本，见断言注释）
  s11 R7 违规：schema='lsu-observation-v1' → FAIL
      schema_version_pre_correction（reason 须含"纠偏前历史样本"如实
      FAIL 措辞）
  s12 R8 违规：缺 needs_backfill → FAIL contract_v2_fields_missing
  s13 R9 违规：L4.detector='none_wired' → FAIL
      L4_detector_v1_value_none_wired

模式切换（v1|v2 同树）：v1 模式下 s2/s3/s6/s7/s8/s9/s10/s11/s12/s13
全部 PASS（它们只违反 v2 规则——历史审计看不见这些降级，正是纠偏的
理由）；唯一例外 s4（空 trace 不可读在 v1 检查 (v) 下也 FAIL）。
s2 在 v1 PASS / v2 FAIL 是"当前 E2E 样本全 chain_complete=false 不得
算数"的最小复现。

用法：python3 tests/test_lsu_audit_v2.py   （退出码 0=全 PASS）
"""
import gzip
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_audit as A          # noqa: E402
import lsu_obs_core as C       # noqa: E402  仅用 sha256_file（基点 v1 工具函数）
from lsu_seed import lsu_seed  # noqa: E402

RUNID = "V2T-F0-W1"
PHASE = "screening"
ITEM = "ITEM-902"
FUNNEL = ("CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
          "injected=1 activated=1")
FUNNEL_INACTIVE = ("CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=0 "
                   "injected=0")
INJ_LINE = ("Tick: 887040, Site: lsq_sendFragmentToTranslation, "
            "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
            "new_vaddr=0x87ffffefd00, faults_injected: 1")

RULE_TOKENS = ["L3_unsupported_for_activated_sample", "L0_funnel_incomplete",
               "evidence_trace_unreadable", "empty_trace_fake_divergence",
               "detector_na_counted_as_detected",
               "chain_complete_with_degraded_layer",
               "schema_version_pre_correction", "contract_v2_fields_missing",
               "L4_detector_v1_value_none_wired"]


def ctr_line(seq, val="0000000000000001"):
    return f"{seq},0,{100 + seq},400080,add,1,1,5,66,{val}"


def write_gz(path, lines):
    with gzip.open(path, "wt") as f:
        for l in lines:
            f.write(l + "\n")


def make_l5(outcome, activated, eligible=None):
    return {"outcome": outcome, "activated": activated, "injected": activated,
            "attempted": 1, "eligible": (265143 if activated else 0)
            if eligible is None else eligible,
            "crash_kind": "guest_or_unknown" if outcome == "Crash" else None,
            "timed_out": outcome == "Timeout", "detected_na": True,
            "checksum": "0123456789abcdef",
            "classes": {"Masked": 1 if outcome == "Masked" else 0,
                        "Detected/Contained": 0, "SDC": 1 if outcome == "SDC" else 0,
                        "Crash": 1 if outcome == "Crash" else 0,
                        "Timeout": 1 if outcome == "Timeout" else 0},
            "conservation": "OK", "first_detection_source": "None"}


def build_v2_sample(camp, s, *, inactive=False, outcome="SDC", mutate=None,
                    chain_override=None):
    """手工按 v2 契约合成一个 COMPLETE 样本（不 import B 的 v2 实现）。

    mutate(obs, d) 在 files 清单计算前执行（文件级 mutation 的 sha 自动
    重对齐，隔离出被测规则）；chain_override 非 None 时覆盖重算值（R6
    内部矛盾样本用）。
    """
    d = camp / ITEM / f"{ITEM}_s{s}"
    d.mkdir(parents=True, exist_ok=True)
    ref_lines = [ctr_line(i) for i in range(6)]
    fault_lines = list(ref_lines)
    fault_lines[2] = ctr_line(2, val="ffffffffffffffff")
    write_gz(d / "ref_commit_trace.csv.gz", ref_lines)
    write_gz(d / "ref_micro_snap.csv.gz", [f"snap,{i}" for i in range(4)])
    if inactive:
        (d / "gem5.out").write_text(FUNNEL_INACTIVE + "\n")
        (d / "addrpath_injections.log").write_text("")
        file_names = ["addrpath_injections.log", "gem5.out",
                      "l5_verdict.json"]
    else:
        write_gz(d / "commit_trace.csv.gz", fault_lines)
        write_gz(d / "micro_snap.csv.gz", [f"snap,{i}" for i in range(4)])
        (d / "gem5.out").write_text(FUNNEL + "\n")
        (d / "addrpath_injections.log").write_text(INJ_LINE + "\n")
        file_names = ["addrpath_injections.log", "commit_trace.csv.gz",
                      "micro_snap.csv.gz", "gem5.out", "l5_verdict.json",
                      "ref_commit_trace.csv.gz", "ref_micro_snap.csv.gz"]
    l5 = make_l5("Masked" if inactive else outcome,
                 activated=0 if inactive else 1)
    (d / "l5_verdict.json").write_text(
        json.dumps(l5, ensure_ascii=False, indent=1))

    def probe(name, rows):
        return {"path": name, "bytes": (d / name).stat().st_size,
                "rows": rows, "truncated": False, "readable": True,
                "error": None}

    if inactive:
        l1 = {"status": "N/A(inactive_no_activation)",
              "reason": "activated=0"}
        l2 = {"status": "N/A(inactive_no_activation)",
              "reason": "activated=0"}
        l3 = {"status": "N/A(inactive_no_activation)", "method": None,
              "reason": "activated=0"}
        l4 = {"status": "N/A(inactive_no_activation)",
              "reason": "activated=0"}
    else:
        l1 = {"status": "complete", "ref": probe("ref_micro_snap.csv.gz", 4),
              "fault": probe("micro_snap.csv.gz", 4),
              "micro_diff": {"no_divergence": False,
                             "first_divergence_snap_seq": 2}}
        l2 = {"status": "complete", "ref": probe("ref_commit_trace.csv.gz", 6),
              "fault": probe("commit_trace.csv.gz", 6),
              "commit_diff": {
                  "verdict": "diverged", "primary_class": "value_error",
                  "latency_seq": 2,
                  "first_errant_commit": {"seq": 2, "class": "value_error",
                                          "tick": 102},
                  "total_divergence_points": 1,
                  "divergence_counts": {"value_error": 1}, "tick_tol": 0,
                  "aligned_pairs": 6, "ref_instructions": 6,
                  "run_instructions": 6, "ref_truncated": False,
                  "run_truncated": False, "aux": {}}}
        l3 = {"status": "complete", "method": "propagation_trace",
              "correlation_keys": ["dynInstSeqNum", "request_id", "ptag"],
              "evidence": {"path_complete": True, "terminal_verified": True,
                           "terminal": {"kind": "errant_commit",
                                        "node_id": 9, "dyn_inst_seq": 412,
                                        "tick": 102},
                           "terminal_reason": None,
                           "first_errant_commit": {"node_id": 9,
                                                   "dyn_inst_seq": 412,
                                                   "tick": 102}},
              "caveats": []}
        l4 = {"status": "complete", "detector": "not_present",
              "detected": False, "detected_na": True,
              "l4_source": "first_verifiable_anomaly",
              "first_anomaly": {"source": "L2", "tick": 102, "seq": 2,
                                "latency_ticks_from_first_injection": 0}}
    l0 = {"attempted": 1, "eligible": 0 if inactive else 265143,
          "injected": 0 if inactive else 1,
          "activated": 0 if inactive else 1, "funnel_source": "stdout",
          "injections": [] if inactive else [
              {"tick": 887040, "site": "lsq_sendFragmentToTranslation",
               "mode": "low_bit_flip", "faults": 1, "field": "vaddr->vaddr",
               "old": "0x7ffffefd00", "new": "0x87ffffefd00",
               "dynamic_target": "vaddr", "raw": INJ_LINE}]}
    obs = {
        "schema": A.SCHEMA_V2,
        "identity": {
            "campaign": "audit_v2_t", "item": ITEM, "runid": RUNID,
            "sample": f"s{s}", "seed": lsu_seed(RUNID, PHASE, s),
            "phase": PHASE, "git_commit": "a" * 40,
            "gem5_opt_sha256": "b" * 64, "lsu_proxy_sha256": "c" * 64,
            "workload": "se:gap_bfs", "workload_sha256": "d" * 64,
            "config_family": "C4-LSU", "pythonhashseed": 0,
            "baseline_key": "e" * 32, "obs_mode": "full",
            "coverage_scope": "full_run"},
        "L0": l0, "L1": l1, "L2": l2, "L3": l3, "L4": l4, "L5": dict(l5),
        "replay_determinism": {"policy": "per_sample", "verified": True,
                               "evidence": {}},
        "violations": [], "degradations": [],
        # v2 契约顶层字段（中央指令 2026-10-13；mutate 在此后执行——
        # m_r8 删除 needs_backfill / m_r6c1 改写 missing_levels）
        "execution_complete": True, "evidence_complete": True,
        "needs_backfill": False, "missing_levels": [],
    }
    if mutate:
        mutate(obs, d)
    obs["files"] = [{"name": n, "path": n, "sha256": C.sha256_file(d / n),
                     "bytes": (d / n).stat().st_size} for n in file_names]
    ok, why = A._v2_chain_complete(obs)
    obs["chain_complete"] = chain_override if chain_override is not None else ok
    obs["chain_status_reason"] = why
    (d / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    (d / "COMPLETE").write_text(json.dumps({
        "finalized_at": "2026-10-13 00:00:00", "schema": obs["schema"],
        "observation_sha256": C.sha256_file(d / "observation.json"),
        "git_commit": "a" * 40, "baseline_key": "e" * 32,
    }, ensure_ascii=False, indent=1) + "\n")
    return d


# ---------------------------------------------------------------- mutations
def m_r1(obs, d):
    obs["L3"] = {"status": "unsupported", "method": None,
                 "reason": "非 PRF 家族（addrpath）：Phase B 前无传播 tag"}
    obs["missing_levels"] = ["L3"]


def m_r2(obs, d):
    obs["L0"]["attempted"] = None      # funnel 行缺失的 abort 路径形态


def m_r3(obs, d):
    (d / "commit_trace.csv.gz").write_bytes(b"")   # 现场清空（记录态未变）


def m_r3_exc(obs, d):
    obs["L5"]["outcome"] = "Crash"
    obs["L5"]["classes"]["Crash"] = 1
    obs["L5"]["classes"]["SDC"] = 0
    obs["L2"]["status"] = "not_observed_before_crash"
    obs["L2"]["commit_diff"] = None
    obs["L2"]["note"] = ("空 trace（0 完整行）：abort 早于 ctrace 首个 "
                         "FLUSH_EVERY 刷盘点（W2.1 生产者批量 flush 契约）")
    obs["L2"]["fault"] = dict(obs["L2"]["fault"], rows=0, bytes=0,
                              error="empty file", readable=False)
    (d / "commit_trace.csv.gz").write_bytes(b"")


def m_r4(obs, d):
    # BUG-4 形态：记录态 fault probe rows==0 但 commit_diff 报真实
    # divergence（磁盘文件完好——隔离 R3，单证 R4）
    obs["L2"]["fault"] = dict(obs["L2"]["fault"], rows=0, bytes=0)
    obs["L2"]["commit_diff"]["total_divergence_points"] = 3


def m_r5a(obs, d):
    obs["L5"]["classes"]["Detected/Contained"] = 1
    obs["L5"]["classes"]["SDC"] = 0


def m_r5b(obs, d):
    obs["L4"]["detected"] = True


def m_r6c1(obs, d):
    obs["missing_levels"] = ["L4"]     # 存储值自认缺层却仍声称链完整


def m_r6c3(obs, d):
    obs["L3"]["method"] = "proxy"      # PRF fanout proxy 口径（v1 E2E 形态）


def m_r7(obs, d):
    obs["schema"] = A.SCHEMA_V1


def m_r8(obs, d):
    del obs["needs_backfill"]


def m_r9(obs, d):
    obs["L4"]["detector"] = "none_wired"


def main():
    tmp = Path(tempfile.mkdtemp(prefix="lsu_audit_v2_test_"))
    camp = tmp / "camp"
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    def has(rec, token):
        return any(token in x for x in rec["reasons"])

    # ---- 造 14 个样本（见模块 docstring 样本表）
    build_v2_sample(camp, 0)                                   # 合规 full
    build_v2_sample(camp, 1, inactive=True)                    # 合规 inactive
    build_v2_sample(camp, 2, mutate=m_r1)                      # R1
    build_v2_sample(camp, 3, mutate=m_r2, chain_override=True)  # R2
    build_v2_sample(camp, 4, mutate=m_r3)                      # R3
    build_v2_sample(camp, 5, mutate=m_r3_exc, outcome="Crash")  # R3 例外
    build_v2_sample(camp, 6, mutate=m_r4)                      # R4
    build_v2_sample(camp, 7, mutate=m_r5a)                     # R5a
    build_v2_sample(camp, 8, mutate=m_r5b)                     # R5b
    build_v2_sample(camp, 9, mutate=m_r6c1)                    # R6 条款1
    build_v2_sample(camp, 10, mutate=m_r6c3, chain_override=True)  # R6 条款3
    build_v2_sample(camp, 11, mutate=m_r7)                     # R7
    build_v2_sample(camp, 12, mutate=m_r8)                     # R8
    build_v2_sample(camp, 13, mutate=m_r9)                     # R9

    # ---- v2 默认模式逐样本断言
    res = A.audit_campaign_root(camp)
    check("v2_scan_returns", res is not None)
    records, residues, replay_dirs, summary = res
    recs = {r["sample"]: r for r in records}
    check("v2_all_samples_audited",
          len(records) == 14 and not residues and not replay_dirs,
          json.dumps(summary, ensure_ascii=False))

    # PASS 侧（双向证明的合规半边）：full 合规样本零规则 token 零 FAIL
    r0 = recs[f"{ITEM}_s0"]
    check("valid_full_v2_passes_no_rule_tokens",
          r0["audit"] == "PASS" and r0["reasons"] == []
          and not any(has(r0, t) for t in RULE_TOKENS)
          and r0["chain_complete"] is True and r0["missing_layers"] == [],
          json.dumps(r0, ensure_ascii=False))
    # PASS 侧：inactive 合规样本（activated=0 → R1 不触发；L4 无 detector
    # 键 → R9 不触发；L3.method=None 合法）
    r1 = recs[f"{ITEM}_s1"]
    check("valid_inactive_v2_passes",
          r1["audit"] == "PASS" and r1["reasons"] == []
          and r1["chain_complete"] is True,
          json.dumps(r1, ensure_ascii=False))

    # R1：activated>0 且 L3 unsupported/method=None → FAIL（且仅此规则）
    r2 = recs[f"{ITEM}_s2"]
    check("r1_fail_l3_unsupported",
          r2["audit"] == "FAIL" and has(r2, "L3_unsupported_for_activated_sample")
          and r2["chain_complete"] is False,
          json.dumps(r2["reasons"], ensure_ascii=False))
    check("r1_precise_single_reason",
          len(r2["reasons"]) == 1,
          json.dumps(r2["reasons"], ensure_ascii=False))

    # R2：L0.attempted=None → FAIL
    r3 = recs[f"{ITEM}_s3"]
    check("r2_fail_l0_funnel_incomplete",
          r3["audit"] == "FAIL" and has(r3, "L0_funnel_incomplete"),
          json.dumps(r3["reasons"], ensure_ascii=False))

    # R3：现场空文件（记录态 probe error 仍是 None）→ FAIL——审计器现场
    # 复核独立于生产者记录
    r4 = recs[f"{ITEM}_s4"]
    check("r3_fail_evidence_trace_unreadable_fresh_probe",
          r4["audit"] == "FAIL" and has(r4, "evidence_trace_unreadable")
          and any("empty file" in x for x in r4["reasons"]),
          json.dumps(r4["reasons"], ensure_ascii=False))

    # R3 例外（保留的 W2.1 契约）：not_observed_before_crash + 空 fault
    # trace → PASS + note（绝不 FAIL）
    r5 = recs[f"{ITEM}_s5"]
    check("r3_exception_not_observed_empty_trace_passes",
          r5["audit"] == "PASS"
          and not has(r5, "evidence_trace_unreadable")
          and any("L2_fault_empty_under_not_observed" in x for x in r5["notes"]),
          json.dumps(r5, ensure_ascii=False))

    # R4：记录态 rows==0 + diverged/points>0 → FAIL（BUG-4 主动拦截）
    r6 = recs[f"{ITEM}_s6"]
    check("r4_fail_empty_trace_fake_divergence",
          r6["audit"] == "FAIL" and has(r6, "empty_trace_fake_divergence"),
          json.dumps(r6["reasons"], ensure_ascii=False))

    # R5a：L5.classes D/C>0 且 detected_na → FAIL
    r7 = recs[f"{ITEM}_s7"]
    check("r5a_fail_detector_na_counted",
          r7["audit"] == "FAIL" and has(r7, "detector_na_counted_as_detected"),
          json.dumps(r7["reasons"], ensure_ascii=False))

    # R5b：L4.detected=True 且 detector=not_present → FAIL
    r8 = recs[f"{ITEM}_s8"]
    check("r5b_fail_detector_na_counted",
          r8["audit"] == "FAIL" and has(r8, "detector_na_counted_as_detected"),
          json.dumps(r8["reasons"], ensure_ascii=False))

    # R6 条款1：chain=True 且 missing_levels 非空 → FAIL（重算一致，单证）
    r9 = recs[f"{ITEM}_s9"]
    check("r6c1_fail_chain_complete_with_degraded_layer",
          r9["audit"] == "FAIL"
          and has(r9, "chain_complete_with_degraded_layer")
          and not any("chain_complete_recompute_mismatch" in x
                      for x in r9["reasons"]),
          json.dumps(r9["reasons"], ensure_ascii=False))

    # R6 条款3：chain=True 且 L3.method=proxy → FAIL（R1 与重算 mismatch
    # 必然共触发——proxy 本身就是 R1 拦截对象且存储值内部矛盾）
    r10 = recs[f"{ITEM}_s10"]
    check("r6c3_fail_chain_complete_with_degraded_layer",
          r10["audit"] == "FAIL"
          and has(r10, "chain_complete_with_degraded_layer")
          and has(r10, "L3_unsupported_for_activated_sample"),
          json.dumps(r10["reasons"], ensure_ascii=False))

    # R7：v1 schema → FAIL，reason 含中央要求的"纠偏前历史样本"措辞
    r11 = recs[f"{ITEM}_s11"]
    check("r7_fail_schema_version_pre_correction",
          r11["audit"] == "FAIL" and has(r11, "schema_version_pre_correction")
          and any("纠偏前历史样本" in x for x in r11["reasons"]),
          json.dumps(r11["reasons"], ensure_ascii=False))

    # R8：缺 needs_backfill → FAIL
    r12 = recs[f"{ITEM}_s12"]
    check("r8_fail_contract_v2_fields_missing",
          r12["audit"] == "FAIL" and has(r12, "contract_v2_fields_missing"),
          json.dumps(r12["reasons"], ensure_ascii=False))

    # R9：detector='none_wired' → FAIL
    r13 = recs[f"{ITEM}_s13"]
    check("r9_fail_l4_detector_v1_value",
          r13["audit"] == "FAIL"
          and has(r13, "L4_detector_v1_value_none_wired"),
          json.dumps(r13["reasons"], ensure_ascii=False))

    # v2 汇总：11 FAIL / 3 PASS（s0/s1/s5）。chain_complete_true=13（除 s2
    # 重算对齐为 False 外，违规样本存储值仍声称 True——chain=True 声称 +
    # 降级层正是 R6 的拦截对象；audit FAIL ≠ chain_complete False）
    check("v2_summary_counts",
          summary["audit_pass"] == 3 and summary["audit_fail"] == 11
          and summary["rules_version"] == "v2"
          and summary["chain_complete_true"] == 13
          and summary["chain_complete_false"] == 1,
          json.dumps(summary, ensure_ascii=False))

    # ---- v1 模式切换（同树 --rules v1）：v2 规则违规在 v1 下不可见
    res_v1 = A.audit_campaign_root(camp, rules_version=A.RULES_V1)
    recs_v1 = {r["sample"]: r for r in res_v1[0]}
    summary_v1 = res_v1[3]
    # s2（R1 违规样本）：v1 PASS / v2 FAIL —— "E2E 样本全
    # chain_complete=false 不得算数"的最小复现（v1 审计看不见 L3 降级）
    v1_s2, v2_s2 = recs_v1[f"{ITEM}_s2"], recs[f"{ITEM}_s2"]
    check("mode_switch_s2_v1_pass_v2_fail",
          v1_s2["audit"] == "PASS" and v2_s2["audit"] == "FAIL"
          and v1_s2["rules_version"] == "v1"
          and v2_s2["rules_version"] == "v2",
          f"v1={v1_s2['audit']} v2={v2_s2['audit']}")
    v1_s11 = recs_v1[f"{ITEM}_s11"]
    check("mode_switch_s11_schema_v1_invisible",
          v1_s11["audit"] == "PASS"
          and recs[f"{ITEM}_s11"]["audit"] == "FAIL",
          json.dumps(v1_s11, ensure_ascii=False))
    # v1 模式全表：仅 s4 FAIL（空 trace 不可读在 v1 检查 (v) 下也 FAIL）；
    # 其余 v2 规则违规样本在 v1 下全 PASS——历史审计的盲区即纠偏对象
    v1_fail_samples = sorted(r["sample"] for r in res_v1[0]
                             if r["audit"] == "FAIL")
    check("mode_switch_v1_only_s4_fails",
          v1_fail_samples == [f"{ITEM}_s4"]
          and summary_v1["audit_pass"] == 13 and summary_v1["audit_fail"] == 1
          and summary_v1["rules_version"] == "v1",
          f"{v1_fail_samples} {json.dumps(summary_v1, ensure_ascii=False)}")

    # ---- CLI 模式切换（--rules 透传 + 默认 v2 + rules_version 落盘）
    jv2, jv1 = tmp / "cli_v2.json", tmp / "cli_v1.json"
    rc_v2 = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--campaign-root", str(camp), "--json", str(jv2)],
        capture_output=True, text=True)
    rc_v1 = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--campaign-root", str(camp), "--rules", "v1", "--json", str(jv1)],
        capture_output=True, text=True)
    b2, b1 = json.loads(jv2.read_text()), json.loads(jv1.read_text())
    check("cli_default_is_v2_rc1",
          rc_v2.returncode == 1
          and b2["summary"]["rules_version"] == "v2"
          and b2["summary"]["audit_fail"] == 11,
          f"rc={rc_v2.returncode}")
    check("cli_rules_v1_rc1_fail1",
          rc_v1.returncode == 1
          and b1["summary"]["rules_version"] == "v1"
          and b1["summary"]["audit_fail"] == 1,
          f"rc={rc_v1.returncode}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
