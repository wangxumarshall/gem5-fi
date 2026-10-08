#!/usr/bin/env python3
"""U10 TDD: ooo_observe L0-L5 composer + classify conservation (P1 plan).

P1 plan Task U10 Step 1 fixtures (4 required + 2 bonus, all honest extras
labeled):
  F1 clean    : no injector logs, FINAL==golden, exit.rc=0
                -> verdict=Inactive, conservation ok
  F2 masked   : CHAOS_L0_FUNNEL activated=1, FINAL==golden, exit.rc=0
                -> verdict=Masked, conservation ok
  F3 sdc      : CHAOS_L0_FUNNEL activated=1, FINAL!=golden, exit.rc=0
                -> verdict=SDC, conservation ok
  F4 violated : funnel attempted=5 eligible=7 injected=3 activated=2
                -> conservation_ok=False, violation names injector+relation
  T5 (bonus)  : abort legitimacy (chaos_l0.hh: abort paths run no exit
                callbacks): simerr panic, rc=134, NO log lines
                -> verdict=SimulatorError, L0 absent is NOT a violation
  T6 (bonus)  : determinism cross-check: funnel activated=0 injected=1,
                FINAL!=golden, rc=0 -> verdict=Inactive (fixed classify
                order) BUT conservation flags checksum!=golden

Standalone (no pytest), mirrors tools/tests/test_ooo_guard_f025.py style.
"""
import shutil
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

GOLDEN = "45737cc9a76c0dce"
OTHER = "deadbeefdeadbeef"


def _mk_outdir(root, name, simout="", simerr="", rc=None, logs=None):
    d = Path(root) / name
    d.mkdir(parents=True)
    if simout:
        (d / "simout").write_text(simout)
    if simerr:
        (d / "simerr").write_text(simerr)
    if rc is not None:
        (d / "exit.rc").write_text("%d\n" % rc)
    for logname, lines in (logs or {}).items():
        (d / logname).write_text("\n".join(lines) + "\n")
    return d


def main():
    checks = []

    def ck(name, cond, detail=""):
        checks.append((name, bool(cond), str(detail)))
        print(("PASS" if cond else "FAIL"), name, ("| " + str(detail)) if detail else "")

    import ooo_observe as O

    root = tempfile.mkdtemp(prefix="ooo-u10-")
    try:
        # ---- F1 clean: no injector logs at all
        f1 = _mk_outdir(root, "f1-clean",
                        simout="hello\nFINAL=%s\n" % GOLDEN, rc=0)
        r1 = O.classify_ooo_run(f1, golden=GOLDEN)
        ck("F1 verdict Inactive", r1["L5"]["verdict"] == "Inactive", r1["L5"]["reason"])
        ck("F1 conservation ok", r1["conservation_ok"] is True, r1["violations"])
        ck("F1 L0 totals zero", r1["L0"]["totals"]["activated"] == 0, r1["L0"]["totals"])
        ck("F1 faults_source none", r1["L0"]["faults_source"] == "none", r1["L0"]["faults_source"])

        # ---- F2 masked: funnel activated=1, checksum==golden
        f2 = _mk_outdir(root, "f2-masked",
                        simout="FINAL=%s\n" % GOLDEN, rc=0,
                        logs={"fault_injections.log": [
                            "CHAOS_L0_FUNNEL: CHAOSPhysReg attempted=12 eligible=9 injected=1 activated=1"]})
        r2 = O.classify_ooo_run(f2, golden=GOLDEN)
        ck("F2 verdict Masked", r2["L5"]["verdict"] == "Masked", r2["L5"]["reason"])
        ck("F2 conservation ok", r2["conservation_ok"] is True, r2["violations"])
        ck("F2 funnel parsed", r2["L0"]["injectors"]["CHAOSPhysReg"]["attempted"] == 12
           and r2["L0"]["totals"]["activated"] == 1, r2["L0"]["injectors"])
        ck("F2 faults_source funnel_activated", r2["L0"]["faults_source"] == "funnel_activated")

        # ---- F3 sdc: funnel activated=1, checksum!=golden (non-default log name)
        f3 = _mk_outdir(root, "f3-sdc",
                        simout="FINAL=%s\n" % OTHER, rc=0,
                        logs={"decode_injections.log": [
                            "CHAOS_L0_FUNNEL: CHAOSDecode attempted=20 eligible=11 injected=2 activated=2"]})
        r3 = O.classify_ooo_run(f3, golden=GOLDEN)
        ck("F3 verdict SDC", r3["L5"]["verdict"] == "SDC", r3["L5"]["reason"])
        ck("F3 conservation ok", r3["conservation_ok"] is True, r3["violations"])
        ck("F3 legacy log scanned", "decode_injections.log" in r3["L0"]["logs_scanned"])

        # ---- F4 conservation violation: eligible>attempted
        f4 = _mk_outdir(root, "f4-violated",
                        simout="FINAL=%s\n" % GOLDEN, rc=0,
                        logs={"decode_injections.log": [
                            "CHAOS_L0_FUNNEL: CHAOSDecode attempted=5 eligible=7 injected=3 activated=2"]})
        r4 = O.classify_ooo_run(f4, golden=GOLDEN)
        ck("F4 conservation broken", r4["conservation_ok"] is False, r4["violations"])
        v4 = " ".join(r4["violations"])
        ck("F4 violation names injector+relation",
           "CHAOSDecode" in v4 and "eligible>attempted" in v4, v4)

        # ---- T5 abort legitimacy: panic + rc=134, no logs
        f5 = _mk_outdir(root, "t5-abort",
                        simerr="panic: inject went wrong\n", rc=134)
        r5 = O.classify_ooo_run(f5, golden=GOLDEN)
        ck("T5 verdict SimulatorError", r5["L5"]["verdict"] == "SimulatorError", r5["L5"]["reason"])
        ck("T5 abort L0 absent not violation", r5["conservation_ok"] is True, r5["violations"])
        ck("T5 L0 evidence absent", r5["L0"]["evidence"] == "absent", r5["L0"]["evidence"])

        # ---- T6 determinism cross-check: activated=0 but checksum!=golden
        f6 = _mk_outdir(root, "t6-det",
                        simout="FINAL=baadf00d0badf00d\n", rc=0,
                        logs={"fault_injections.log": [
                            "CHAOS_L0_FUNNEL: CHAOSPhysReg attempted=4 eligible=2 injected=1 activated=0"]})
        r6 = O.classify_ooo_run(f6, golden=GOLDEN)
        ck("T6 verdict Inactive (classify order)", r6["L5"]["verdict"] == "Inactive", r6["L5"]["reason"])
        ck("T6 determinism violation flagged", r6["conservation_ok"] is False, r6["violations"])
        v6 = " ".join(r6["violations"])
        ck("T6 violation names checksum!=golden", "checksum" in v6, v6)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    failed = [c for c in checks if not c[1]]
    print("\nSELFTEST %s (%d checks, %d failed)" % (
        "PASS" if not failed else "FAIL", len(checks), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
