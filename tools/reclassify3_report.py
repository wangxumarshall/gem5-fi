#!/usr/bin/env python3
"""Three-class report generator: reads reclass3_cells.json + H7 formal results,
computes C1/C2/C3(3a/3b/3c) + validity/artifact rates per cell, flags Crash>=10%
cells for secondary verification, emits the markdown table."""
import json, os, re

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
rows = json.load(open(os.path.join(REPO, "artifacts/meta/reclass3_cells.json")))

# ---- import H7 formal (shell-script run; provenance = artifacts/p20_h7_formal/results.txt) ----
h7 = []
for line in open(os.path.join(REPO, "artifacts/p20_h7_formal/results.txt")):
    m = re.match(r"(true|false) seed=(\d+) rc=(\d+) panic=(\d+) applied=(\d+)", line.strip())
    if not m: continue
    ecc, seed, rc, panic, applied = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
    if ecc == "false":
        if applied == 0:  cls = "Inactive"
        elif panic > 0 or rc == 134: cls = "Crash"
        else: cls = "Masked"   # censored-window survivor (no panic in 360s)
    else:
        if applied == 0: cls = "Corrected"   # ECC-caught (the ptwEcc revert)
        else: cls = "Masked"
    h7.append(dict(ecc=ecc, seed=seed, cls=cls))
# aggregate H7 into 2 pseudo-cells
for ecc, label in (("false", "two_bit_corrupt+ECC-off"), ("true", "two_bit_corrupt+ECC-on")):
    sub = [h for h in h7 if h["ecc"] == ecc]
    counts = {}
    for h in sub: counts[h["cls"]] = counts.get(h["cls"], 0) + 1
    rows.append(dict(campaign="p20_h7_formal(shell)", cell=f"ecc_{ecc}", unit="ptw",
                     model="two_bit_corrupt", axes="kernel_walk_only", workload="FS-kernel-boot",
                     prot=("secded+logic-fault-sim" if ecc=="false" else "ptwEcc"),
                     plat="C0-FS", n_total=len(sub),
                     Masked=counts.get("Masked",0), SDC=0, Crash=counts.get("Crash",0),
                     Hang=0, Inactive=counts.get("Inactive",0), SimulatorError=0,
                     Corrected=counts.get("Corrected",0), DetectedContained=0,
                     provenance="artifacts/p20_h7_formal/results.txt"))

# ---- three-class metrics ----
def wilson(k, n, z=1.96):
    if n == 0: return ("—", "—")
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*((p*(1-p)/n + z*z/(4*n*n))**0.5)/d
    return (f"{p*100:.1f}", f"[{(c-h)*100:.1f},{(c+h)*100:.1f}]")

out_rows = []
for r in rows:
    n = r["n_total"]; nv = n - r["Inactive"] - r["SimulatorError"]
    nvw = n - r["Inactive"]  # validity denominator
    validity = nv/nvw if nvw else None
    c1 = r["Masked"]
    c2 = r["Corrected"] + r["DetectedContained"]
    c3a, c3b, c3c = r["SDC"], r["Crash"], r["Hang"]
    def pct(k): return f"{k/nv*100:.1f}" if nv else "—"
    out_rows.append(dict(**r, N_valid=nv,
        C1=pct(c1), C2=pct(c2), C3=pct(c3a+c3b+c3c),
        C3a=pct(c3a), C3b=pct(c3b), C3c=pct(c3c),
        validity=f"{validity*100:.1f}" if validity is not None else "—",
        crash_share=c3b/nv if nv else 0,
        needs_verify=(nv >= 30 and c3b/nv >= 0.10)))

json.dump(out_rows, open(os.path.join(REPO, "artifacts/meta/reclass3_metrics.json"), "w"),
          indent=1, ensure_ascii=False)

# ---- units needing verification (Crash>=10%, group by unit) ----
need = {}
for r in out_rows:
    if r["needs_verify"]:
        need.setdefault(r["unit"], []).append((r["campaign"], r["cell"], r["C3b"], r["N_valid"]))
print("cells:", len(out_rows), " total reps:", sum(r["n_total"] for r in out_rows))
print("Crash>=10% cells by unit (need secondary verification):")
for u in sorted(need, key=lambda u: -len(need[u])):
    print(f"  {u}: {len(need[u])} cells — e.g. {need[u][:3]}")
