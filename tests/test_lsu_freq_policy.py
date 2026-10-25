#!/usr/bin/env python3
"""Frequency-policy overlay contract test."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_freq_policy as P

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond: fails.append(name)

def test_policy_covers_all_runids():
    pol = P.load_policy()
    ids = {e["run_id"] for e in pol["entries"]}
    rm = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/runid_map.json").read_text("utf-8"))
    check("policy_covers_325", len(rm["entries"]) == 325 and all(e["run_id"] in ids for e in rm["entries"]))
    check("f6_is_64", sum(1 for e in pol["entries"] if e["frequency"]=="F6" and not e.get("legacy")) == 64)

def test_entries_exactly_325_authoritative():
    """[A4 2026-10-25b] entries == EXACTLY the 325 authoritative runid_map RunIDs:
    no duplicates, no hidden aliases, no legacy rows. The 4 CSV-only V2.0-deleted
    F6 rows (T09-F6-W4, S12-F6-W5, C13-F6-W6, O08-F6-W7) live in a separate
    explicit legacy_f6_non_authoritative section that query() still refuses."""
    pol = P.load_policy()
    ent = pol["entries"]
    check("entries_len_325", len(ent) == 325, str(len(ent)))
    check("entries_unique_325", len({e["run_id"] for e in ent}) == 325,
          str(len({e["run_id"] for e in ent})))
    check("counts_authoritative_only",
          pol["counts"] == {"total": 325, "normal": 261, "stress_only": 39,
                            "stress_redundant": 25, "legacy_non_authoritative": 4},
          str(pol["counts"]))
    leg = pol.get("legacy_f6_non_authoritative", [])
    check("legacy_section_len_4", len(leg) == 4, str(len(leg)))
    check("legacy_runids_expected",
          {e["run_id"] for e in leg} == {"T09-F6-W4", "S12-F6-W5", "C13-F6-W6", "O08-F6-W7"},
          str(sorted(e["run_id"] for e in leg)))
    check("legacy_flags_explicit",
          all(e.get("legacy") is True and e.get("authoritative") is False for e in leg),
          str([(e["run_id"], e.get("legacy"), e.get("authoritative")) for e in leg]))
    ids, lids = {e["run_id"] for e in ent}, {e["run_id"] for e in leg}
    check("legacy_disjoint_from_entries", not (ids & lids), str(sorted(ids & lids)))
    # query() must still find & refuse every legacy row (campaign gate depends on it)
    bad = [r for r in sorted(lids)
           if P.query(pol, r, 1)["decision"] != "REFUSE_STRESS_REDUNDANT"]
    check("legacy_query_refuses", not bad, str(bad))
    # a runid that is neither authoritative nor legacy stays UNKNOWN_RUNID
    check("unknown_still_unknown",
          P.query(pol, "X09-F6-W1", 1)["decision"] == "UNKNOWN_RUNID")

def test_campaign_refuses_redundant_and_seed2():
    import lsu_campaign as LC
    pol = P.load_policy()
    # every redundant F6 refuses
    red = [e["run_id"] for e in pol["entries"] if e["run_policy"] == "STRESS_REDUNDANT" and not e["legacy"]]
    check("redundant_exist", len(red) == 25)
    import lsu_freq_policy as FP
    bad = [r for r in red if FP.query(pol, r, 1)["decision"] != "REFUSE_STRESS_REDUNDANT"]
    check("all_redundant_refused", not bad, str(bad[:5]))
    # representative seed2 is not-required, seed1 allowed
    check("rep_seed1_allow", FP.query(pol, "T04-F6-W4", 1)["decision"] == "ALLOW_STRESS_ONLY")
    check("rep_seed2_not_required", FP.query(pol, "T04-F6-W4", 2)["decision"] == "POLICY_NOT_REQUIRED")
    # the campaign must expose the gate
    check("campaign_has_gate", hasattr(LC, "policy_decision"))

def test_policy_decision_gate_semantics():
    """[R6-FREQPOLICY] the ruled gate semantics through the campaign's own
    policy_decision (not just the raw query): the loud opt-in, the
    never-permits, and the optional-overlay degradation."""
    import lsu_campaign as LC
    if not hasattr(LC, "policy_decision"):
        check("gate_present", False, "lsu_campaign.policy_decision 缺失")
        return
    check("gate_present", True)
    pol = P.load_policy()
    red = next(e["run_id"] for e in pol["entries"]
               if e["run_policy"] == "STRESS_REDUNDANT" and not e["legacy"])
    norm = next(e["run_id"] for e in pol["entries"] if e["run_policy"] == "NORMAL")

    def refused(fn):
        try:
            fn()
            return False
        except SystemExit as e:
            return str(e).startswith("[R6-FREQPOLICY]")

    check("normal_seed1_allow", LC.policy_decision(norm, 1) == "ALLOW")
    check("normal_seed4_refused", refused(lambda: LC.policy_decision(norm, 4)))
    # representative F6 seed1 needs the loud opt-in
    check("rep_seed1_refused_without_flag",
          refused(lambda: LC.policy_decision("T04-F6-W4", 1)))
    check("rep_seed1_allowed_with_flag",
          LC.policy_decision("T04-F6-W4", 1, allow_stress_only=True) == "ALLOW_STRESS_ONLY")
    # --allow-stress-only never permits seed>1, never unblocks STRESS_REDUNDANT
    check("rep_seed2_refused_even_with_flag",
          refused(lambda: LC.policy_decision("T04-F6-W4", 2, allow_stress_only=True)))
    check("redundant_refused_even_with_flag",
          refused(lambda: LC.policy_decision(red, 1, allow_stress_only=True)))
    # [A4] a legacy CSV-only F6 row (legacy_f6_non_authoritative section, not in
    # entries) still refuses through the campaign gate — never UNKNOWN, never run
    check("legacy_refused_even_with_flag",
          refused(lambda: LC.policy_decision("C13-F6-W6", 1, allow_stress_only=True)))
    # overlay optional: missing module / missing JSON never block a NORMAL run
    _orig = LC._FP
    try:
        LC._FP = None
        check("module_missing_allow", LC.policy_decision(norm, 1) == "ALLOW")
        class _NoJSON:
            @staticmethod
            def load_policy():
                raise FileNotFoundError("R6-FREQUENCY-POLICY.json")
        LC._FP = _NoJSON
        check("json_missing_allow", LC.policy_decision(norm, 1) == "ALLOW")
    finally:
        LC._FP = _orig
    # unknown runid: an F6 tier refuses (no ungoverned stress run); a
    # non-F6 synthetic id (test/toy fixtures) runs ungated.
    check("unknown_f6_refused", refused(lambda: LC.policy_decision("X09-F6-W1", 1)))
    check("unknown_nonf6_allow", LC.policy_decision("X01-F0-W1", 1) == "ALLOW")

def test_scheduler_all_excludes_redundant():
    """[R6-FREQPOLICY] lsu_r6_schedule.sh must drop schedule_enabled=false cells
    from --cells all AND from an explicit --cells list, with one visible drop
    line per RunID, while schedule_enabled=true cells stay selected.

    The live ready_contract.json (post R6-RECONCILE 110b96aa) has gate={} and 0
    READY rows, so --cells all against it dies at the binary check before any
    selection exists. The scheduler is therefore driven through a fixture
    contract built from REAL contract rows whose statuses mirror the
    pre-RECONCILE READY set (A04-F6-W3 — STRESS_REDUNDANT, schedule_enabled=
    false — was genuinely READY then and leaked into --cells all). Without a
    selectable disabled cell this test would be vacuous."""
    import subprocess, tempfile, os, shutil
    pol = P.load_policy()
    sched = {e["run_id"]: e for e in pol["entries"]}
    con = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json").read_text("utf-8"))
    rows = {e["run_id"]: e for e in con["entries"]}

    KEEP = ["A01-F0-W3", "T04-F6-W4"]   # NORMAL / STRESS_ONLY rep -> schedule_enabled=true
    DROP = ["A04-F6-W3", "A06-F6-W5"]   # STRESS_REDUNDANT -> schedule_enabled=false
    HELD = ["T01-F0-W4"]                # contract-BLOCKED control (policy would allow it)
    check("sched_fixture_policy_keeps",
          all(sched[r].get("schedule_enabled") is True for r in KEEP),
          str([(r, sched[r].get("schedule_enabled")) for r in KEEP]))
    check("sched_fixture_policy_drops",
          all(sched[r].get("schedule_enabled") is False for r in DROP),
          str([(r, sched[r].get("schedule_enabled")) for r in DROP]))

    binpath = REPO / "CHAOS" / "gem5" / "build" / "ARM" / "gem5.opt"
    if not (binpath.exists() and os.access(binpath, os.X_OK)):
        check("sched_fixture_binary", False, "missing executable %s" % binpath)
        return
    binsha = subprocess.run(["sha256sum", str(binpath)],
                            capture_output=True, text=True).stdout.split()[0]
    entries = []
    for rid in KEEP + DROP:
        e = dict(rows[rid]); e["status"] = "READY"; entries.append(e)
    for rid in HELD:                      # stays contract-BLOCKED
        entries.append(dict(rows[rid]))
    fixture = {
        "source": "tests/test_lsu_freq_policy.py::test_scheduler_all_excludes_redundant "
                  "(REAL contract rows; READY set mirrors pre-R6-RECONCILE state)",
        "total": len(entries),
        "status": {"READY": len(KEEP) + len(DROP), "BLOCKED": len(HELD)},
        "seeds_per_cell": 1, "max_parallel": 1,
        "formal_outdir": "runs/lsu/r6_freqpolicy_t3_fixture",
        "fs_checkpoint": con["fs_checkpoint"],
        "gate": {"binary": str(binpath), "binary_sha256": binsha},
        "verdict": {"formal_phase": "screening", "screening_target": 385,
                    "focus_target": 2401, "focus_runids": []},
        "entries": entries,
    }
    RUNROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_freqpolicy_t3_fixture"  # script refuses runroot outside runs/lsu

    def sched_dry(cells):
        shutil.rmtree(RUNROOT, ignore_errors=True)   # no stale plan.tsv can mask a failure
        with tempfile.TemporaryDirectory() as td:
            cpath = os.path.join(td, "fixture_contract.json")
            with open(cpath, "w") as f:
                json.dump(fixture, f, ensure_ascii=False)
            r = subprocess.run(["bash", str(REPO / "tools" / "lsu_r6_schedule.sh"),
                                "--contract", cpath, "--runroot", RUNROOT,
                                "--cells", cells, "--dry-run"],
                               capture_output=True, text=True, cwd=str(REPO))
        plan = os.path.join(RUNROOT, "plan.tsv")
        plan_ids = ([l.split("\t")[0] for l in open(plan).read().splitlines() if l.strip()]
                    if os.path.isfile(plan) else None)
        return r, plan_ids

    r, plan_ids = sched_dry("all")
    check("scheduler_all_dryrun_ok", r.returncode == 0, (r.stderr or r.stdout)[-300:])
    if r.returncode != 0:
        return
    check("scheduler_all_excludes_disabled",
          plan_ids is not None and not (set(DROP) & set(plan_ids)),
          str(sorted(set(DROP) & set(plan_ids or []))))
    check("scheduler_all_drop_lines_visible",
          all(("[R6-FREQPOLICY] drop %s: schedule_enabled=false" % rid) in r.stdout
              for rid in DROP),
          r.stdout[-400:])
    check("scheduler_all_keeps_enabled",
          set(KEEP) <= set(plan_ids or []), str(plan_ids))
    check("scheduler_all_blocked_still_held",
          not (set(HELD) & set(plan_ids or [])), str(plan_ids))

    # ruling: a MANUALLY listed schedule_enabled=false cell is dropped, not silently run
    r2, plan_ids2 = sched_dry(",".join(["A01-F0-W3"] + DROP))
    check("scheduler_explicit_dryrun_ok", r2.returncode == 0, (r2.stderr or r2.stdout)[-300:])
    if r2.returncode != 0:
        return
    check("scheduler_explicit_drops_disabled", plan_ids2 == ["A01-F0-W3"], str(plan_ids2))
    check("scheduler_explicit_drop_line_visible",
          all(("[R6-FREQPOLICY] drop %s: schedule_enabled=false" % rid) in r2.stdout
              for rid in DROP),
          r2.stdout[-400:])

def test_runner_manifest_carries_policy():
    """[R6-FREQPOLICY] lsu_runner.build_manifest must carry the frequency
    policy (run_policy/required_seeds/include_in_statistics) read from the
    overlay — the runner never re-derives the rule. Real signature is
    build_manifest(item_id, phase, sample_index, ...): ITEM-054 -> T04-F6-W4
    (representative F6), ITEM-041 -> T01-F0-W4 (NORMAL)."""
    import lsu_runner as LR
    m = LR.build_manifest("ITEM-054", "pilot", 0)          # T04-F6-W4
    check("manifest_stress_run_id", m.get("run_id") == "T04-F6-W4", str(m.get("run_id")))
    check("manifest_run_policy", m.get("run_policy") == "STRESS_ONLY", str(m.get("run_policy")))
    check("manifest_required_seeds", m.get("required_seeds") == 1, str(m.get("required_seeds")))
    check("manifest_stress_not_in_stats", m.get("include_in_statistics") is False,
          str(m.get("include_in_statistics")))
    m2 = LR.build_manifest("ITEM-041", "pilot", 0)         # T01-F0-W4
    check("manifest_normal_run_id", m2.get("run_id") == "T01-F0-W4", str(m2.get("run_id")))
    check("manifest_normal_policy", m2.get("run_policy") == "NORMAL", str(m2.get("run_policy")))
    check("manifest_normal_seeds", m2.get("required_seeds") == 3, str(m2.get("required_seeds")))
    check("manifest_normal_in_stats", m2.get("include_in_statistics") is True,
          str(m2.get("include_in_statistics")))
    # UNKNOWN_RUNID: query() returns a SHORT dict with no run_policy key —
    # the manifest must degrade to "UNKNOWN" and still freeze, never crash.
    _orig_query = P.query
    try:
        P.query = lambda pol, rid, seed: {"run_id": rid, "seed": seed,
                                          "decision": "UNKNOWN_RUNID"}
        m3 = LR.build_manifest("ITEM-054", "pilot", 0)
        check("manifest_unknown_runid_degrades",
              m3.get("run_policy") == "UNKNOWN", str(m3.get("run_policy")))
    finally:
        P.query = _orig_query
    # overlay unavailable (policy JSON missing): the manifest must still be
    # produced (no run_policy key, or "UNKNOWN") — never an exception.
    _orig_load = P.load_policy
    try:
        def _no_json(*a, **k):
            raise FileNotFoundError("R6-FREQUENCY-POLICY.json")
        P.load_policy = _no_json
        m4 = LR.build_manifest("ITEM-054", "pilot", 0)
        check("manifest_overlay_optional",
              m4.get("run_id") == "T04-F6-W4"
              and ("run_policy" not in m4 or m4.get("run_policy") == "UNKNOWN"),
              str(m4.get("run_policy")))
    finally:
        P.load_policy = _orig_load

def test_ready_contract_policy_axis():
    """[R6-FREQPOLICY] ready_contract 报告政策轴，但政策 ≠ 技术 BLOCKED。

    live 契约 325 行全 BLOCKED 是 R6-RECONCILE 110b96aa 的真实技术状态
    （runid_map 阻塞 + 链门禁降级），与频率政策无关 —— 因此断言的不是
    "无 BLOCKED"，而是**两轴互不干涉**：
      1) 每行 policy_state ∈ {NORMAL, STRESS_ONLY, STRESS_REDUNDANT}；
      2) 顶层 policy_counts 恰为逐行 tally（Σ == 325）；
      3) T04-F6-W4（钉死的代表 F6）为 STRESS_ONLY；
      4) 独立轴：同一输入，有/无 overlay 两次 build_contract 的
         (run_id, status, category) 逐行相同 —— 政策绝不改写技术判定
         （overlay 缺失时该轴降级 UNKNOWN 并响亮计数，同样不改写）。"""
    VALID = {"NORMAL", "STRESS_ONLY", "STRESS_REDUNDANT"}
    doc = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json")
                     .read_text("utf-8"))
    ent = doc["entries"]
    check("contract_rows_325", doc["total"] == 325 == len(ent),
          f"total={doc['total']} len={len(ent)}")
    check("policy_state_present", all("policy_state" in e for e in ent))
    bad = [e["run_id"] for e in ent if e.get("policy_state") not in VALID]
    check("policy_state_valid_enum", not bad, str(bad[:5]))
    tally = {}
    for e in ent:
        tally[e.get("policy_state")] = tally.get(e.get("policy_state"), 0) + 1
    pc = doc.get("policy_counts")
    check("policy_counts_tally_entries", pc == tally, f"doc={pc} recount={tally}")
    check("policy_counts_sum_total", pc is not None and sum(pc.values()) == 325,
          str(pc))
    t04 = next((e for e in ent if e["run_id"] == "T04-F6-W4"), None)
    check("t04_f6_w4_stress_only",
          t04 is not None and t04.get("policy_state") == "STRESS_ONLY",
          str(t04 and t04.get("policy_state")))
    # 独立轴：同一输入（契约记录的真证据根）下，有/无 overlay 的重建
    # status/category 必须逐行相同。
    import lsu_ready_contract as RC
    root = doc["chain_gate"]["evidence_root"]
    args = (str(RC.DEFAULT_MAP), str(RC.DEFAULT_MATRIX),
            str(REPO / "docs/gem5-fi/lsu/mdspec/coverage_matrix.md"))
    try:
        with_pol = RC.build_contract(*args, evidence_root=root)
        no_pol = RC.build_contract(*args, evidence_root=root, policy={})
    except Exception as ex:                    # 实现前：build_contract 无 policy 形参
        check("policy_axis_rebuild", False, repr(ex))
        return
    check("policy_axis_rebuild", True)

    def cols(rows):
        return [(r["run_id"], r["status"], r["category"]) for r in rows]
    check("rebuild_rows_325", len(with_pol) == len(no_pol) == 325,
          f"{len(with_pol)}/{len(no_pol)}")
    diffs = [(a, b) for a, b in zip(cols(with_pol), cols(no_pol)) if a != b]
    check("policy_never_rewrites_status_category", not diffs, str(diffs[:3]))
    check("rebuild_with_policy_enum",
          all(r["policy_state"] in VALID for r in with_pol),
          str([r["policy_state"] for r in with_pol
               if r["policy_state"] not in VALID][:5]))
    check("rebuild_without_policy_loud_unknown",
          all(r["policy_state"] == "UNKNOWN" for r in no_pol),
          str([r.get("policy_state") for r in no_pol
               if r.get("policy_state") != "UNKNOWN"][:5]))

def test_status_table_policy_axis():
    """[R6-FREQPOLICY] R6-STATUS-TABLE 第三条正交只读轴 policy_state。

    真实顶层形状（tools/lsu_r6_status_table.py 产物）：{meta, summary, rows}，
    rows=325 契约 RunID。政策轴只报告、不裁决：STRESS_REDUNDANT（政策不
    要求）的行绝不因政策被计为 failure/BLOCKED/EVIDENCE_MISSING——
    evidence_state/eligibility 照实报告磁盘与上游事实；overlay 缺失或
    RunID 不在权威 325 entries（legacy CSV-only F6）⇒ UNKNOWN（不可治理，
    响亮），绝不静默等于 NORMAL。"""
    VALID = {"NORMAL", "STRESS_ONLY", "STRESS_REDUNDANT"}
    doc = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json")
                     .read_text("utf-8"))
    rows = doc["rows"]                      # 真实形状：doc 本身就是 dict+rows
    check("status_rows_325", len(rows) == 325, str(len(rows)))
    check("policy_axis_present", all("policy_state" in r for r in rows))
    bad = [r["run_id"] for r in rows
           if r.get("policy_state") not in VALID | {"UNKNOWN"}]
    check("policy_axis_enum", not bad, str(bad[:5]))
    check("policy_axis_no_unknown",
          all(r.get("policy_state") in VALID for r in rows),
          "overlay 缺失或存在不受管 RunID（policy_state=UNKNOWN）")
    # 政策不要求的 F6：无任何流 ⇒ NOT_RUN（绝不是 EVIDENCE_MISSING/TRUNCATED）
    bad = [r["run_id"] for r in rows
           if r.get("policy_state") == "STRESS_REDUNDANT"
           and r.get("evidence_state") in ("EVIDENCE_MISSING", "TRUNCATED")]
    check("redundant_not_counted_missing", not bad, str(bad[:5]))
    bad = [r["run_id"] for r in rows
           if r.get("policy_state") == "STRESS_REDUNDANT"
           and r.get("samples", 0) == 0
           and r.get("evidence_state") != "NOT_RUN"]
    check("redundant_no_runs_stays_not_run", not bad, str(bad[:5]))
    # 逐行 tally == summary.policy_states（同源，Σ == 325）
    tally = {}
    for r in rows:
        tally[r["policy_state"]] = tally.get(r["policy_state"], 0) + 1
    ps = doc["summary"].get("policy_states")
    check("policy_states_tally", ps == tally, f"doc={ps} recount={tally}")
    check("policy_states_sum_325", ps is not None and sum(ps.values()) == 325,
          str(ps))
    # T04-F6-W4（钉死的代表 F6）：STRESS_ONLY 且既有证据保留（样本+准入在场）
    t04 = next((r for r in rows if r["run_id"] == "T04-F6-W4"), None)
    check("t04_f6_w4_stress_only",
          t04 is not None and t04.get("policy_state") == "STRESS_ONLY",
          str(t04 and t04.get("policy_state")))
    check("t04_f6_w4_evidence_preserved",
          t04 is not None and t04.get("samples", 0) > 0
          and t04.get("admitted_samples", 0) > 0,
          str(t04 and {k: t04.get(k) for k in
                       ("samples", "activated_samples", "admitted_samples",
                        "evidence_state", "eligibility")}))
    # 降级与不受管（直接调 adjudicate，无流样本，快）：
    #   无 overlay ⇒ UNKNOWN；legacy CSV-only F6（不在权威 entries）⇒ UNKNOWN
    import lsu_r6_status_table as ST
    idx = ST._load_policy_index()
    check("policy_index_loaded", idx is not None and len(idx) == 325,
          str(idx and len(idx)))
    pilots = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json")
                        .read_text("utf-8")).get("pilots", {})
    main_root = Path("/home/sdc/gem5-fi-ding")
    row = ST.adjudicate("T04-F6-W4", [], None, pilots,
                        main_root, main_root / "runs/lsu", idx)
    check("adjudicate_stress_only", row["policy_state"] == "STRESS_ONLY",
          str(row["policy_state"]))
    row2 = ST.adjudicate("T04-F6-W4", [], None, pilots,
                         main_root, main_root / "runs/lsu", {})
    check("adjudicate_no_overlay_unknown", row2["policy_state"] == "UNKNOWN",
          str(row2["policy_state"]))
    row3 = ST.adjudicate("T09-F6-W4", [], None, pilots,
                         main_root, main_root / "runs/lsu", idx)
    check("adjudicate_legacy_not_normal", row3["policy_state"] == "UNKNOWN",
          str(row3["policy_state"]))

def main():
    test_policy_covers_all_runids()
    test_entries_exactly_325_authoritative()
    test_campaign_refuses_redundant_and_seed2()
    test_policy_decision_gate_semantics()
    test_scheduler_all_excludes_redundant()
    test_runner_manifest_carries_policy()
    test_ready_contract_policy_axis()
    test_status_table_policy_axis()
    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
