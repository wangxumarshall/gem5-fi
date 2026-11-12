#!/usr/bin/env python3
"""Build phase3/formal/evidence_index.json from real pilot run artifacts.

This is the bridge between a TEST-ID pilot and the 40-sample formal preflight:
the preflight never infers runtime status from static file existence.  It reads
this index, and every field here is derived from a real run directory:

  * runtime_pilot              - the run directory has a trace + terminal
  * fault_activation           - validator ActivationStatus
  * fault_consumption          - validator FaultConsumptionStatus
  * propagation                - validator PropagationStatus
  * terminal_oracle            - validator TerminalState / OracleResult
  * observed_output            - the faulted run's own terminal observation

Input manifest (JSON):
  {
    "M03/R01": {"run_id": "TEST-M03-R01"},
    ...
  }
A missing entry stays absent in the index (preflight reports NOT_RUN).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_formal_validate as validator


def _read_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _verdict(run_dir):
    v = os.path.join(run_dir, "Validation", "verdict.json")
    return _read_json(v)


def _revalidate(run_dir, model, context, out_dir):
    """Recompute a verdict from the real trace WITHOUT touching the run dir.

    The result is written under phase3/formal/revalidated/ so historical run
    artefacts stay immutable.  No gem5 process is launched.
    """
    paths = validator.find_run_paths(run_dir)
    if not paths.get("trace"):
        return {}
    events, bad, err = validator.load_events_tolerant(paths["trace"])
    by_id = {e["event_id"]: e for e in events}
    manifest = validator.load_manifest(paths.get("manifest"))
    target_va = manifest.get("target_va")
    if isinstance(target_va, str) and target_va:
        target_va = int(target_va, 0)
    result = validator.evaluate_run(
        events, by_id, bad, model, manifest.get("workload", ""), context,
        target_va, manifest.get("target_mode", ""),
        manifest.get("run_id", os.path.basename(run_dir)),
        paths.get("golden"), paths.get("terminal"), manifest,
        trace_error=err, control_run=manifest.get("control_run") or None)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "%s.json" % os.path.basename(run_dir))
    with open(dst, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, default=str)
    return result


def _find_trace(run_dir):
    for rel in ("Trace/prop_evt.txt.gz", "run/prop_evt.txt.gz",
                "prop_evt.txt.gz"):
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            return p
    return None


def _find_observed(run_dir):
    for rel in ("Run_Log/observed_output.txt", "Run_Log/golden_output.txt",
                "observed_output.txt", "golden_output.txt"):
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            return p
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--manifest", default=None,
                    help="JSON mapping 'M03/R01' -> {run_id}")
    ap.add_argument("--out", default=None)
    ap.add_argument("--revalidate", action="store_true",
                    help="recompute every verdict from the real trace and "
                         "store it under phase3/formal/revalidated/ (the run "
                         "directory is never modified)")
    ap.add_argument("--reval-dir", default=None)
    args = ap.parse_args(argv)

    root = os.path.abspath(args.repo_root)
    manifest_path = args.manifest or os.path.join(
        root, "phase3", "formal", "pilot_runs.json")
    out_path = args.out or os.path.join(
        root, "phase3", "formal", "evidence_index.json")
    manifest = _read_json(manifest_path)

    index = {"generated_from": manifest_path, "runs_root": os.path.join(
        root, "runs"), "contexts": {}}
    missing_runs = []
    for key, rec in sorted(manifest.items()):
        run_id = rec.get("run_id") if isinstance(rec, dict) else rec
        if not run_id:
            continue
        run_dir = os.path.join(root, "runs", run_id)
        trace = _find_trace(run_dir)
        observed = _find_observed(run_dir)
        if not os.path.isdir(run_dir):
            missing_runs.append({"key": key, "run_id": run_id,
                                 "reason": "run directory missing"})
            continue
        verdict = _verdict(run_dir)
        if args.revalidate:
            model, ctx = key.split("/", 1)
            reval_dir = args.reval_dir or os.path.join(
                root, "phase3", "formal", "revalidated")
            fresh = _revalidate(run_dir, model, ctx, reval_dir)
            if fresh:
                verdict = fresh
        if not verdict:
            # Produce the verdict from the real trace if the runner did not.
            model, ctx = key.split("/", 1)
            report = os.path.join(run_dir, "Validation", "verdict.json")
            os.makedirs(os.path.dirname(report), exist_ok=True)
            try:
                validator.main([
                    "--run-dir", run_dir, "--model", model,
                    "--context", ctx, "--report-json", report,
                    "--control-run", rec.get("control_run", ""),
                ])
                verdict = _read_json(report)
            except SystemExit:
                verdict = _read_json(report)
        terminal = verdict.get("TerminalState", "NOT_OBSERVED")
        oracle = verdict.get("OracleResult", "NOT_OBSERVED")
        manifest_path = os.path.join(run_dir, "sample_manifest.json")
        manifest = _read_json(manifest_path)
        index["contexts"][key] = {
            "run_id": run_id,
            "run_dir": run_dir,
            "manifest": manifest_path if os.path.isfile(manifest_path)
            else "",
            "manifest_present": os.path.isfile(manifest_path),
            "gem5_sha256": manifest.get("gem5_sha256", ""),
            "source_commit": manifest.get("git_head", ""),
            "workload_sha256": manifest.get("workload_sha256", ""),
            "control_oracle_sha256": manifest.get(
                "control_oracle_sha256", ""),
            "trace": trace,
            "observed_output": observed,
            "runtime_pilot": "PASS" if (trace and
                                        os.path.isfile(os.path.join(
                                            run_dir, "Run_Log",
                                            "gem5_exit_code.txt")))
            else "NOT_RUN",
            "fault_activation": verdict.get("ActivationStatus", "NOT_RUN"),
            "fault_consumption": verdict.get("FaultConsumptionStatus",
                                             "NOT_RUN"),
            "propagation": verdict.get("PropagationStatus", "NOT_RUN"),
            "terminal_oracle": "%s/%s" % (terminal, oracle),
            "terminal_state": terminal,
            "oracle_result": oracle,
            "trace_completeness": verdict.get("TraceCompleteness",
                                              "NOT_RUN"),
            "control_oracle": (verdict.get("Details", {}) or {}).get(
                "control_oracle", {}),
        }

    index["missing_runs"] = missing_runs
    with open(out_path, "w") as fh:
        json.dump(index, fh, indent=2, sort_keys=True, default=str)
    print(json.dumps({
        "out": out_path,
        "contexts": len(index["contexts"]),
        "missing_runs": len(missing_runs),
        "keys": sorted(index["contexts"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
