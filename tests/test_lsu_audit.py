#!/usr/bin/env python3
"""test_lsu_audit.py — 独立审计器单测（OBS 计划 T6a，Subagent-C）。

合成 campaign 树（复用 test_lsu_obs_core.py 的 fixture 手法：ctrace=W2.1 契约 /
msnap=W2.4 契约 / 注入行=s319 实测格式 + finalize_sample 造真 COMPLETE 样本）覆盖：
  1  full 样本 PASS（chain_complete=False 因 L3 unsupported——非 PRF 家族诚实规则；
     missing_layers=["L3"]；audit 与 chain_complete 是两条独立判据）
  2  inactive 样本 PASS（chain_complete=True，L1-L4 全 N/A，missing_layers=[]）
  3  l0l5 样本 PASS（chain_complete=False，missing_layers 含 L1/L2——
     not_collected(l0l5_mode) 是诚实状态故 audit=PASS，但该层数据确实未采集）
  4  observation.json 损坏 → FAIL
  5  files sha 被篡改 → FAIL（全量复核，不是抽样）
  6  chain_complete 存储值与重算不符 → FAIL
  7  identity.seed 与 sample 号派生不符（sample-0 seed）→ FAIL（OBS-5a 报告的
     driver bug 的机器检测）
  8  残留列举（staging / 无 COMPLETE / .replay 证据目录单列）
  9  golden 审计（完好 PASS / 截断 FAIL / 期望 sha 不符 FAIL）
  10 模式 2 legacy 只读扫描（记录 + 绝不写旧目录：树快照逐字节不变 +
     --json 落旧目录内被拒绝）

用法：python3 tests/test_lsu_audit.py   （退出码 0=全 PASS）
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
WT = HERE.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_audit as A          # noqa: E402
import lsu_obs_core as C       # noqa: E402
import micro_diff              # noqa: E402
from lsu_seed import lsu_seed  # noqa: E402

RUNID = "A01-F0-W9"
PHASE = "screening"
ITEM = "ITEM-900"


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
    return ("Tick: 887040, Site: lsq_sendFragmentToTranslation, "
            "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
            "new_vaddr=0x87ffffefd00, faults_injected: 1 "
            "(NOTE: SE-inert — byte7 zero lands in SE 512MiB range)")


FUNNEL = ("CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
          "injected=1 activated=1")
FUNNEL_INACTIVE = "CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=0 injected=0"


def make_l5(outcome, activated=1, crash_kind=None, timed_out=False):
    return {"outcome": outcome, "activated": activated, "injected": activated,
            "crash_kind": crash_kind, "timed_out": timed_out,
            "detected_na": True, "checksum": "0123456789abcdef",
            "classes": {"Masked": 0, "Detected/Contained": 0, "SDC": 0,
                        "Crash": 0, "Timeout": 0},
            "conservation": "OK"}


def ref_traces(tmp):
    """共享 golden ref 轨迹（divergence-free 基线）。"""
    ref_lines = [ctr_line(i) for i in range(12)]
    ctr = tmp / "ref_commit_trace.csv.gz"
    msn = tmp / "ref_micro_snap.csv.gz"
    write_ctr(ctr, ref_lines)
    write_msnap(msn, [micro_diff._synth_row(i, (i + 1) * 1000, 1000 + i * 500)
                      for i in range(6)])
    return ctr, msn, ref_lines


def fault_traces(staging, ref_lines, rows_ref, diverge=True):
    ctr = staging / "commit_trace.csv.gz"
    msn = staging / "micro_snap.csv.gz"
    if diverge:
        lines = list(ref_lines)
        lines[5] = ctr_line(5, val="ffffffffffffffff")
        write_ctr(ctr, lines)
        rows = list(rows_ref)
        rows[2] = micro_diff._synth_row(2, 3000, 2000,
                                        int_tbl={0: 5, 1: 6, 2: 9, 3: 8})
        write_msnap(msn, rows)
    else:
        write_ctr(ctr, ref_lines)
        write_msnap(msn, rows_ref)
    return ctr, msn


def make_identity(s, seed=None, obs_mode="full"):
    return {
        "campaign": "audit_t", "item": ITEM, "runid": RUNID, "sample": f"s{s}",
        "seed": lsu_seed(RUNID, PHASE, s) if seed is None else seed,
        "phase": PHASE, "git_commit": "a" * 40,
        "gem5_opt_sha256": "b" * 64, "lsu_proxy_sha256": "c" * 64,
        "workload": "se:gap_bfs", "workload_sha256": "d" * 64,
        "config_family": "C4-LSU", "pythonhashseed": 0,
        "baseline_key": C.baseline_key({
            "gem5_opt_sha256": "b" * 64, "lsu_proxy_sha256": "c" * 64,
            "workload": "gap_bfs", "workload_sha256": "d" * 64,
            "cpu": "O3", "variant": "B0", "maxinsts": 0,
            "obs_flags": ["--chaos_ctrace", "--chaos_msnap"],
            "env": {"PYTHONHASHSEED": "0"}, "checkpoint": "none (SE)"}),
        "obs_mode": obs_mode,
        "coverage_scope": ("full_run" if obs_mode == "full"
                           else "none_full_run_forbidden_pending_phaseB"),
    }


def build_sample(camp, s, *, mode="full", inactive=False, seed=None,
                 l5=None, replay=None):
    """造一个真 COMPLETE 样本（staging → finalize），返回 final 目录。"""
    item_dir = camp / ITEM
    item_dir.mkdir(parents=True, exist_ok=True)
    staging = item_dir / f"{ITEM}_s{s}.staging"
    staging.mkdir(exist_ok=True)
    final = item_dir / f"{ITEM}_s{s}"

    inj_text = "" if inactive else real_inj_line() + "\n"
    (staging / "addrpath_injections.log").write_text(inj_text)
    (staging / "gem5.out").write_text(
        (FUNNEL_INACTIVE if inactive else FUNNEL) + "\n...sim_exit...\n")
    l5v = l5 or make_l5("SDC" if not inactive else "Masked",
                        activated=0 if inactive else 1)
    (staging / "l5_verdict.json").write_text(
        json.dumps(l5v, ensure_ascii=False, indent=1))

    # 轨迹与 L1/L2（golden ref 在 tmp 根共享；full 模式才产轨迹）
    tmp = camp.parent
    ctr_ref, msn_ref, ref_lines = ref_traces(tmp)
    rows_ref = [micro_diff._synth_row(i, (i + 1) * 1000, 1000 + i * 500)
                for i in range(6)]
    if mode == "full" and not inactive:
        ctr_f, msn_f = fault_traces(staging, ref_lines, rows_ref, diverge=True)
        l1 = C.build_l1(msn_ref, msn_f)
        l2 = C.build_l2(ctr_ref, ctr_f, l5=l5v)
    else:
        l1 = C.build_l1(msn_ref, msn_ref, inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)", "reason": "cli(l0l5)"}
        l2 = C.build_l2(ctr_ref, ctr_ref, l5=l5v, inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)", "reason": "cli(l0l5)"}
    l3 = C.build_l3("addrpath", l2, inactive=inactive)
    l0 = C.parse_l0((staging / "gem5.out").read_text(), inj_text)
    l4 = C.build_l4(l0, l1, l2, l5v,
                    fault_msnap_path=staging / "micro_snap.csv.gz",
                    inactive=inactive) if mode == "full" else \
        {"status": "not_collected(l0l5_mode)", "reason": "cli(l0l5)"}

    names = (["addrpath_injections.log", "commit_trace.csv.gz",
              "micro_snap.csv.gz", "gem5.out", "l5_verdict.json"]
             if (mode == "full" and not inactive)
             else ["addrpath_injections.log", "gem5.out", "l5_verdict.json"])
    files = [{"name": n, "path": n, "sha256": C.sha256_file(staging / n),
              "bytes": (staging / n).stat().st_size} for n in names]
    ident = make_identity(s, seed=seed, obs_mode=mode)
    replay_ev = replay or {"policy": "per_sample", "verified": True,
                           "evidence": {}}
    obs = C.build_observation(ident, l0, l1, l2, l3, l4, l5v, replay_ev, files)
    (staging / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    C.finalize_sample(staging, final)
    return final


def build_golden(tmp, name, truncate=False):
    gdir = tmp / "goldens" / name
    staging = Path(str(gdir) + ".staging")
    staging.mkdir(parents=True, exist_ok=True)
    ctr, msn, _ = ref_traces(tmp)
    shutil.copy(ctr, staging / "commit_trace.csv.gz")
    shutil.copy(msn, staging / "micro_snap.csv.gz")
    (staging / "gem5.out").write_text("no-fault golden\n")
    if truncate:  # 截断 golden = 不可用作比对基线
        blob = (staging / "commit_trace.csv.gz").read_bytes()
        (staging / "commit_trace.csv.gz").write_bytes(blob[:len(blob) // 2])
    files = [{"name": n, "path": n,
              "sha256": C.sha256_file(staging / n),
              "bytes": (staging / n).stat().st_size}
             for n in ("commit_trace.csv.gz", "micro_snap.csv.gz", "gem5.out")]
    obs = {"schema": C.SCHEMA,
           "identity": {"gem5_opt_sha256": "b" * 64, "baseline_key": "e" * 32,
                        "kind": "no_fault_golden", "campaign": "audit_t"},
           "files": files, "violations": [], "degradations": []}
    (staging / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    C.finalize_sample(staging, gdir)
    return gdir


def tree_state(root):
    """只读快照：全部文件的 (size, mtime_ns)——用于证明零写入。"""
    out = []
    for p in sorted(Path(root).rglob("*")):
        st = p.stat()
        out.append((str(p), st.st_size, st.st_mtime_ns))
    return out


def main():
    tmp = Path(tempfile.mkdtemp(prefix="lsu_audit_test_"))
    camp = tmp / "camp"
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ---- 造样本：s0 full / s1 inactive / s2 l0l5 / s3 损坏 / s4 sha 篡改 /
    #      s5 chain 篡改 / s6 seed 不符 + 残留 s7.staging / s8 无 COMPLETE
    d0 = build_sample(camp, 0, mode="full", l5=make_l5("SDC"))
    d1 = build_sample(camp, 1, mode="full", inactive=True,
                      l5=make_l5("Masked", activated=0))
    d2 = build_sample(camp, 2, mode="l0l5", l5=make_l5("Masked"))
    d3 = build_sample(camp, 3, mode="full", l5=make_l5("SDC"))
    (d3 / "observation.json").write_text('{"schema": "lsu-obs", "L0": {')
    d4 = build_sample(camp, 4, mode="full", l5=make_l5("SDC"))
    with open(d4 / "commit_trace.csv.gz", "ab") as f:
        f.write(b"\x00tamper")
    d5 = build_sample(camp, 5, mode="full", l5=make_l5("SDC"))
    obs5 = json.loads((d5 / "observation.json").read_text())
    obs5["chain_complete"] = True   # 存储值篡改为 True（重算仍 False）
    (d5 / "observation.json").write_text(
        json.dumps(obs5, ensure_ascii=False, indent=1))
    comp5 = json.loads((d5 / "COMPLETE").read_text())
    comp5["observation_sha256"] = C.sha256_file(d5 / "observation.json")
    (d5 / "COMPLETE").write_text(
        json.dumps(comp5, ensure_ascii=False, indent=1) + "\n")
    build_sample(camp, 6, mode="full", l5=make_l5("SDC"),
                 seed=lsu_seed(RUNID, PHASE, 0))  # sample-0 seed（driver bug 形态）
    (camp / ITEM / f"{ITEM}_s7.staging").mkdir(parents=True, exist_ok=True)
    (camp / ITEM / f"{ITEM}_s7.staging" / "junk").write_text("x")
    (camp / ITEM / f"{ITEM}_s8").mkdir(parents=True, exist_ok=True)
    (camp / ITEM / f"{ITEM}_s8" / "junk").write_text("x")
    (camp / ITEM / f"{ITEM}_s0.replay").mkdir(parents=True, exist_ok=True)
    (camp / ITEM / f"{ITEM}_s0.replay" / "replay_verdict.json").write_text("{}")

    res = A.audit_campaign_root(camp)
    check("campaign_scan_returns", res is not None)
    records, residues, replay_dirs, summary = res
    recs = {r["sample"]: r for r in records}

    # 1) full 样本：PASS / chain False（L3 unsupported）/ missing=[L3]
    r0 = recs[f"{ITEM}_s0"]
    check("full_sample_pass", r0["audit"] == "PASS",
          json.dumps(r0["reasons"], ensure_ascii=False))
    check("full_chain_false_l3",
          r0["chain_complete"] is False and r0["missing_layers"] == ["L3"],
          str(r0))
    # audit PASS 与 chain_complete 分离（两条独立判据，绝不混同）
    check("audit_neq_chain", r0["audit"] == "PASS"
          and r0["chain_complete"] is False)

    # 2) inactive：PASS / chain True / L1-L4 N/A / missing=[]
    r1 = recs[f"{ITEM}_s1"]
    check("inactive_pass_chain_true",
          r1["audit"] == "PASS" and r1["chain_complete"] is True
          and r1["missing_layers"] == [],
          json.dumps(r1, ensure_ascii=False))

    # 3) l0l5：PASS（not_collected 诚实）但 missing 含 L1/L2、chain False
    r2 = recs[f"{ITEM}_s2"]
    check("l0l5_pass_but_missing_l1l2",
          r2["audit"] == "PASS" and r2["chain_complete"] is False
          and "L1" in r2["missing_layers"] and "L2" in r2["missing_layers"],
          json.dumps(r2, ensure_ascii=False))

    # 4) observation.json 损坏 → FAIL
    r3 = recs[f"{ITEM}_s3"]
    check("corrupt_obs_fail",
          r3["audit"] == "FAIL"
          and any("observation_unparseable" in x for x in r3["reasons"]),
          json.dumps(r3, ensure_ascii=False))

    # 5) files sha 篡改 → FAIL（全量复核抓到）
    r4 = recs[f"{ITEM}_s4"]
    check("sha_tamper_fail",
          r4["audit"] == "FAIL"
          and any("sha_mismatch" in x for x in r4["reasons"]),
          json.dumps(r4, ensure_ascii=False))

    # 6) chain_complete 存储值与重算不符 → FAIL
    r5 = recs[f"{ITEM}_s5"]
    check("chain_mismatch_fail",
          r5["audit"] == "FAIL" and any(
              "chain_complete_recompute_mismatch" in x
              for x in r5["reasons"]),
          json.dumps(r5, ensure_ascii=False))

    # 7) sample-0 seed（driver bug 形态）→ FAIL
    r6 = recs[f"{ITEM}_s6"]
    check("seed_mismatch_fail",
          r6["audit"] == "FAIL"
          and any("identity_seed_mismatch" in x for x in r6["reasons"]),
          json.dumps(r6, ensure_ascii=False))

    # 8) 残留与 replay 证据目录
    res_kinds = {r["sample"]: r["kind"] for r in residues}
    check("residue_staging_listed",
          res_kinds.get(f"{ITEM}_s7.staging") == "staging", str(res_kinds))
    check("residue_incomplete_listed",
          res_kinds.get(f"{ITEM}_s8") == "incomplete_no_COMPLETE",
          str(res_kinds))
    check("replay_dir_separate_from_residue",
          replay_dirs == [f"{ITEM}_s0.replay"]
          and f"{ITEM}_s0.replay" not in res_kinds,
          f"{replay_dirs} {res_kinds}")
    check("summary_counts",
          summary["samples_audited"] == 7 and summary["audit_pass"] == 3
          and summary["audit_fail"] == 4
          and summary["chain_complete_true"] == 2   # s1 + s5(篡改存储值)
          and summary["chain_complete_false"] == 4  # s0/s2/s4/s6
          and summary["missing_layers_histogram"]
          == {"L0,L1,L2,L3,L4,L5": 1,   # s3 损坏 → 全层级未知
              "L1,L2,L3,L4": 1,         # s2 l0l5
              "L3": 4,                  # s0/s4/s5/s6 full（L3 unsupported）
              "none": 1},               # s1 inactive
          json.dumps(summary, ensure_ascii=False))

    # 9) golden 审计
    g_ok = build_golden(tmp, "g_ok")
    g_tr = build_golden(tmp, "g_tr", truncate=True)
    check("golden_pass", A.audit_golden_dir(g_ok)["audit"] == "PASS")
    rg = A.audit_golden_dir(g_tr)
    check("golden_truncated_fail",
          rg["audit"] == "FAIL"
          and any("golden_trace_not_readable" in x for x in rg["reasons"]),
          json.dumps(rg, ensure_ascii=False))
    rg2 = A.audit_golden_dir(g_ok, expect_gem5_sha="f" * 64)
    check("golden_sha_expect_fail", rg2["audit"] == "FAIL"
          and any("gem5_opt_sha256" in x for x in rg2["reasons"]),
          json.dumps(rg2, ensure_ascii=False))

    # 10) 模式 2 legacy 只读扫描 + CLI
    leg = tmp / "legacy"
    (leg / f"{ITEM}_s0").mkdir(parents=True)
    (leg / f"{ITEM}_s1").mkdir(parents=True)
    (leg / f"{ITEM}_s10").mkdir(parents=True)
    (leg / "ITEM-999_s0").mkdir(parents=True)  # 其他 item（不得混入）
    for s, v in ((0, make_l5("Masked")), (1, make_l5("Crash",
                                                     crash_kind="simulator_assert")),
                 (10, make_l5("SDC"))):
        (leg / f"{ITEM}_s{s}" / "l5_verdict.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=1))
    before = tree_state(leg)
    out_json = tmp / "legacy_summary.json"
    r = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--legacy-root", str(leg), "--item", ITEM, "--json", str(out_json)],
        capture_output=True, text=True)
    check("legacy_cli_rc0", r.returncode == 0, r.stderr[-300:])
    lines = [json.loads(l) for l in r.stdout.splitlines()
             if l.startswith("{") and '"sample"' in l]
    check("legacy_records_shape",
          len(lines) == 3
          and all(x["chain"] == "outcome_complete_chain_pending"
                  and x["missing_levels"] == ["L1", "L2", "L3", "L4"]
                  and x["evidence"] and x["evidence"].endswith(
                      "l5_verdict.json") for x in lines),
          r.stdout[-500:])
    check("legacy_numeric_order",
          [x["sample"] for x in lines]
          == [f"{ITEM}_s0", f"{ITEM}_s1", f"{ITEM}_s10"],
          str([x["sample"] for x in lines]))
    check("legacy_outcomes",
          {x["sample"]: x["outcome"] for x in lines}
          == {f"{ITEM}_s0": "Masked", f"{ITEM}_s1": "Crash",
              f"{ITEM}_s10": "SDC"}, r.stdout[-500:])
    check("legacy_readonly_no_writes", tree_state(leg) == before,
          "legacy 树被写入！")
    check("legacy_json_written", out_json.exists()
          and json.loads(out_json.read_text())["summary"]["samples"] == 3)
    # --json 落在旧目录内 → 拒绝
    r_bad = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--legacy-root", str(leg), "--item", ITEM,
         "--json", str(leg / "summary.json")],
        capture_output=True, text=True)
    check("legacy_json_inside_refused",
          r_bad.returncode == 2 and "绝不写" in (r_bad.stderr + r_bad.stdout),
          f"rc={r_bad.returncode} {r_bad.stderr[-200:]}")
    check("legacy_tree_still_untouched", tree_state(leg) == before)

    # CLI 模式 1（campaign 有 FAIL → 退出码 1；--json 落盘一致）
    camp_json = tmp / "camp_summary.json"
    r1c = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--campaign-root", str(camp), "--json", str(camp_json)],
        capture_output=True, text=True)
    check("campaign_cli_rc1_on_fail", r1c.returncode == 1,
          f"rc={r1c.returncode}")
    bundle = json.loads(camp_json.read_text())
    check("campaign_json_bundle_consistent",
          bundle["summary"]["audit_fail"] == 4
          and len(bundle["records"]) == 7 and len(bundle["residues"]) == 2
          and bundle["replay_evidence_dirs"] == [f"{ITEM}_s0.replay"],
          json.dumps(bundle["summary"], ensure_ascii=False))

    # 干净 campaign（全部 PASS）→ CLI 退出码 0
    camp2 = tmp / "camp_clean"
    build_sample(camp2, 0, mode="full", l5=make_l5("SDC"))
    build_sample(camp2, 1, mode="full", inactive=True,
                 l5=make_l5("Masked", activated=0))
    r2c = subprocess.run(
        [sys.executable, str(WT / "tools" / "lsu_audit.py"),
         "--campaign-root", str(camp2)],
        capture_output=True, text=True)
    check("clean_campaign_cli_rc0", r2c.returncode == 0,
          f"rc={r2c.returncode} {r2c.stdout[-400:]}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
