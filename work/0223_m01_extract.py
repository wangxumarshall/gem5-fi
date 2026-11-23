#!/usr/bin/env python3
"""W5X3 M01 diagnostic evidence extraction.

For each of 15 M01 samples + 5 controls, extract the fault-tagged committed
load chain (load PC/dseq/data_fnv/register -> consumer PC) and the guest
oracle.  Maps data_fnv to Marker A(0xAA)/B(0x55) and disasm PCs to ARM64
instructions.  Output: MMU_FINAL/_work/m01_evidence.json
"""
import gzip, re, json, os, csv

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
O = os.path.join(ROOT, "MMU_FINAL", "_work")
os.makedirs(O, exist_ok=True)

# FNV-1a-64 reference (data_fnv -> byte value)
FNV = {
    "af64274c86026bfd": ("0xAA", "Marker A (old/stale page)"),
    "af64084c86023750": ("0x55", "Marker B (new page)"),
    "217454b2f3049aa5": ("16x0xAA", "NEON vector of Marker A"),
    "d7e54fa625bb2055": ("16x0x55", "NEON vector of Marker B"),
}

# context -> committed load PC(s) + disasm
CTX_LOADS = {
    "C01": [("400eb0", "ldrb w2, [x28]", "v = *p (stale load, x28=&p)")],
    "C02": [("4011d0", "ldr q0, [x28]", "vec = vld1q_u8(p)"),
            ("4011e4", "ldrb w2, [x28]", "v = *p (scalar oracle)")],
    "C03": [("401138", "ldrb w0, [x28]", "dead = *p (discarded)")],
    "C04": [("401108", "ldrb w2, [x28]", "v = *p (first load)"),
            ("401118", "ldrb w0, [x28, x0]", "w = *(p + (v & 0x0F)) (second load)")],
    "C05": [("4010cc", "ldrb w0, [x28]", "v = *p (stale load)")],
}

CONSUMER_DISASM = {
    "400eb8": "and x0, x2, #0xff  (v & 0xff -> worker reg, zero-extend)",
    "400ebc": "and w2, w2, #0xff  (v & 0xff for scalar)",
    "4010d0": "and w2, w0, #0xff",
    "4010d4": "cmp w21, w0, uxtb   (cmp v, expect)",
    "401110": "and x0, x2, #0xf    (v & 0x0F  -> offset)",
    "401118": "ldrb w0, [x28, x0]  (second load at p+offset)",
    "4011d4": "add v0.16b, v0.16b, v1.16b  (vaddq_u8 +1)",
    "4011d8": "umov w0, v0.b[0]   (extract lane 0)",
    "4011e8": "and w2, w2, #0xff",
    "400d80": "ldrb (warm loop sink += p[0])",
}


def parse_line(line):
    return dict(re.findall(r"([a-zA-Z_0-9]+)=([^ ]*)", line))


def load_trace(path):
    evs = []
    with gzip.open(path, "rt", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if not line.startswith("PROP-EVT"):
                continue
            d = parse_line(line)
            d["_line"] = ln
            evs.append(d)
    return evs


def parse_oracle(path):
    out = []
    for line in open(path, errors="replace"):
        if "W9_RESULT" in line:
            d = parse_line(line)
            out.append({"iter": int(d.get("iter", 0)),
                        "observed": d.get("observed", ""),
                        "branch": d.get("branch", ""),
                        "vec0": d.get("vec0", ""),
                        "result": d.get("result", "").strip(),
                        "pa1": d.get("pa1", ""), "pa2": d.get("pa2", ""),
                        "expected": d.get("expected", ""),
                        "old_marker": d.get("old_marker", ""),
                        "new_marker": d.get("new_marker", "")})
    return out


def extract(run, ctx):
    base = os.path.join(ROOT, "runs", "W5X3", run)
    evs = load_trace(base + "/Trace/prop_evt.txt.gz")
    oracle = parse_oracle(base + "/Run_Log/board.terminal")
    # build per-dseq committed load info
    load_pcs = [p for p, _, _ in CTX_LOADS[ctx]]
    loads = {}  # dseq -> dict
    commits = {}  # dseq -> commit/squash status
    for e in evs:
        if e.get("kind") in ("commit", "squash"):
            ds = e.get("dyn_inst_seq")
            commits.setdefault(ds, {"cs": "", "ss": "", "pc": ""})
            commits[ds]["cs"] = e.get("commit_status", "") or commits[ds]["cs"]
            commits[ds]["ss"] = e.get("squash_status", "") or commits[ds]["ss"]
            commits[ds]["pc"] = e.get("pc", "") or commits[ds]["pc"]
        elif e.get("kind") == "translation_result" and e.get("pc"):
            ds = e.get("dyn_inst_seq")
            commits.setdefault(ds, {"cs": "", "ss": "", "pc": ""})
            commits[ds]["pc"] = e.get("pc", "") or commits[ds]["pc"]
            commits[ds]["fault"] = e.get("fault_id", "0")
    # ALL memory_response + rf_writeback (not just fault-tagged); consumer is fault-tagged
    mem = {}
    wb = {}
    consumers = []
    for e in evs:
        if e.get("kind") == "memory_response":
            ds = e.get("dyn_inst_seq")
            mem[ds] = {"fn": e.get("data_fnv", ""), "va": e.get("va", ""),
                       "pa": e.get("pa", ""), "line": e["_line"],
                       "eid": e.get("event_id")}
        elif e.get("kind") == "rf_writeback":
            ds = e.get("dyn_inst_seq")
            wb[ds] = {"reg": e.get("field", ""), "line": e["_line"],
                      "eid": e.get("event_id")}
        elif e.get("kind") == "consumer" and e.get("fault_id") == "1":
            consumers.append({"dseq": e.get("dyn_inst_seq"),
                              "pc": e.get("pc", ""),
                              "producer": e.get("field", "").replace("consumer_of=", ""),
                              "cs": e.get("commit_status", ""),
                              "line": e["_line"], "eid": e.get("event_id")})
    # fault arm / suppress
    arm = [e for e in evs if e.get("kind") == "mmu_fault_arm" and e.get("fault_id") == "1"]
    supp = [e for e in evs if e.get("kind") == "tlbi_suppressed" and e.get("fault_id") == "1"]
    disarm = [e for e in evs if e.get("kind") == "mmu_fault_disarm" and e.get("fault_id") == "1"]

    result = {"run": run, "ctx": ctx, "oracle": oracle,
              "arm_eid": arm[0]["event_id"] if arm else None,
              "suppress_eids": [e["event_id"] for e in supp],
              "disarm_eids": [e["event_id"] for e in disarm],
              "loads": [], "consumers": []}
    # committed loads at context PCs (all iterations)
    for pc, dis, desc in CTX_LOADS[ctx]:
        for ds, c in commits.items():
            if c["pc"] == pc and c["cs"] == "committed":
                m = mem.get(ds, {})
                fn = m.get("fn", "")
                entry = {
                    "pc": pc, "dseq": int(ds), "disasm": dis, "desc": desc,
                    "data_fnv": fn, "data": FNV.get(fn, (fn, "")),
                    "va": m.get("va", ""), "pa": m.get("pa", ""),
                    "reg": wb.get(ds, {}).get("reg", ""),
                    "mem_eid": m.get("eid", ""), "mem_line": m.get("line", ""),
                    "wb_eid": wb.get(ds, {}).get("eid", ""),
                    "wb_line": wb.get(ds, {}).get("line", ""),
                    "commit_status": c["cs"]}
                result["loads"].append(entry)
    # consumers whose producer matches a context load
    producer_seqs = set(str(l["dseq"]) for l in result["loads"])
    for c in consumers:
        if c["producer"] in producer_seqs:
            result["consumers"].append(c)
    return result


def main():
    samples = [f"M01-F0-W9-W5X3-{c}-{t}"
               for c in ("C01", "C02", "C03", "C04", "C05")
               for t in ("T01", "T02", "T03")]
    controls = ["CTRL-M01-C01", "CTRL-M01-C02", "CTRL-M01-C03",
                "CTRL-M01-C04", "CTRL-M01-C05"]
    out = {"samples": {}, "controls": {}}
    for s in samples:
        ctx = "C" + s.split("-C")[1][:2]
        out["samples"][s] = extract(s, ctx)
    for c in controls:
        ctx = "C" + c.split("-C")[1]
        out["controls"][c] = extract(c, ctx)
    with open(os.path.join(O, "m01_evidence.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    # quick stdout summary
    for s, v in sorted(out["samples"].items()):
        obs = v["oracle"]
        fail = [o for o in obs if o["result"] == "FAIL"]
        loadc = "; ".join(f"{l['pc']}:{l['data'][0]}" for l in v["loads"])
        cons = "; ".join(f"{c['pc']}<-{c['producer'].split('=')[-1]}" for c in v["consumers"])
        print(f"{s} loads=[{loadc}] consumers=[{cons}] FAIL_iters={[o['iter'] for o in fail]}")
    print("controls:")
    for c, v in sorted(out["controls"].items()):
        loadc = "; ".join(f"{l['pc']}:{l['data'][0]}" for l in v["loads"])
        print(f"  {c} loads=[{loadc}]")

if __name__ == "__main__":
    main()