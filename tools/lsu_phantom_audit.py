#!/usr/bin/env python3
"""audit_tool.py — Subagent D 只读污染审计工具（F-047 幻影激活扩大审计，D-2026-10-10-幻影审计）。

绝对只读：只解析 runs/lsu/pilot/ 下已有文件，全部输出写 /tmp/lsu_analysis_D/。

审计范围判定（源自源码与工具链实证，证据见 AUDIT_REPORT.md §1）：
  PRE-op-filtered  : CHAOSAddrPath::maybeCorruptPre 且 fire 后有 isLoad/!isLoad 过滤
                     —— L01 (l01_load_addr, load-only), L02 (l02_load_state, load-only)
                        [S04/S05/S11/S13 store-only 同理，但 pilot 无 Store_Queue 单元，零样本]
  PRE-unfiltered   : CHAOSAddrPath::maybeCorruptPre 无 op 类过滤
                     —— A04 (a04_subst), A05 (a05_shift), A06 (a06_size), A08 (a08_subst)
  LSQFWD-L03-site  : CHAOSLSQFwd::violationCorrupt（onEligible 后无过滤、写入必然执行）
                     —— L03（注意 F-047(b): --lsqfwd_l03 不接线，structMode=byte_flip，
                        fire 落点由共享 trigger 决定；本工具按日志实际落点记账）
  POST (对照,不入污染审计): A01/A02/A03 maybeCorrupt（sendFragment 钩子）

幻影判定规则（RULES.md 全文）：
  P1 pure-phantom     : trigger.injected>=1 且注入日志零写入行（trigger 计数与写入脱钩的直接证据）
  P2 partial-phantom  : trigger.injected > 写入行数 >= 1（部分 fire 落错 op 类）
  N  noop-write       : 写入行存在但 old_addr==new_addr 且 old_size==new_size（写入执行、值未变）
  R  real             : 至少一行值变化写入
  三方一致性           : l5_verdict.injected vs guard.out CHAOS_LSU_TRIGGER vs 日志写入行
                        (+ CHAOS_L0_FUNNEL 行、行内 faults_injected 计数、checksum/outcome 复算)
"""
import json
import re
import sys
from pathlib import Path

REPO = Path("/home/sdc/gem5-fi-ding")
PILOT = REPO / "runs/lsu/pilot"
OUT = Path("/tmp/lsu_analysis_D")

# ---- scope tables (provenance: tools/lsu_campaign.py MODEL_FLAGS + CHAOSAddrPath.cc read 2026-10-10)
HOOK_CLASS = {
    # model: (hook_class, pre_mode)
    "L01": ("PRE_op_filtered", "l01_load_addr"),
    "L02": ("PRE_op_filtered", "l02_load_state"),
    "S04": ("PRE_op_filtered", "s04_store_subst"),   # store-only; no pilot samples
    "S05": ("PRE_op_filtered", "s05_store_size"),
    "S11": ("PRE_op_filtered", "s11_store_lost"),
    "S13": ("PRE_op_filtered", "s13_store_addr"),
    "A04": ("PRE_unfiltered", "a04_subst"),
    "A05": ("PRE_unfiltered", "a05_shift"),
    "A06": ("PRE_unfiltered", "a06_size"),
    "A08": ("PRE_unfiltered", "a08_subst"),
    "L03": ("LSQFWD_L03_site", None),
    "A01": ("POST_control", None),
    "A02": ("POST_control", None),
    "A03": ("POST_control", None),
}
PRE_WRITE_RE = re.compile(r"Site: lsq_pushRequest_PRE")
L03_CV_RE = re.compile(r"Site: checkViolations_L03")
L03_FWD_RE = re.compile(r"Site: store->load_forward")
POST_WRITE_RE = re.compile(r"Site: lsq_sendFragmentToTranslation")
TRIG_RE = re.compile(r"CHAOS_LSU_TRIGGER: injector=(\S+) tier=(F\d) attempted=(\d+) "
                     r"eligible=(\d+) injected=(\d+)")
FUNNEL_RE = re.compile(r"CHAOS_L0_FUNNEL: (\S+) attempted=(\d+) eligible=(\d+) "
                       r"injected=(\d+) activated=(\d+)")
L0_RE = re.compile(r"CHAOS_L0: (\S+): target=(\d+) reads=(\d+) overwritten=(\d+) "
                   r"at=(\d+) hit=(\d+)")
PRE_LINE_RE = re.compile(
    r"Tick: (\d+), Site: lsq_pushRequest_PRE, mode=(\S+), "
    r"old_addr=0x([0-9a-f]+), new_addr=0x([0-9a-f]+), "
    r"old_size=(\d+), new_size=(\d+), faults_injected: (\d+)")
POST_LINE_RE = re.compile(
    r"Tick: (\d+), Site: lsq_sendFragmentToTranslation, mode=(\S+), "
    r"old_vaddr=0x([0-9a-f]+), new_vaddr=0x([0-9a-f]+), "
    r"faults_injected: (\d+)")
# fault-target semantics per pre_mode (value-change evidence):
#   a04/a08: addr (do-while guarantees !=), a05: addr (rotate may be identity),
#   a06: size (target may equal original), l01: addr (XOR always !=),
#   l02: FLAGS (not logged — value-identity NOT observable),
#   a01/a02 (POST): vaddr (XOR always !=), L03-cv: cmp_addr (XOR, not logged)
ADDR_TARGET = {"a04_subst", "a08_subst", "a05_shift", "l01_load_addr"}
SIZE_TARGET = {"a06_size"}
FLAG_TARGET = {"l02_load_state"}
EXIT_RE = re.compile(r'"exit_code": (-?\d+)')
SEED_RE = re.compile(r'"(--addrpath_rng_seed|--rng_seed|--l1d_rng_seed|--prefetch_rng_seed|--exmon_rng_seed|--tlb_rng_seed)", "(\d+)"')
PREMODE_RE = re.compile(r'"--agu_pre_mode", "(\S+)"')
CHECKSUM_RE = re.compile(r"^([0-9a-f]{16})$", re.M)


def parse_guard(guard_path):
    g = {"exists": guard_path.exists()}
    if not g["exists"]:
        return g
    txt = guard_path.read_text(errors="replace")
    g["run_finish"] = '"action": "run-finish"' in txt
    m = TRIG_RE.search(txt)
    g["trigger"] = {"injector": m.group(1), "tier": m.group(2),
                    "attempted": int(m.group(3)), "eligible": int(m.group(4)),
                    "injected": int(m.group(5))} if m else None
    e = EXIT_RE.search(txt)
    g["exit_code"] = int(e.group(1)) if e else None
    s = SEED_RE.search(txt)
    g["seed"] = int(s.group(2)) if s else None
    pm = PREMODE_RE.search(txt)
    g["pre_mode_cmd"] = pm.group(1) if pm else None
    cs = CHECKSUM_RE.findall(txt)
    g["checksum_last"] = cs[-1] if cs else None
    g["timeout_killed"] = "TIMEOUT" in txt and g["exit_code"] in (None, -9, 124)
    return g


def parse_log(log_path):
    r = {"exists": log_path.exists()}
    if not r["exists"]:
        return r
    txt = log_path.read_text(errors="replace")
    pre_lines = PRE_LINE_RE.findall(txt)
    r["pre_writes"] = len(PRE_WRITE_RE.findall(txt))
    r["pre_write_records"] = [
        {"tick": int(t), "mode": mo, "old_addr": oa, "new_addr": na,
         "old_size": int(os_), "new_size": int(ns), "faults_injected": int(fi)}
        for t, mo, oa, na, os_, ns, fi in pre_lines]
    r["post_write_records"] = [
        {"tick": int(t), "mode": mo, "old_vaddr": ov, "new_vaddr": nv,
         "faults_injected": int(fi)}
        for t, mo, ov, nv, fi in POST_LINE_RE.findall(txt)]
    r["l03_cv_writes"] = len(L03_CV_RE.findall(txt))
    r["l03_fwd_writes"] = len(L03_FWD_RE.findall(txt))
    r["post_writes"] = len(POST_WRITE_RE.findall(txt))
    f = FUNNEL_RE.search(txt)
    r["funnel"] = {"injector": f.group(1), "attempted": int(f.group(2)),
                   "eligible": int(f.group(3)), "injected": int(f.group(4)),
                   "activated": int(f.group(5))} if f else None
    l0 = L0_RE.search(txt)
    r["l0"] = {"target": int(l0.group(2)), "reads": int(l0.group(3)),
               "hit": int(l0.group(6))} if l0 else None
    return r


def recompute_outcome(checksum, golden, exit_code, timeout):
    if timeout:
        return "Timeout"
    if exit_code not in (0, None):
        return "Crash"
    if checksum is None:
        return "Crash"
    if golden and checksum != golden:
        return "SDC"
    return "Masked"


def audit_sample(unit, item, run_id, model, s_idx, golden):
    udir = PILOT / unit
    sd = udir / f"{item}_s{s_idx}"
    rec = {"item": item, "runid": run_id, "sample_index": s_idx,
           "run_dir": str(sd)}
    verdict_path = sd / "l5_verdict.json"
    if not verdict_path.exists():
        rec.update({"error": "l5_verdict.json missing", "in_scope": False})
        return rec
    v = json.loads(verdict_path.read_text())
    guard = parse_guard(udir / f"{item}_s{s_idx}_guard.out")
    hook = HOOK_CLASS.get(model, ("UNKNOWN", None))
    # log file: addrpath family -> addrpath_injections.log; lsqfwd -> lsq_fwd_injections.log
    logs = sorted(sd.glob("*injections.log"))
    log = parse_log(logs[0]) if logs else {"exists": False}
    log_name = logs[0].name if logs else None

    rec.update({
        "model": model, "hook_class": hook[0], "pre_mode_expected": hook[1],
        "seed": guard.get("seed"),
        "golden": golden,
        "original_outcome": v.get("outcome"),
        "original_faults_injected": v.get("injected"),
        "original_activated": v.get("activated"),
        "original_classes": v.get("classes"),
        "original_crash_kind": v.get("crash_kind"),
        "verdict_checksum": v.get("checksum"),
        "funnel_source": v.get("funnel_source"),
        "gem5_exit": v.get("gem5_exit"),
        "guard_run_finish": guard.get("run_finish"),
        "trigger_line": guard.get("trigger"),
        "log_file": log_name,
        "log_pre_writes": log.get("pre_writes", 0) if log.get("exists") else None,
        "log_noop_writes": log.get("noop_writes", 0) if log.get("exists") else None,
        "log_l03_cv_writes": log.get("l03_cv_writes", 0) if log.get("exists") else None,
        "log_l03_fwd_writes": log.get("l03_fwd_writes", 0) if log.get("exists") else None,
        "log_post_writes": log.get("post_writes", 0) if log.get("exists") else None,
        "log_funnel": log.get("funnel"),
        "log_l0": log.get("l0"),
        "guard_checksum_last": guard.get("checksum_last"),
    })
    # activated scope filter
    if v.get("error") or (v.get("activated") or 0) < 1:
        rec["in_scope"] = False
        rec["note"] = "not an activated sample (error or activated<1)"
        return rec
    rec["in_scope"] = True

    trig = guard.get("trigger")
    trig_inj = trig["injected"] if trig else None
    pre_mode = hook[1]
    wrec = log.get("pre_write_records") or []
    # per-hook write-line count (the site the model actually injects at)
    if hook[0] == "LSQFWD_L03_site":
        writes = (log.get("l03_cv_writes", 0) + log.get("l03_fwd_writes", 0)
                  if log.get("exists") else None)
        value_ev = "xor_structural (cmp_addr^=bit; per-line values not logged)"
    elif hook[0] == "POST_control":
        writes = log.get("post_writes") if log.get("exists") else None
        value_ev = "vaddr_change (XOR bit flip)"
    else:
        writes = log.get("pre_writes") if log.get("exists") else None
        value_ev = None
    # noop = write executed but fault-target value identical (MODE-AWARE):
    if pre_mode in ADDR_TARGET:
        noop = sum(1 for w in wrec if w["old_addr"] == w["new_addr"])
        value_ev = "addr_change"
    elif pre_mode in SIZE_TARGET:
        noop = sum(1 for w in wrec if w["old_size"] == w["new_size"])
        value_ev = "size_change"
    elif pre_mode in FLAG_TARGET:
        noop = 0  # fault target = Request flags, NOT logged — identity unverifiable
        value_ev = "flag_write (value-identity NOT log-observable)"
    else:
        noop = 0
    rec["trigger_injected"] = trig_inj
    rec["actual_write_lines"] = writes
    rec["value_evidence_kind"] = value_ev

    ev = []
    # ---- phantom / noop / real verdict (RULES.md P1/P2/N/R, mode-aware) ----
    if not log.get("exists"):
        cat, actual = "uncertain", "uncertain"
        ev.append("injection log missing")
    elif writes is None:
        cat, actual = "uncertain", "uncertain"
    elif writes == 0:
        if trig_inj is None:
            cat, actual = "uncertain", "uncertain"
            ev.append("no trigger line and zero site-matched writes but activated>=1 (anomaly)")
        else:
            cat = "phantom_pure"
            actual = False
            ev.append(f"P1: trigger injected={trig_inj} but 0 write lines at the "
                      f"model's site in {log_name}")
            fl = log.get("funnel")
            if fl and fl["injected"] == 0:
                ev.append(f"P1 corroborated: CHAOS_L0_FUNNEL injected={fl['injected']} "
                          f"activated={fl['activated']} (injector own count = 0 writes)")
            l0 = log.get("l0")
            if l0 and l0["target"] == 0:
                ev.append("P1 corroborated: CHAOS_L0 target=0 reads=0 hit=0 "
                          "(no item ever registered)")
    else:
        real = writes - (noop or 0)
        cat = None
        if trig_inj is not None and trig_inj > writes:
            cat = "phantom_partial"
            ev.append(f"P2: trigger injected={trig_inj} > write lines={writes} "
                      f"({trig_inj - writes} phantom fires)")
        if (noop or 0) > 0 and real == 0:
            cat = "noop_only_write"
            actual = "noop_only"
            ev.append(f"N: {noop} write line(s) executed but fault-target value "
                      f"identical (no fault effect)")
        else:
            actual = True
            if (noop or 0) > 0:
                cat = cat if cat == "phantom_partial" else "real_with_noop"
                ev.append(f"N: {noop} of {writes} write line(s) value-identical (noop), "
                          f"{real} value-changing")
            else:
                cat = cat if cat == "phantom_partial" else "real"
                ev.append(f"R: {writes} write line(s) at the model's site; {value_ev}")
    rec["category"] = cat
    rec["actual_fault_write"] = actual

    # ---- three-way consistency checks ----
    checks = {}
    vinj = v.get("injected")
    if trig_inj is not None:
        checks["verdict_vs_trigger"] = "OK" if vinj == trig_inj else \
            f"MISMATCH verdict={vinj} trigger={trig_inj}"
    if writes is not None:
        checks["verdict_vs_log_writes"] = "OK" if vinj == writes else \
            f"MISMATCH verdict={vinj} log_writes={writes} (contamination signature if verdict>log)"
    fl = log.get("funnel")
    if fl and writes is not None:
        checks["funnel_vs_log_writes"] = "OK" if fl["injected"] == writes else \
            f"MISMATCH funnel={fl['injected']} log_writes={writes}"
    wrec2 = log.get("post_write_records") or []
    if wrec and hook[1] is not None:
        expect = list(range(1, len(wrec) + 1))
        got = [w["faults_injected"] for w in wrec]
        checks["line_counter"] = "OK" if got == expect else f"MISMATCH {got}"
        modes = {w["mode"] for w in wrec}
        checks["mode_match"] = "OK" if modes == {hook[1]} else \
            f"MISMATCH log_modes={modes} expected={hook[1]}"
    if wrec2:
        expect2 = list(range(1, len(wrec2) + 1))
        got2 = [w["faults_injected"] for w in wrec2]
        checks["post_line_counter"] = "OK" if got2 == expect2 else f"MISMATCH {got2}"
    oc = recompute_outcome(guard.get("checksum_last"), golden,
                           guard.get("exit_code"), guard.get("timeout_killed"))
    checks["outcome_recompute"] = "OK" if oc == v.get("outcome") else \
        f"MISMATCH recomputed={oc} verdict={v.get('outcome')}"
    if guard.get("seed") is not None:
        checks["seed_present"] = "OK"
    rec["consistency_checks"] = checks
    rec["evidence"] = ev

    # ---- suggested class per user ruling ----
    if cat == "phantom_pure":
        rec["suggested_class"] = ("InvalidInjection(phantom:triggered-not-applied) "
                                  "[schema class absent — see schema check]")
        rec["note"] = ("trigger fired on wrong op class; zero fault write; "
                       "checksum==golden is vacuous; must NOT count as Masked/activated")
    elif cat == "phantom_partial":
        rec["suggested_class"] = "keep original class minus phantom fires (denominator -= phantoms)"
    elif cat == "noop_only_write":
        rec["suggested_class"] = ("NoEffect(noop-write: applied-but-value-identical) "
                                  "[schema class absent — see schema check]")
        rec["note"] = ("write executed but old==new; zero fault effect by construction; "
                       "A03 precedent (CHAOSAddrPath.cc:156-164) subtracts no-op from activated")
    else:
        rec["suggested_class"] = "keep original class (real value-changing write confirmed)"
        if rec.get("value_evidence_kind", "").startswith("flag_write"):
            rec["note"] = ("l02 fault target = Request::STRICT_ORDER flag, NOT logged — "
                           "write execution confirmed by log line; flag value-identity "
                           "not verifiable from log (if flag was already set, no-op; "
                           "SE workloads do not preset STRICT_ORDER)")
        if rec.get("value_evidence_kind", "").startswith("xor_structural"):
            rec["note"] = ("L03-site write: cmp_addr ^= bit is value-changing by construction; "
                           "per-line old/new not logged. Model-identity caveat: --lsqfwd_l03 "
                           "flag is not wired (F-047(b)); site reached via shared-trigger "
                           "race, structMode=byte_flip in config.ini")
    return rec


def main():
    manifest_rows, summary = [], {}
    for unit in ("AGU", "Load_Queue"):
        udir = PILOT / unit
        status = json.loads((udir / "unit_status.json").read_text())
        um = json.loads((udir / "unit_manifest.json").read_text())
        run_ids = {a["item"]: a["run_id"] for a in um["admission"]}
        goldens = {a["item"]: (a["reason"].split("golden=")[-1].strip()
                               if "golden=" in a["reason"] else None)
                   for a in um["admission"]}
        for item, st in sorted(status["items"].items()):
            run_id = run_ids.get(item, "?")
            model = run_id.split("-")[0]
            hook = HOOK_CLASS.get(model, ("UNKNOWN", None))[0]
            agg = {"unit": unit, "runid": run_id, "model": model,
                   "hook_class": hook,
                   "status": st.get("status"),
                   "original_activated_runs": st.get("activated_runs"),
                   "original_five_class": st.get("five_class"),
                   "original_simfail": st.get("post_activation_simulator_failure"),
                   "samples_audited": 0, "phantom_pure": 0, "phantom_partial": 0,
                   "noop_only": 0, "real": 0, "real_with_noop": 0,
                   "uncertain": 0, "not_in_scope": 0,
                   "corrected_five_class": {}, "mismatch_flags": []}
            # iterate sample dirs s0.. until absent
            s = 0
            while True:
                sd = udir / f"{item}_s{s}"
                if not sd.is_dir():
                    break
                rec = audit_sample(unit, item, run_id, model, s, goldens.get(item))
                manifest_rows.append(rec)
                if not rec.get("in_scope"):
                    agg["not_in_scope"] += 1
                else:
                    agg["samples_audited"] += 1
                    cat = rec["category"]
                    if cat == "phantom_pure":
                        agg["phantom_pure"] += 1
                    elif cat == "phantom_partial":
                        agg["phantom_partial"] += 1
                    elif cat == "noop_only_write":
                        agg["noop_only"] += 1
                    elif cat == "real":
                        agg["real"] += 1
                    elif cat == "real_with_noop":
                        agg["real_with_noop"] += 1
                    else:
                        agg["uncertain"] += 1
                    for k, val in rec.get("consistency_checks", {}).items():
                        if val != "OK" and k != "seed_present":
                            agg["mismatch_flags"].append(f"s{s}:{k}:{val}")
                s += 1
            # corrected five-class: drop phantom_pure + noop_only from their original class
            corr = dict(st.get("five_class") or {})
            dropped = {}
            for rec in manifest_rows:
                if rec.get("item") == item and rec.get("in_scope") and \
                        rec.get("category") in ("phantom_pure", "noop_only_write"):
                    oc = rec.get("original_outcome")
                    if rec.get("original_crash_kind") == "simulator_assert" and oc == "Crash":
                        key = "post_activation_simulator_failure"
                    else:
                        key = oc
                    corr[key] = max(0, corr.get(key, 0) - 1)
                    dropped[rec["sample_index"]] = rec["category"]
            agg["corrected_five_class"] = corr
            agg["dropped_samples"] = dropped
            agg["tentative_effective_activated"] = (
                agg["real"] + agg["real_with_noop"])
            agg["write_confirmed_activated"] = (
                agg["real"] + agg["real_with_noop"] + agg["noop_only"]
                + agg["phantom_partial"])
            summary[item] = agg

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "contamination_manifest.jsonl", "w") as f:
        for r in manifest_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT / "audit_summary.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    # console digest
    print(f"total sample records: {len(manifest_rows)}")
    print(f"{'item':<10}{'runid':<13}{'hook':<18}{'orig_act':>8}{'audit':>6}"
          f"{'phantom':>8}{'partial':>8}{'noop':>6}{'real':>6}{'r+noop':>7}"
          f"{'uncert':>7}{'eff_act':>8}  flags")
    for item, a in sorted(summary.items()):
        if a["original_activated_runs"] == 0 and a["samples_audited"] == 0:
            continue
        print(f"{item:<10}{a['runid']:<13}{a['hook_class']:<18}"
              f"{a['original_activated_runs']:>8}{a['samples_audited']:>6}"
              f"{a['phantom_pure']:>8}{a['phantom_partial']:>8}{a['noop_only']:>6}"
              f"{a['real']:>6}{a['real_with_noop']:>7}{a['uncertain']:>7}"
              f"{a['tentative_effective_activated']:>8}  "
              f"{'; '.join(a['mismatch_flags'][:3]) or '-'}")


if __name__ == "__main__":
    main()
