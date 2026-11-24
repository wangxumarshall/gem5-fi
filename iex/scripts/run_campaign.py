#!/usr/bin/env python3
"""IEX v3 campaign runner: plan / control / pilot / fault / audit.

Every run is a fresh gem5 process with a unique CaseID and appended
AttemptID.  The workload ELF, input, ROI and target PC are fixed per
Model x Context; Fault and Control differ only in IEX_FAULT_ENABLED and
the selected ordinal.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = "IEX_WHEN_5x3_v3_2026-11-23"
GEM5 = os.path.join(ROOT, "gem5", "build", "ARM", "gem5.opt")
SE = os.path.join(HERE, "iex_se.py")
WORKLOAD_MANIFEST = os.path.join(ROOT, "workloads", "v3", "manifest.json")
ORACLE = os.path.join(ROOT, "oracle", "oracle_vectors.json")
RESULTS = os.path.join(ROOT, "results", SPEC)
TIMEOUT = 600

sys.path.insert(0, HERE)
import iex_oracle as oracle


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=False)
    os.replace(tmp, path)


def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(obj, sort_keys=False) + "\n")


def git_commit(path):
    try:
        return subprocess.check_output(
            ["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def git_dirty(path):
    try:
        out = subprocess.check_output(
            ["git", "-C", path, "status", "--porcelain"], text=True)
        return out.strip()
    except Exception:
        return "UNKNOWN"


def workload_index():
    """Return ContextKey -> workload record.

    The frozen manifest records the original server absolute ELF paths.  When
    the harness is used from a Git checkout, fall back to the colocated
    workloads/v3/build ELF with the same basename.  All experiment parameters
    (PC, ROI, golden values, selector mode) are unchanged.
    """
    base = os.path.join(ROOT, "workloads", "v3", "build")
    out = {}
    for c in load_json(WORKLOAD_MANIFEST)["contexts"]:
        c = dict(c)
        elf = c.get("elf", "")
        if elf and not os.path.exists(elf):
            c["elf"] = os.path.join(base, os.path.basename(elf))
        out[c["context_key"]] = c
    return out


def oracle_index():
    return load_json(ORACLE)["vectors"]


def case_matrix():
    rows = []
    for m in oracle.MODELS:
        for c in oracle.CONTEXTS:
            key = f"{m}-{c}"
            for t in oracle.TIMINGS:
                rows.append({
                    "CaseID": f"{key}-{t}",
                    "ModelID": m, "ContextID": c, "TimingID": t,
                    "ContextKey": key,
                    "Percentile": oracle.PERCENTILES[t],
                    "ControlID": f"CTRL-{key}",
                    "RunRole": "FAULT",
                })
    return rows


def plan(args):
    wm = workload_index()
    rows = case_matrix()
    assert len(rows) == 105
    assert len({r["CaseID"] for r in rows}) == 105
    for r in rows:
        assert r["ContextKey"] in wm, r
    controls = []
    for m in oracle.MODELS:
        for c in oracle.CONTEXTS:
            key = f"{m}-{c}"
            w = wm[key]
            controls.append({
                "ControlID": f"CTRL-{key}", "ContextKey": key,
                "ModelID": m, "ContextID": c, "WorkloadID": w["workload_id"],
                "ELF": w["elf"], "ELF_SHA256": w["elf_sha256"],
                "DefaultEligibleN": 100,
            })
    manifest = {
        "spec": SPEC, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_root": ROOT, "results_root": RESULTS,
        "workload_manifest": WORKLOAD_MANIFEST,
        "workload_manifest_sha256": sha256_file(WORKLOAD_MANIFEST),
        "oracle_vectors_sha256": sha256_file(ORACLE),
        "gem5_binary": GEM5, "gem5_sha256": sha256_file(GEM5),
        "gem5_git_commit": git_commit(os.path.join(ROOT, "gem5")),
        "gem5_git_status": git_dirty(os.path.join(ROOT, "gem5")),
        "se_script": SE, "se_script_sha256": sha256_file(SE),
        "model_count": 7, "context_count": 35,
        "fault_count": 105, "control_count": 35,
        "cases": rows, "controls": controls,
    }
    write_json(os.path.join(RESULTS, "manifest", "manifest.json"), manifest)
    with open(os.path.join(RESULTS, "manifest", "cases.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"PLAN PASS spec={SPEC} faults={len(rows)} controls={len(controls)}")
    env = {
        "spec": SPEC,
        "source_root": ROOT,
        "working_root": ROOT,
        "iex_when_root": RESULTS,
        "gem5_binary": GEM5,
        "gem5_sha256": sha256_file(GEM5),
        "gem5_git_commit": git_commit(os.path.join(ROOT, "gem5")),
        "gem5_git_status": git_dirty(os.path.join(ROOT, "gem5")),
        "se_script": SE, "se_script_sha256": sha256_file(SE),
        "compiler": "aarch64-openEuler-linux-gcc 12.3.1",
        "compiler_path": shutil.which("aarch64-openEuler-linux-gcc"),
        "objdump": shutil.which("objdump"),
        "cpu": "ArmO3CPU, 1 core, 1 thread, 2GHz, timing memory, "
               "classic 32KiB L1I/L1D, 256KiB L2, DDR3_1600_8x8",
        "seed_policy": "N/A_DETERMINISTIC",
        "timeout_seconds": TIMEOUT,
        "parallelism": args.jobs,
        "retry_limit": 1,
        "oracle_vectors": ORACLE,
        "workload_manifest": WORKLOAD_MANIFEST,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_json(os.path.join(RESULTS, "environment", "environment.json"), env)
    print("wrote", os.path.join(RESULTS, "manifest", "manifest.json"))


def run_dir(kind, case_or_control):
    return os.path.join(RESULTS, kind, case_or_control)


def next_attempt(case_id):
    base = None
    for kind in ("controls", "runs", "pilots"):
        p = os.path.join(RESULTS, kind, case_id)
        if os.path.isdir(p):
            base = p
            break
    if base is None:
        return 1
    n = 0
    for name in os.listdir(base):
        if name.startswith("attempt-"):
            n = max(n, int(name.split("-")[1]))
    return n + 1


def env_for(case, role, fault_enabled, selector_mode, ordinal, ncal,
            attempt_dir):
    w = workload_index()[case["ContextKey"]]
    env = os.environ.copy()
    env.update({
        "IEX_MODEL": w["model"],
        "IEX_CONTEXT": w["context"],
        "IEX_WORKLOAD": w["workload_id"],
        "IEX_FAULT_CONFIG": f"{w['model']}-CFG01",
        "IEX_ORACLE_ID": f"{w['context_key']}-ORACLE",
        "IEX_RUN_ID": f"{role}-{case.get('CaseID', case.get('ControlID'))}",
        "IEX_SAMPLE_ID": case.get("CaseID", case.get("ControlID")),
        "IEX_PAIR_ID": case.get("ControlID", ""),
        "IEX_SEED": "N/A_DETERMINISTIC",
        "IEX_GEM5_COMMIT": git_commit(os.path.join(ROOT, "gem5")),
        "IEX_FAULT_ENABLED": "1" if fault_enabled else "0",
        "IEX_TARGET_PC": w["target_pc"],
        "IEX_CONSUMER_PC": w["consumer_pc"] or "0x0",
        "IEX_ROI_START": w["roi_start"],
        "IEX_ROI_END": w["roi_end"],
        "IEX_TIMING_ID": case.get("TimingID", ""),
        "IEX_SELECTOR_MODE": selector_mode,
        "IEX_SELECT_ORDINAL": str(ordinal or 0),
        "IEX_CALIBRATED_N": str(ncal or 0),
        "IEX_ITER_PC": w["iter_pc"] or "0x0",
        "IEX_ITER_INIT": str(w["iter_init"]),
        "IEX_OLDER_BRANCH_PC": w["older_branch_pc"] or "0x0",
        "IEX_TRACE_FILE": os.path.join(attempt_dir, "trace.jsonl"),
        "IEX_CORE": "0",
    })
    return env


def run_gem5(case, role, fault_enabled, selector_mode, ordinal, ncal,
             kind, label):
    outroot = os.path.join(RESULTS, kind, label)
    os.makedirs(outroot, exist_ok=True)
    att = next_attempt(label)
    attempt_dir = os.path.join(outroot, f"attempt-{att:04d}")
    os.makedirs(attempt_dir, exist_ok=False)
    env = env_for(case, role, fault_enabled, selector_mode, ordinal, ncal,
                  attempt_dir)
    cmd = [GEM5, "-d", os.path.join(attempt_dir, "m5out"),
           "--quiet", SE, workload_index()[case["ContextKey"]]["elf"]]
    t0 = time.time()
    timed_out = False
    with open(os.path.join(attempt_dir, "stdout.txt"), "w") as so, \
         open(os.path.join(attempt_dir, "stderr.txt"), "w") as se:
        try:
            p = subprocess.run(cmd, cwd=os.path.join(ROOT, "gem5"),
                               env=env, stdout=so, stderr=se,
                               timeout=TIMEOUT)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = -9
            timed_out = True
    elapsed = time.time() - t0
    out = parse_stdout(os.path.join(attempt_dir, "stdout.txt"))
    trace_summary = summarize_trace(
        os.path.join(attempt_dir, "trace.jsonl"))
    meta = {
        "spec": SPEC, "kind": kind, "role": role,
        "label": label, "attempt": att,
        "case": case, "fault_enabled": bool(fault_enabled),
        "selector_mode": selector_mode, "select_ordinal": ordinal,
        "calibrated_n": ncal,
        "command": cmd, "cwd": os.path.join(ROOT, "gem5"),
        "env": {k: v for k, v in env.items() if k.startswith("IEX_")},
        "returncode": rc, "timed_out": timed_out,
        "elapsed_seconds": round(elapsed, 3),
        "stdout_sha256": sha256_file(
            os.path.join(attempt_dir, "stdout.txt")),
        "stderr_sha256": sha256_file(
            os.path.join(attempt_dir, "stderr.txt")),
        "trace_sha256": sha256_file(
            os.path.join(attempt_dir, "trace.jsonl"))
        if os.path.exists(os.path.join(attempt_dir, "trace.jsonl")) else "",
        "guest_output": out, "trace_summary": trace_summary,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_json(os.path.join(attempt_dir, "meta.json"), meta)
    return meta


def parse_stdout(path):
    ctx = None
    vals = []
    begin = end = False
    for line in open(path, errors="replace"):
        if line.startswith("IEX_GEM5_BEGIN"):
            begin = True
        elif line.startswith("IEX_GEM5_END"):
            end = True
        elif line.startswith("IEX-"):
            parts = line.strip().split(",")
            ctx = parts[0]
            vals = parts[1:]
    pairs = []
    for i in range(0, len(vals) - 1, 2):
        try:
            pairs.append((int(vals[i], 16), int(vals[i + 1], 16)))
        except ValueError:
            break
    return {"context": ctx, "slots": pairs,
            "raw_values": vals, "gem5_begin": begin, "gem5_end": end}


def summarize_trace(path):
    if not os.path.exists(path):
        return {"exists": False}
    n = 0
    run_end = None
    events = {}
    inject = None
    candidates = []
    for line in open(path):
        n += 1
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        events[e.get("event")] = events.get(e.get("event"), 0) + 1
        if e.get("event") == "run_end":
            run_end = e
        elif e.get("event") == "inject":
            inject = e
        elif e.get("event") in ("candidate", "eligible_control"):
            candidates.append({
                "ordinal": e.get("candidate_ordinal"),
                "seq": e.get("dynamic_instruction_id"),
                "eligible": e.get("timing_eligible", 1),
            })
    return {"exists": True, "lines": n, "event_counts": events,
            "run_end": run_end, "inject": inject,
            "candidates": candidates}


def control_context(ctx_key, attempts=2, jobs=1):
    w = workload_index()[ctx_key]
    case = {
        "ControlID": f"CTRL-{ctx_key}", "ContextKey": ctx_key,
        "ModelID": w["model"], "ContextID": w["context"],
    }
    metas = []
    for i in range(attempts):
        m = run_gem5(case, "CONTROL", False, w["selector_mode"], 0, 0,
                     "controls", case["ControlID"])
        metas.append(m)
    return metas


def controls(args):
    keys = args.context or [f"{m}-{c}" for m in oracle.MODELS
                            for c in oracle.CONTEXTS]
    if args.jobs <= 1:
        results = [control_context(k) for k in keys]
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            results = list(ex.map(control_context, keys))
    rows = []
    for key, metas in zip(keys, results):
        m0 = metas[0]
        tr = m0["trace_summary"]
        end = tr.get("run_end") or {}
        n = end.get("eligible_events", 0)
        cands0 = [c["seq"] for c in tr.get("candidates", [])
                  if c.get("eligible", 1)]
        cands1 = [c["seq"] for c in metas[1]["trace_summary"].get(
            "candidates", []) if c.get("eligible", 1)]
        repeat = cands0 == cands1
        ords = {}
        if n >= 20:
            for t, p in oracle.PERCENTILES.items():
                ords[t] = math.ceil(n * p)
            distinct = len(set(ords.values())) == 3 and \
                all(1 <= v <= n for v in ords.values())
            if not distinct:
                n = -abs(n)
        rows.append({
            "ControlID": m0["case"]["ControlID"], "ContextKey": key,
            "MeasuredEligibleN": n, "T01_Ordinal": ords.get("T01"),
            "T02_Ordinal": ords.get("T02"), "T03_Ordinal": ords.get("T03"),
            "RepeatCensus_PASS": repeat, "CandidateSeqs": cands0,
            "ContextPredicate_PASS": bool(
                n >= 20 and (m0["case"]["ContextID"] != "C05" or
                             end.get("context_reject_events", 0) == 0)),
            "GuestSlots": len(m0["guest_output"]["slots"]),
            "AllSlotsGolden": all(
                (f"0x{raw:016X}", f"0x{aux:016X}") ==
                (w["final_golden_hex"], w["aux_golden_hex"])
                for raw, aux in m0["guest_output"]["slots"]
                for w in [workload_index()[key]]),
            "attempt_dirs": [
                os.path.join(RESULTS, "controls", m0["case"]["ControlID"],
                             f"attempt-{m['attempt']:04d}") for m in metas],
        })
    path = os.path.join(RESULTS, "audit", "controls.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    write_json(os.path.join(RESULTS, "audit", "controls.json"), rows)
    ok = sum(1 for r in rows if r["MeasuredEligibleN"] >= 20 and
             r["T01_Ordinal"] and r["RepeatCensus_PASS"])
    print(f"CONTROL completed {len(rows)} / N>=20 {ok}")
    for r in rows:
        print(r["ControlID"], "N=", r["MeasuredEligibleN"],
              r["T01_Ordinal"], r["T02_Ordinal"], r["T03_Ordinal"],
              "repeat", r["RepeatCensus_PASS"], "gold", r["AllSlotsGolden"])


def ordinal_for(control_id, timing):
    path = os.path.join(RESULTS, "audit", "controls.json")
    for r in load_json(path):
        if r["ControlID"] == control_id:
            return r["MeasuredEligibleN"], r.get(f"{timing}_Ordinal")
    raise SystemExit("run controls first: " + control_id)


def fault_case(case_id, jobs_unused=None):
    cm = {r["CaseID"]: r for r in case_matrix()}
    case = cm[case_id]
    n, k = ordinal_for(case["ControlID"], case["TimingID"])
    if not n or n < 20 or not k:
        raise SystemExit(f"{case_id}: control gate not ready N={n} K={k}")
    w = workload_index()[case["ContextKey"]]
    meta = run_gem5(case, "FAULT", True, w["selector_mode"], k, n,
                    "runs", case_id)
    return meta


def fault(args):
    ids = args.case or [r["CaseID"] for r in case_matrix()]
    if args.jobs <= 1:
        metas = [fault_case(c) for c in ids]
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(fault_case, c): c for c in ids}
            metas = [f.result() for f in as_completed(futs)]
    bad = []
    for m in metas:
        tr = m["trace_summary"]
        inj = tr.get("inject")
        end = tr.get("run_end") or {}
        ok = (m["returncode"] == 0 and not m["timed_out"] and inj and
              inj.get("applied") == 1 and
              end.get("timing_satisfied") == 1 and
              end.get("timing_selected_ordinal") ==
              (m["select_ordinal"] or -1))
        if not ok:
            bad.append({"case": m["case"]["CaseID"],
                        "attempt": m["attempt"], "rc": m["returncode"],
                        "inject": bool(inj),
                        "selected": end.get("timing_selected_ordinal"),
                        "target": m["select_ordinal"]})
    print(f"FAULT completed {len(metas)}; gate-fail {len(bad)}")
    for b in bad:
        print(" GATE_FAIL", b)
    write_json(os.path.join(RESULTS, "audit", "fault_gate.json"), bad)


def pilot(args):
    out = []
    for m in (args.model or oracle.MODELS):
        key = f"{m}-C01"
        case = {"CaseID": f"PILOT-{m}-C01-T02", "ContextKey": key,
                "ModelID": m, "ContextID": "C01", "TimingID": "T02",
                "ControlID": f"CTRL-{key}"}
        try:
            n, k = ordinal_for(case["ControlID"], "T02")
        except SystemExit:
            n, k = 0, 0
        if k:
            out.append(run_gem5(case, "PILOT_FAULT", True,
                                workload_index()[key]["selector_mode"], k, n,
                                "pilots", case["CaseID"]))
        # zero-apply negative control: valid selector, FaultEnabled=NO
        neg = dict(case)
        neg["CaseID"] = f"NEGCTRL-{m}-C01-T02"
        out.append(run_gem5(neg, "PILOT_NEGATIVE", False,
                            workload_index()[key]["selector_mode"], k or 1,
                            n or 1, "pilots", neg["CaseID"]))
        # C05 state pilot
        c5 = f"{m}-C05"
        case5 = {"CaseID": f"PILOT-{m}-C05-T02", "ContextKey": c5,
                 "ModelID": m, "ContextID": "C05", "TimingID": "T02",
                 "ControlID": f"CTRL-{c5}"}
        try:
            n5, k5 = ordinal_for(case5["ControlID"], "T02")
        except SystemExit:
            n5, k5 = 0, 0
        if k5:
            out.append(run_gem5(case5, "PILOT_FAULT", True,
                                "C05_ORDINAL", k5, n5, "pilots",
                                case5["CaseID"]))
    write_json(os.path.join(RESULTS, "audit", "pilot_index.json"),
               [{"label": m["label"], "attempt": m["attempt"],
                 "rc": m["returncode"], "inject": bool(
                     m["trace_summary"].get("inject")),
                 "applied": (m["trace_summary"].get("inject") or {}
                             ).get("applied"),
                 "timing_satisfied": (m["trace_summary"].get(
                     "run_end") or {}).get("timing_satisfied")}
                for m in out])
    print(f"PILOT completed {len(out)} runs")


def audit(args):
    import analyze
    analyze.main(args)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--jobs", type=int, default=8)
    p.set_defaults(func=plan)
    p = sub.add_parser("control")
    p.add_argument("--context", nargs="*")
    p.add_argument("--jobs", type=int, default=8)
    p.set_defaults(func=controls)
    p = sub.add_parser("pilot")
    p.add_argument("--model", nargs="*")
    p.set_defaults(func=pilot)
    p = sub.add_parser("fault")
    p.add_argument("--case", nargs="*")
    p.add_argument("--jobs", type=int, default=8)
    p.set_defaults(func=fault)
    p = sub.add_parser("audit")
    p.add_argument("--jobs", type=int, default=1)
    p.set_defaults(func=audit)
    args = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
