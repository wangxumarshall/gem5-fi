#!/usr/bin/env python3
"""logparse.py — openEuler kernel-log parser for the SDC diagnosis engine
(plan §7.2, Task 4.2).

Parses the three openEuler log forms into a uniform event list:
  1. vmcore-dmesg.txt / dmesg    — `[ 104485.842931] ...` uptime-stamped lines
  2. journalctl -k output       — `Aug 14 19:07:04 host kernel: ...` (date-stamped)
  3. /var/log/messages (rsyslog)— `Aug 14 19:07:04 host kernel: ...` (MMM dd HH:MM:SS)

Extracts per anomaly event:
  - kind: WARNING / Oops / panic / spurious-translation-fault / EDAC / SEL...
  - CPU number (`CPU: 179` / `CPU 179` fields)
  - ESR value (via esr_decode) + FAR + WnR/FSC decode
  - pc / lr symbol+offset
  - PID / Comm (process)
  - call-trace top frames
  - timestamp (uptime seconds or syslog datetime)

Aggregation outputs (for §7.4 Step 1/Step 4):
  - per-core counts + concentration (P1: single core > 60%)
  - per-instruction (pc symbol) recurrence (5/6 same-instruction signature)
  - distinct processes (P2: >= 2 apps on the same core)

Usage:
  python3 logparse.py <vmcore-dmesg.txt|dmesg.txt|messages> [--json]
  python3 logparse.py <dir>          # all vmcore-dmesg.txt under a dir
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esr_decode import decode as decode_esr  # noqa: E402

# --- line forms ------------------------------------------------------------
# dmesg/vmcore-dmesg: [ 104485.842931] MESSAGE
RE_UPTIME = re.compile(r"^\[\s*(\d+)\.(\d+)\]\s?(.*)$")
# journalctl -k / rsyslog: Aug 14 19:07:04 host kernel: MESSAGE
RE_SYSLOG = re.compile(
    r"^([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+kernel:\s?(.*)$")
# journalctl with monotonic: "Aug 14 19:07:04 host kernel: [104485.842931] msg"
# (handled by stripping the inner uptime after syslog match)

# --- event patterns ---------------------------------------------------------
RE_WARN_CPU = re.compile(r"WARNING: CPU: (\d+)")
RE_OOPS_CPU = re.compile(r"(?:CPU|on CPU)\s*:?\s*(\d+)")
RE_PID_COMM = re.compile(r"PID: (\d+)(?:\s+Comm:\s*(\S+))?")
RE_ESR = re.compile(r"ESR[^\n]{0,20}?0x([0-9a-fA-F]{4,16})", re.IGNORECASE)
RE_FAR = re.compile(r"FAR[^\n]{0,10}?0x([0-9a-fA-F]{8,16})", re.IGNORECASE)
RE_PC = re.compile(r"^pc\s*:\s*(\S+)")
RE_LR = re.compile(r"^lr\s*:\s*(\S+)")
RE_SPURIOUS = re.compile(r"Ignoring spurious kernel translation fault", re.I)
RE_UNABLE = re.compile(r"Unable to handle kernel (paging request|write to read-only)", re.I)
RE_INTERNAL = re.compile(r"Internal error:\s*(.*?)\s*\[", re.I)
RE_EDAC = re.compile(r"\b(EDAC|edac)\b|mce|Machine check", re.I)
RE_SEL_RAS = re.compile(r"rasnode|ghes|HEST|EINJ|ras-mc-ctl", re.I)
RE_REG = re.compile(r"^(x\d+|sp):\s*([0-9a-f]+)", re.M)


def parse(text: str, source: str = ""):
    """Parse one log text into a list of anomaly events."""
    events = []
    cur = None  # pending WARNING/Oops context (registers arrive on next lines)

    def flush():
        nonlocal cur
        if cur:
            events.append(cur)
            cur = None

    lines = text.splitlines()
    for ln in lines:
        # timestamp prefix
        ts = None
        m = RE_UPTIME.match(ln)
        rest = ln
        if m:
            ts = float(f"{m.group(1)}.{m.group(2)}")
            rest = m.group(3)
        else:
            m2 = RE_SYSLOG.match(ln)
            if m2:
                ts = f"{m2.group(1)} {m2.group(2)} {m2.group(3)}"
                rest = m2.group(5)
                m3 = RE_UPTIME.match(rest.strip())
                if m3:  # journalctl keeps the [uptime] inside
                    ts = float(f"{m3.group(1)}.{m3.group(2)}")
                    rest = m3.group(3)

        # event-starting lines
        is_warn = "WARNING:" in rest
        is_oops = ("Oops" in rest or "internal error" in rest.lower()
                   or RE_UNABLE.search(rest) or "Kernel panic" in rest)
        is_spurious = RE_SPURIOUS.search(rest)
        is_edac = RE_EDAC.search(rest) or RE_SEL_RAS.search(rest)

        if is_spurious:
            flush()
            cur = {"kind": "spurious_translation_fault",
                   "ts": ts, "source": source, "raw": rest}
            mc = RE_WARN_CPU.search(rest) or RE_OOPS_CPU.search(rest)
            if mc:
                cur["cpu"] = int(mc.group(1))
            mp = RE_PID_COMM.search(rest)
            if mp:
                cur["pid"] = int(mp.group(1))
                if mp.group(2):
                    cur["comm"] = mp.group(2)
            continue
        if is_warn:
            # A WARNING line DIRECTLY following an 'Ignoring spurious'
            # line is the SAME event (kernel prints spurious first, then
            # the WARNING with the CPU/PID context) — merge, don't split.
            if cur and cur["kind"] == "spurious_translation_fault":
                mc = RE_WARN_CPU.search(rest) or RE_OOPS_CPU.search(rest)
                if mc:
                    cur["cpu"] = int(mc.group(1))
                mp = RE_PID_COMM.search(rest)
                if mp:
                    cur["pid"] = int(mp.group(1))
                    if mp.group(2):
                        cur["comm"] = mp.group(2)
                continue
            flush()
            cur = {"kind": "WARNING", "ts": ts, "source": source, "raw": rest}
            mc = RE_WARN_CPU.search(rest) or RE_OOPS_CPU.search(rest)
            if mc:
                cur["cpu"] = int(mc.group(1))
            mp = RE_PID_COMM.search(rest)
            if mp:
                cur["pid"] = int(mp.group(1))
                if mp.group(2):
                    cur["comm"] = mp.group(2)
            continue
        if is_oops:
            flush()
            cur = {"kind": "Oops", "ts": ts, "source": source, "raw": rest}
            mc = RE_WARN_CPU.search(rest) or RE_OOPS_CPU.search(rest)
            if mc:
                cur["cpu"] = int(mc.group(1))
            mp = RE_PID_COMM.search(rest)
            if mp:
                cur["pid"] = int(mp.group(1))
                if mp.group(2):
                    cur["comm"] = mp.group(2)
            continue
        if is_edac:
            # EDAC/RAS lines are context, not anomalies — record counts once
            events.append({"kind": "edac_ras_line", "ts": ts,
                           "source": source, "raw": rest[:200]})
            continue

        # context lines for the pending event
        if cur is not None:
            me = RE_ESR.search(rest)
            if me:
                cur["esr"] = int(me.group(1), 16)
                cur["esr_decode"] = decode_esr(cur["esr"])
            mf = RE_FAR.search(rest)
            if mf:
                cur["far"] = int(mf.group(1), 16)
            mp = RE_PC.match(rest.strip())
            if mp:
                cur["pc"] = mp.group(1)
            ml = RE_LR.match(rest.strip())
            if ml:
                cur["lr"] = ml.group(1)
            mc = RE_OOPS_CPU.search(rest)      # 'CPU: 179 PID: ...' oops header
            if mc and "cpu" not in cur:
                cur["cpu"] = int(mc.group(1))
            mp2 = RE_PID_COMM.search(rest)
            if mp2:
                cur["pid"] = int(mp2.group(1))
                if mp2.group(2):
                    cur["comm"] = mp2.group(2)
            if rest.startswith("x") or rest.startswith("sp:"):
                cur.setdefault("regs", {}).update(
                    dict(re.findall(r"(x\d+|sp):\s*([0-9a-f]+)", rest)))
            if "Call trace:" in rest:
                cur["in_trace"] = True
                cur.setdefault("trace", [])
                continue
            if cur.get("in_trace") and rest.strip() and not rest.startswith(" "):
                pass  # trace frames are indented under dmesg; keep simple
            if cur.get("in_trace"):
                frame = rest.strip().split()[0] if rest.strip() else ""
                if frame and len(cur["trace"]) < 12:
                    cur["trace"].append(frame)
            if "---[ end trace" in rest or "SMP: stopping" in rest:
                flush()
        # a blank heuristic: a new WARNING header closes the previous event
        if is_warn and cur and cur["kind"] != "WARNING":
            flush()
    flush()
    return events


def aggregate(events):
    """§7.4 Step 1/Step 4 aggregations: per-core concentration (P1),
    per-instruction recurrence, per-core process diversity (P2)."""
    anomalies = [e for e in events if e["kind"] in
                 ("WARNING", "Oops", "spurious_translation_fault")]
    total = len(anomalies)
    per_core = {}
    per_core_comms = {}
    per_pc = {}
    esr_values = {}
    for e in anomalies:
        c = e.get("cpu")
        if c is not None:
            per_core[c] = per_core.get(c, 0) + 1
            per_core_comms.setdefault(c, set()).add(e.get("comm", "?"))
        if "pc" in e:
            per_pc[e["pc"]] = per_pc.get(e["pc"], 0) + 1
        if "esr" in e:
            key = f"0x{e['esr']:x}"
            esr_values[key] = esr_values.get(key, 0) + 1

    conc = 0.0
    top_core, top_count = None, 0
    if total and per_core:
        top_core = max(per_core, key=per_core.get)
        top_count = per_core[top_core]
        conc = top_count / total

    multi_app_on_top = False
    if top_core is not None:
        multi_app_on_top = len(per_core_comms.get(top_core, set())) >= 2

    return {
        "n_anomalies": total,
        "per_core": {str(k): v for k, v in sorted(per_core.items())},
        "top_core": top_core,
        "top_core_count": top_count,
        "concentration": round(conc, 4),
        "P1_concentration_gt60pct": conc > 0.60,
        "P2_multi_app_on_top_core": multi_app_on_top,
        "per_pc_symbol": per_pc,
        "esr_histogram": esr_values,
        "n_edac_ras_lines": sum(1 for e in events
                                if e["kind"] == "edac_ras_line"),
    }


def load_text(path: str):
    with open(path, errors="replace") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="log file, or a directory containing "
                                 "vmcore-dmesg.txt files")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if os.path.isdir(args.path):
        files = sorted(glob.glob(os.path.join(args.path, "*", "vmcore-dmesg.txt"))
                       or glob.glob(os.path.join(args.path, "vmcore-dmesg.txt")))
    else:
        files = [args.path]

    out = {}
    all_events = []
    for fp in files:
        evts = parse(load_text(fp), source=fp)
        out[fp] = aggregate(evts)
        all_events.extend(evts)

    if len(files) > 1:
        out["__combined__"] = aggregate(all_events)

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    else:
        for name, agg in out.items():
            print(f"=== {name} ===")
            print(f"  anomalies={agg['n_anomalies']}  "
                  f"top_core={agg['top_core']} ({agg['top_core_count']}, "
                  f"{agg['concentration']*100:.1f}%)  "
                  f"P1(>60%)={'HIT' if agg['P1_concentration_gt60pct'] else 'miss'}  "
                  f"P2(multi-app)={'HIT' if agg['P2_multi_app_on_top_core'] else 'miss'}")
            print(f"  ESR histogram: {agg['esr_histogram'] or '{}'}")
            top_pc = max(agg["per_pc_symbol"].items(), key=lambda kv: kv[1],
                         default=None)
            if top_pc:
                print(f"  top pc: {top_pc[0]} ×{top_pc[1]}")


if __name__ == "__main__":
    main()
