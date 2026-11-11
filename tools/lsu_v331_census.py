#!/usr/bin/env python3
"""LSU v3.3.1 eligible-event census (audit-only, never graded).

Runs one `platform/run_pilot.py` census probe per requested ordinal with the
model's own selection machinery, then extracts the selected event identity
(dyn_inst_seq, PC, address, entry ids) from the model log / trace.

Census probes are artifacts: oracle outcomes are ignored, nothing is written
under pilots_* or the Excel, and no formal identity is consumed.

Usage:
  python3 tools/lsu_v331_census.py --model A01 --seed 2108120075 \
      --ordinals 1,100,1040 --tag A01_w1

Outputs:
  audit_v3_3_1/roi/census/<tag>.jsonl          one row per probe
  audit_v3_3_1/roi/census/<tag>/K<K>/*.log     small raw logs (no trace/stats)
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATFORM = os.path.join(ROOT, "docs/gem5-fi/lsu/implementation_v3_2/platform")
RUN_PILOT = os.path.join(PLATFORM, "run_pilot.py")
GEM5 = os.path.join(ROOT, "build/ARM/gem5.opt")
WORKLOAD_DIR = os.path.join(ROOT, "docs/gem5-fi/lsu/implementation_v3_2/workloads")
CENSUS_DIR = os.path.join(ROOT, "audit_v3_3_1/roi/census")

DEFAULT_WORKLOAD = {
    "A01": "agu_addrmodes",
    "A03": "agu_addrmodes",
    "LQ04": "lq_lifetime_ordinal",
    "SQ01": "sq_drain",
    "SQ03": "sq_drain",
    "SP05": "store_path",
    "FW02": "sq_forward",
    "FW05": "fw05_forward",
    "MD04": "replay_dependency",
    "DA04": "alignment",
    "LP01": "load_response",
}

MODEL_LOG_HINTS = {
    "A01": ["addrpath_injections.log"],
    "A03": ["addrpath_injections.log"],
    "LQ04": ["lq04_injections.log"],
    "FW02": ["lsq_fwd_injections.log"],
    "FW05": ["lsq_fwd_injections.log"],
    "SQ01": ["lsq_fwd_injections.log"],
    "SQ03": ["lsq_fwd_injections.log"],
    "SP05": ["lsq_fwd_injections.log"],
    "MD04": ["lsq_fwd_injections.log", "md04_injections.log"],
    "DA04": ["lsq_fwd_injections.log"],
    "LP01": ["l1d_fwd_injections.log"],
}

NUM = re.compile(r"(?i)(pc|dyn_inst_seq|seq|store_seq|load_seq|addr|address|vaddr|"
                 r"store_addr|load_addr|actual_ea|golden_ea|request_va|sq_idx|"
                 r"sq_entry_id|lq_idx|lq_entry_id|gen|entry_generation|"
                 r"eligible_ordinal|event_ordinal|ordinal|byte0_after|"
                 r"store_data_hex|new_be|old_be|size|access_size)"
                 r"\s*[=:]\s*(0x[0-9a-fA-F]+|[0-9a-fA-F]+|-?\d+)")


def kv_pairs(text):
    out = {}
    for m in NUM.finditer(text or ""):
        k, v = m.group(1).lower(), m.group(2)
        if k not in out:
            out[k] = v
    return out


HEX_FIELDS = {
    "pc", "addr", "address", "vaddr", "store_addr", "load_addr",
    "actual_ea", "golden_ea", "request_va", "old_addr", "new_addr", "va", "pa",
}
DEC_FIELDS = {
    "dyn_inst_seq", "seq", "store_seq", "load_seq", "sq_idx", "sq_entry_id",
    "lq_idx", "lq_entry_id", "gen", "entry_generation", "eligible_ordinal",
    "event_ordinal", "ordinal", "size", "access_size",
}


def parse_int(v, field=None):
    """gem5 CHAOS logs print PCs/addresses as bare hex (e.g. pc=400558)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    try:
        if field in HEX_FIELDS and not s.lower().startswith("0x"):
            if re.fullmatch(r"[0-9a-fA-F]+", s) and (len(s) >= 5 or re.search(r"[a-fA-F]", s)):
                return int(s, 16)
        if field in DEC_FIELDS and not s.lower().startswith("0x"):
            return int(s, 10)
        return int(s, 0)
    except (TypeError, ValueError):
        return None


def first_jsonl_event(path, wanted):
    if not os.path.exists(path):
        return None
    with open(path, "r", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("event_type") in wanted:
                return d
    return None


def parse_probe(model, ordinal, outdir):
    row = {"model": model, "ordinal": ordinal, "outdir": outdir,
           "exit_code": None, "injection_count": None, "pc": None,
           "seq": None, "addr": None, "eligible": None, "attempted": None,
           "detail": None, "hit_evidence": None}
    meta_path = os.path.join(outdir, "pilot_meta.json")
    if os.path.exists(meta_path):
        try:
            meta = json.load(open(meta_path))
        except Exception:
            meta = {}
        row["exit_code"] = meta.get("exit_code")
        row["injection_count"] = meta.get("injection_count")
        inj = meta.get("injection") or {}
        row["attempted"] = inj.get("attempted")
        row["eligible"] = inj.get("eligible")
        row["elapsed_seconds"] = meta.get("elapsed_seconds")
        row["sample_run_id"] = meta.get("excel_identity", {}).get("sample_run_id")
        row["event_ordinal_used"] = meta.get("excel_identity", {}).get("event_ordinal_used")

    # 1. the tool's own trace: first injection event carries the richest detail
    ev = first_jsonl_event(os.path.join(outdir, "trace_v31.jsonl"),
                           {"injection"})
    if ev:
        row["detail"] = ev.get("detail")
        row["seq"] = parse_int(ev.get("dyn_inst_seq"), "dyn_inst_seq")
        row["addr"] = (parse_int(ev.get("va"), "addr")
                       if ev.get("va") is not None else None)
        kv = kv_pairs(ev.get("detail"))
        for k in ("pc", "dyn_inst_seq", "seq", "store_seq", "load_seq",
                  "addr", "vaddr", "store_addr", "load_addr", "sq_idx",
                  "sq_entry_id", "lq_idx", "lq_entry_id", "eligible_ordinal"):
            if row.get(k if k != "dyn_inst_seq" else "seq") is None and k in kv:
                row[k if k != "dyn_inst_seq" else "seq"] = parse_int(kv[k], k)
        if row["pc"] is None and "pc" in kv:
            row["pc"] = parse_int(kv["pc"], "pc")
        if row["addr"] is None and "addr" in kv:
            row["addr"] = parse_int(kv["addr"], "addr")

    # 2. model log lines (may carry pc when the trace detail does not)
    for name in MODEL_LOG_HINTS.get(model, []):
        p = os.path.join(outdir, name)
        if not os.path.exists(p):
            continue
        for line in open(p, errors="replace"):
            if not line.strip() or "SUMMARY" in line or "FUNNEL" in line:
                continue
            if "A03_ACTIVATION" in line or "RESTORE" in line or "STATUS" in line:
                continue
            kv = kv_pairs(line)
            if not kv or ("seq" not in kv and "dyn_inst_seq" not in kv
                          and "store_seq" not in kv and "load_seq" not in kv):
                continue
            m = re.search(r"(?:reason|affected)=([^;\\s]+)", line)
            if m:
                row["reason"] = m.group(1)
                m2 = re.search(r"reason=([^;\\s]+)", line)
                if m2:
                    row["reason"] = m2.group(1)
            if row["pc"] is None and "pc" in kv:
                row["pc"] = parse_int(kv["pc"], "pc")
            if row["seq"] is None and "dyn_inst_seq" in kv:
                row["seq"] = parse_int(kv["dyn_inst_seq"], "dyn_inst_seq")
            if row["seq"] is None and "seq" in kv:
                row["seq"] = parse_int(kv["seq"], "seq")
            if row["seq"] is None and "store_seq" in kv:
                row["seq"] = parse_int(kv["store_seq"], "store_seq")
            if row["seq"] is None and "load_seq" in kv:
                row["seq"] = parse_int(kv["load_seq"], "load_seq")
            if row["addr"] is None and "addr" in kv:
                row["addr"] = parse_int(kv["addr"], "addr")
            if row["addr"] is None and "store_addr" in kv:
                row["addr"] = parse_int(kv["store_addr"], "store_addr")
            if row["addr"] is None and "load_addr" in kv:
                row["addr"] = parse_int(kv["load_addr"], "load_addr")
            row["hit_evidence"] = (row["hit_evidence"] or "") + line.strip()[:400] + "\n"
            break

    # 3. funnel totals
    for name in ("stdout.log",) + tuple(MODEL_LOG_HINTS.get(model, [])):
        p = os.path.join(outdir, name)
        if not os.path.exists(p):
            continue
        for line in open(p, errors="replace"):
            if "eligible=" in line and row["eligible"] is None:
                m = re.search(r"eligible=(\d+)", line)
                if m:
                    row["eligible"] = int(m.group(1))
            if "attempted=" in line and row["attempted"] is None:
                m = re.search(r"attempted=(\d+)", line)
                if m:
                    row["attempted"] = int(m.group(1))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True,
                    choices=sorted(DEFAULT_WORKLOAD) + ["RP01"])
    ap.add_argument("--ordinals", required=True,
                    help="comma-separated eligible ordinals")
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--workload", default=None,
                    help="workload name or absolute path (default per model)")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--scratch", default="/home/sdc/.cache/v331_census")
    args = ap.parse_args()

    if args.model == "RP01":
        sys.exit("RP01 has no run_pilot path; use the v3.2.12 count-only preflight")

    wl = args.workload or DEFAULT_WORKLOAD[args.model]
    wl_path = wl if os.path.isabs(wl) else os.path.join(WORKLOAD_DIR, wl)
    if not os.path.exists(wl_path):
        sys.exit("workload not found: %s" % wl_path)

    os.makedirs(CENSUS_DIR, exist_ok=True)
    keep_root = os.path.join(CENSUS_DIR, args.tag)
    os.makedirs(keep_root, exist_ok=True)
    out_jsonl = os.path.join(CENSUS_DIR, args.tag + ".jsonl")
    rows = []
    with open(out_jsonl, "a") as jf:
        for tok in args.ordinals.split(","):
            k = int(tok)
            outdir = os.path.join(args.scratch, "%s_%s_K%d" % (args.tag, args.model, k))
            shutil.rmtree(outdir, ignore_errors=True)
            cmd = [sys.executable, RUN_PILOT,
                   "--model", args.model,
                   "--pilot-id", "PROBE-%s-%s-K%d" % (args.tag, args.model, k),
                   "--event-ordinal", str(k),
                   "--seed", str(args.seed),
                   "--context-index", "1",
                   "--outdir", outdir,
                   "--gem5", GEM5,
                   "--timeout", str(args.timeout),
                   "--workload", wl_path]
            timed_out = False
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    start_new_session=True)
            try:
                proc.wait(timeout=args.timeout + 30)
            except subprocess.TimeoutExpired:
                # census probes may hang after activation (F5); kill the whole
                # probe session and keep the partial record written before it.
                timed_out = True
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            row = parse_probe(args.model, k, outdir)
            row["timed_out"] = timed_out
            row["workload"] = wl_path
            row["census_tag"] = args.tag
            rows.append(row)
            jf.write(json.dumps(row) + "\n")
            jf.flush()
            # persist small raw artifacts (never the multi-MB trace/stats)
            keep = os.path.join(keep_root, "K%d" % k)
            os.makedirs(keep, exist_ok=True)
            for name in os.listdir(outdir) if os.path.isdir(outdir) else []:
                if name.endswith(".log") or name in ("pilot_meta.json", "command.txt", "config.ini"):
                    shutil.copy2(os.path.join(outdir, name), os.path.join(keep, name))
            # never keep the multi-MB trace/stats/prop artifacts: the parsed
            # JSON row + small logs are the durable census record.
            shutil.rmtree(outdir, ignore_errors=True)
            pc = "0x%x" % row["pc"] if isinstance(row["pc"], int) else row["pc"]
            print("K=%-5s rc=%s inj=%s pc=%-10s seq=%-7s addr=%s" % (
                k, row["exit_code"], row["injection_count"], pc,
                row["seq"], row["addr"]))
    print("wrote", out_jsonl, "rows", len(rows))


if __name__ == "__main__":
    main()
