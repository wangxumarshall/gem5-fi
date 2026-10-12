#!/usr/bin/env python3
"""test_lsu_obs_core.py — 观测核心单测（OBS 计划 T2）。

合成 fixture（ctrace=W2.1 契约 / msnap=W2.4 契约 / 注入行=s319 实测格式），
覆盖：baseline_key 漂移、gz 探针截断、L0 解析与 abort 回退、L1/L2 比对、
L3 unsupported 诚实规则、L4 延迟、九分类映射、chain_complete 判定、
staging→COMPLETE 协议（含 fatal 拒绝、identity 漂移拒绝、quarantine）。

用法：python3 tests/test_lsu_obs_core.py   （退出码 0=全 PASS）
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import lsu_obs_core as C   # noqa: E402
import micro_diff          # noqa: E402  （复用其合成行生成器，契约同源）


# ---------------------------------------------------------------- fixtures
def ctr_line(seq, tick=None, pc="400080", op="add", val="0000000000000001"):
    tick = 100 + seq if tick is None else tick
    return f"{seq},0,{tick},{pc},{op},1,1,5,66,{val}"


def write_ctr(path, lines):
    with gzip.open(path, "wt") as f:
        for l in lines:
            f.write(l + "\n")


def write_msnap(path, rows):
    micro_diff._write_snap(str(path), rows)


def real_inj_line():
    # s319 实测行（addrpath_injections.log 真实格式，含 NOTE 尾注）
    return ("Tick: 887040, Site: lsq_sendFragmentToTranslation, "
            "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
            "new_vaddr=0x87ffffefd00, faults_injected: 1 "
            "(NOTE: SE-inert — byte7 zero lands in SE 512MiB range)")


FUNNEL = ("CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
          "injected=1 activated=1")


def base_ident(**over):
    ident = {
        "gem5_opt_sha256": "a" * 64, "lsu_proxy_sha256": "b" * 64,
        "workload": "gap_bfs", "workload_sha256": "c" * 64,
        "cpu": "O3", "variant": "B0", "maxinsts": 0,
        "obs_flags": ["--chaos_ctrace", "--chaos_msnap"],
        "env": {"PYTHONHASHSEED": "0"}, "checkpoint": "none (SE)",
    }
    ident.update(over)
    return ident


def make_l5(outcome, activated=1, crash_kind=None, timed_out=False):
    return {"outcome": outcome, "activated": activated, "injected": activated,
            "crash_kind": crash_kind, "timed_out": timed_out,
            "detected_na": True, "checksum": "0123456789abcdef",
            "classes": {"Masked": 0, "Detected/Contained": 0, "SDC": 0,
                        "Crash": 0, "Timeout": 0},
            "conservation": "OK"}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="obs_core_test_"))
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ---- 1) baseline_key：任一 hash 变化 → 不同键 ----
    k1, k2 = C.baseline_key(base_ident()), C.baseline_key(base_ident())
    k3 = C.baseline_key(base_ident(gem5_opt_sha256="d" * 64))
    k4 = C.baseline_key(base_ident(workload="agu_addrmodes"))
    check("baseline_key_stable", k1 == k2 and len(k1) == 32)
    check("baseline_key_binary_drift", k1 != k3)
    check("baseline_key_workload_drift", k1 != k4)

    # ---- 2) gz_probe：完整/截断 ----
    ref_lines = [ctr_line(i) for i in range(10)]
    write_ctr(tmp / "ctr_ref.csv.gz", ref_lines)
    write_ctr(tmp / "ctr_div.csv.gz",
              ref_lines[:5] + [ctr_line(5, val="ffffffffffffffff")]
              + ref_lines[6:])
    write_ctr(tmp / "ctr_same.csv.gz", ref_lines)
    blob = (tmp / "ctr_ref.csv.gz").read_bytes()
    (tmp / "ctr_trunc.csv.gz").write_bytes(blob[:len(blob) // 2])
    # 大文件截断（300 行切 60%）——保证前缀有可数完整行（真实 abort 形态）
    big_lines = [ctr_line(i) for i in range(300)]
    write_ctr(tmp / "ctr_big.csv.gz", big_lines)
    big_blob = (tmp / "ctr_big.csv.gz").read_bytes()
    (tmp / "ctr_bigtrunc.csv.gz").write_bytes(big_blob[:int(len(big_blob) * 0.6)])
    p_ok = C.gz_probe(tmp / "ctr_ref.csv.gz")
    p_tr = C.gz_probe(tmp / "ctr_bigtrunc.csv.gz")
    p_ms = C.gz_probe(tmp / "nonexistent.csv.gz")
    check("gz_probe_complete", p_ok["readable"] and not p_ok["truncated"]
          and p_ok["rows"] == 10, str(p_ok))
    check("gz_probe_truncated_flagged",
          p_tr["truncated"] and p_tr["rows"] > 0, str(p_tr))
    check("gz_probe_missing", not p_ms["readable"] and p_ms["error"])

    # ---- 3) parse_l0：funnel+日志 / abort 回退 / 双缺失 ----
    l0 = C.parse_l0(FUNNEL + "\n030921682b3731f2\n", real_inj_line() + "\n")
    check("l0_funnel", l0["attempted"] == 1 and l0["eligible"] == 265143
          and l0["injected"] == 1 and l0["funnel_source"] == "stdout", str(l0))
    check("l0_injection_fields",
          l0["injections"][0]["tick"] == 887040
          and l0["injections"][0]["site"] == "lsq_sendFragmentToTranslation"
          and l0["injections"][0]["mode"] == "low_bit_flip"
          and l0["injections"][0]["old"] == "0x7ffffefd00"
          and l0["injections"][0]["new"] == "0x87ffffefd00"
          and l0["injections"][0]["dynamic_target"] == "vaddr", str(l0))
    l0_abort = C.parse_l0("... panic ...\n", real_inj_line() + "\n")
    check("l0_abort_fallback",
          l0_abort["injected"] == 1 and l0_abort["attempted"] is None
          and "fallback" in l0_abort["funnel_source"], str(l0_abort))
    l0_none = C.parse_l0("nothing here\n", "")
    check("l0_both_missing_violation",
          any(v.startswith("funnel_missing") for v in l0_none["violations"]),
          str(l0_none))

    # ---- 4) L2 比对：无分歧 / 分歧 / 截断+Crash ----
    l2_same = C.build_l2(tmp / "ctr_ref.csv.gz", tmp / "ctr_same.csv.gz",
                         l5=make_l5("Masked"))
    check("l2_no_divergence_complete",
          l2_same["status"] == "complete"
          and l2_same["commit_diff"]["verdict"] == "no_divergence"
          and l2_same["commit_diff"]["first_errant_commit"] is None,
          str(l2_same.get("commit_diff")))
    l2_div = C.build_l2(tmp / "ctr_ref.csv.gz", tmp / "ctr_div.csv.gz",
                        l5=make_l5("SDC"))
    fe = l2_div["commit_diff"]["first_errant_commit"]
    check("l2_first_errant",
          l2_div["status"] == "complete"
          and l2_div["commit_diff"]["verdict"] == "diverged"
          and fe["seq"] == 5 and fe["tick"] == 105 and fe["pc"] == "400080"
          and fe["class"] == "data_corruption", str(fe))
    l2_crash = C.build_l2(tmp / "ctr_big.csv.gz", tmp / "ctr_bigtrunc.csv.gz",
                          l5=make_l5("Crash", crash_kind="simulator_assert"))
    check("l2_crash_before_divergence",
          l2_crash["status"] == "not_observed_before_crash"
          and l2_crash["fault"]["truncated"] is True
          and l2_crash["commit_diff"]["verdict"]
          == "truncated_no_divergence_in_prefix", str(l2_crash["commit_diff"]))
    l2_to = C.build_l2(tmp / "ctr_big.csv.gz", tmp / "ctr_bigtrunc.csv.gz",
                       l5=make_l5("Timeout", timed_out=True))
    check("l2_timeout_before_divergence",
          l2_to["status"] == "not_observed_before_timeout", l2_to["status"])
    # 边界：超早期 abort（0 完整行前缀）→ 诚实 not_observed（非 error）
    l2_early = C.build_l2(tmp / "ctr_big.csv.gz", tmp / "ctr_trunc.csv.gz",
                          l5=make_l5("Crash", crash_kind="simulator_assert"))
    check("l2_early_abort_zero_prefix",
          l2_early["status"] == "not_observed_before_crash"
          and l2_early["commit_diff"] is None
          and "空前缀" in l2_early.get("note", ""), str(l2_early))

    # ---- 5) L1 比对：无分歧 / RAT 分歧 ----
    rows_ref = [micro_diff._synth_row(i, (i + 1) * 1000, 1000 + i * 500)
                for i in range(5)]
    write_msnap(tmp / "ms_ref.csv.gz", rows_ref)
    write_msnap(tmp / "ms_same.csv.gz", rows_ref)
    rows_div = list(rows_ref)
    rows_div[2] = micro_diff._synth_row(2, 3000, 2000,
                                        int_tbl={0: 5, 1: 6, 2: 9, 3: 8})
    write_msnap(tmp / "ms_div.csv.gz", rows_div)
    l1_same = C.build_l1(tmp / "ms_ref.csv.gz", tmp / "ms_same.csv.gz")
    l1_div = C.build_l1(tmp / "ms_ref.csv.gz", tmp / "ms_div.csv.gz")
    check("l1_no_divergence",
          l1_same["status"] == "complete"
          and l1_same["micro_diff"]["no_divergence"] is True)
    check("l1_rat_div_first_snap",
          l1_div["status"] == "complete"
          and l1_div["micro_diff"]["first_divergence_snap_seq"] == 2
          and l1_div["micro_diff"]["rat_div_max_by_class"]["int"] == 1,
          str(l1_div.get("micro_diff")))

    # ---- 6) L3 unsupported 诚实规则 ----
    l3 = C.build_l3("addrpath", l2_div)
    check("l3_unsupported_non_prf",
          l3["status"] == "unsupported" and l3["method"] is None
          and "Phase B" in l3["reason"]
          and l3["auxiliary_commit_footprint"]["n_divergence_points"] == 1,
          str(l3))
    l3_prf = C.build_l3("physreg", l2_div, method="fanout_proxy")
    check("l3_prf_proxy_caveat",
          l3_prf["status"] == "complete" and l3_prf["method"] == "proxy"
          and "upper-bound" in l3_prf["caveat"], str(l3_prf))

    # ---- 7) L4：首异常（L2 优先）与延迟 ----
    # 注入 tick=50 < 首错误提交 tick=105（连贯 fixture；延迟=55 ticks）
    inj_early = ("Tick: 50, Site: lsq_sendFragmentToTranslation, "
                 "mode=low_bit_flip, old_vaddr=0x1000, new_vaddr=0x2000, "
                 "faults_injected: 1")
    l0v = C.parse_l0(FUNNEL + "\nx\n", inj_early + "\n")
    l4 = C.build_l4(l0v, l1_div, l2_div, make_l5("SDC"),
                    fault_msnap_path=tmp / "ms_div.csv.gz")
    fa = l4["first_anomaly"]
    check("l4_first_anomaly_l2",
          fa["source"] == "L2" and fa["tick"] == 105
          and fa["latency_ticks_from_first_injection"] == 55, str(fa))
    check("l4_detected_na_never_detected",
          l4["detected_na"] is True and l4["detected"] is False
          and l4["detector"] == "none_wired")

    # ---- 8) 九分类映射 ----
    check("fds_masked_none",
          C.first_detection_source(make_l5("Masked"))[0] == "None")
    check("fds_sdc_none", C.first_detection_source(make_l5("SDC"))[0] == "None")
    check("fds_guest_crash_os",
          C.first_detection_source(make_l5("Crash",
                                           crash_kind="guest_or_unknown"))[0]
          == "OS")
    check("fds_simassert_none",
          C.first_detection_source(make_l5("Crash",
                                           crash_kind="simulator_assert"))[0]
          == "None")

    # ---- 9) build_observation + chain_complete ----
    ident = {"campaign": "t", "runid": "A01-F0-W9", "sample": "s0",
             "seed": 1, "git_commit": "x" * 40, "gem5_opt_sha256": "a" * 64,
             "workload": "gap_bfs", "workload_sha256": "c" * 64,
             "baseline_key": k1, "pythonhashseed": 0}
    files = [{"name": "commit_trace.csv.gz", "path": "commit_trace.csv.gz",
              "sha256": C.sha256_file(tmp / "ctr_ref.csv.gz"),
              "bytes": (tmp / "ctr_ref.csv.gz").stat().st_size}]
    replay_ok = {"policy": "per_sample", "verified": True, "evidence": {}}
    obs_act = C.build_observation(
        ident, l0v, l1_div, l2_div, l3,
        C.build_l4(l0v, l1_div, l2_div, make_l5("SDC")),
        make_l5("SDC"), replay_ok, files)
    check("obs_activated_chain_false_l3",
          obs_act["chain_complete"] is False
          and "L3" in obs_act["chain_status_reason"],
          obs_act["chain_status_reason"])
    check("obs_nine_class_fields",
          obs_act["L5"]["first_detection_source"] == "None"
          and obs_act["L5"]["outcome"] == "SDC")
    # inactive：activated=0 → L1-L4 全 N/A + chain_complete True
    l5_inact = make_l5("Masked", activated=0)
    l0_inact = C.parse_l0(
        "CHAOS_LSU_TRIGGER: attempted=1 eligible=0 injected=0\n", "")
    obs_inact = C.build_observation(
        ident, l0_inact,
        C.build_l1(tmp / "ms_ref.csv.gz", tmp / "ms_same.csv.gz",
                   inactive=True),
        C.build_l2(tmp / "ctr_ref.csv.gz", tmp / "ctr_same.csv.gz",
                   l5=l5_inact, inactive=True),
        C.build_l3("addrpath", None, inactive=True),
        C.build_l4(l0_inact, None, None, l5_inact, inactive=True),
        l5_inact, replay_ok, files)
    check("obs_inactive_chain_true",
          obs_inact["chain_complete"] is True
          and all(obs_inact[lv]["status"] == "N/A(inactive_no_activation)"
                  for lv in ("L1", "L2", "L3", "L4")),
          obs_inact["chain_status_reason"])
    # replay 未验证 → False
    obs_norep = C.build_observation(
        ident, l0v, l1_div, l2_div, l3, C.build_l4(l0v, l1_div, l2_div,
                                                   make_l5("SDC")),
        make_l5("SDC"), {"policy": "per_sample", "verified": False}, files)
    check("obs_replay_unverified_false", obs_norep["chain_complete"] is False)

    # ---- 10) staging → COMPLETE 协议 ----
    def stage(name, obs):
        st = tmp / (name + ".staging")
        st.mkdir(parents=True, exist_ok=True)
        (st / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        shutil.copy(tmp / "ctr_ref.csv.gz", st / "commit_trace.csv.gz")
        return st

    st1 = stage("good", dict(obs_act,
                             violations=[],
                             files=[{"name": "commit_trace.csv.gz",
                                     "path": "commit_trace.csv.gz",
                                     "sha256": C.sha256_file(
                                         tmp / "ctr_ref.csv.gz"),
                                     "bytes": 1}]))
    fin = C.finalize_sample(st1, tmp / "good")
    check("finalize_ok_complete_marker",
          fin == tmp / "good" and (tmp / "good" / "COMPLETE").exists())
    ok, reason = C.verify_complete(tmp / "good",
                                   {"git_commit": ident["git_commit"],
                                    "baseline_key": k1})
    check("verify_complete_ok", ok, reason)
    ok2, reason2 = C.verify_complete(tmp / "good",
                                     {"baseline_key": "f" * 32})
    check("verify_complete_identity_drift", not ok2
          and "identity drift" in reason2, reason2)
    # violations 非空 → 拒绝 finalize，staging 保留
    st2 = stage("bad", dict(obs_act, violations=["file_missing: x"]))
    try:
        C.finalize_sample(st2, tmp / "bad")
        check("finalize_violation_refused", False, "no exception")
    except RuntimeError as e:
        check("finalize_violation_refused", "violations" in str(e)
              and st2.exists(), str(e))
    # sha 不符 → 拒绝
    st3 = stage("badsha", dict(obs_act, violations=[],
                               files=[{"name": "x", "path": "commit_trace.csv.gz",
                                       "sha256": "0" * 64, "bytes": 1}]))
    try:
        C.finalize_sample(st3, tmp / "badsha")
        check("finalize_sha_refused", False, "no exception")
    except RuntimeError as e:
        check("finalize_sha_refused", "sha" in str(e), str(e))
    # final 已有 COMPLETE → finalize 返回 None（绝不覆盖）
    check("finalize_existing_complete_noop",
          C.finalize_sample(stage("good2", dict(obs_act, violations=[])),
                            tmp / "good") is None)
    # 残留无 COMPLETE 目录 → quarantine 保留
    (tmp / "residue").mkdir(exist_ok=True)
    (tmp / "residue" / "junk").write_text("x")
    q = C.quarantine(tmp / "residue")
    check("quarantine_preserves", q is not None and q.exists()
          and (q / "junk").exists() and not (tmp / "residue").exists(), str(q))

    # ---- 11) file_lock 跨进程互斥（golden 跨进程防护的核心） ----
    lock_path = tmp / "golden_x.golden.lock"
    child_code = (
        "import sys, time; sys.path.insert(0, %r); import lsu_obs_core as C\n"
        "try:\n"
        "    with C.file_lock(%r, timeout_s=0.5, poll_s=0.1):\n"
        "        pass\n"
        "except TimeoutError:\n"
        "    sys.exit(42)\n"
        "sys.exit(0)" % (str(HERE.parent / "tools"), str(lock_path)))
    with C.file_lock(lock_path, timeout_s=5, poll_s=0.1):
        r = subprocess.run([sys.executable, "-c", child_code],
                           capture_output=True)
        check("file_lock_blocks_other_process", r.returncode == 42,
              f"rc={r.returncode}")
    r2 = subprocess.run([sys.executable, "-c", child_code], capture_output=True)
    check("file_lock_released_after_scope", r2.returncode == 0,
          f"rc={r2.returncode}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
