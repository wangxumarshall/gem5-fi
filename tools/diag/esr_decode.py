#!/usr/bin/env python3
"""esr_decode.py — ARM64 ESR_ELx EC/FSC decoder for the openEuler SDC
diagnosis engine (plan §7.3, Task 4.1).

Decodes a 64-bit ESR_ELx value into its exception class (EC), instruction
length (IL), data-abort flags (WnR/ISV/SAS/SRT — when ISS is a data-abort
encoding), and the Fault Status Code (FSC) with translation level, then maps
the exception type onto the SDC-relevance weight matrix from the plan
(§7.3 异常类型加权表 — star ratings are the plan's reference ratios:
59.35x nested SError ... 6.92x BRK/BKPT ... 1x generic DABT/Oops).

Verification anchor (plan Task 4.1): ESR 0x96000044 must decode to
DABT / WnR=1 / FSC=L0 translation fault (the core179 repeated-WARN
signature from the six vmcore reports; 0x96000004 is the same with WnR=0).

Usage:
  python3 esr_decode.py 0x96000044
  python3 esr_decode.py --json 0x96000004 0x96000044 0x2000000
  echo "ESR = 0x96000044" | python3 esr_decode.py --stdin
"""
import argparse
import json
import re
import sys

# ESR_ELx layout (ARMv8-A, DDI 0487):
#   [63:32] ISS2+RES0 (only for some classes)   [31:26] EC
#   [25] IL   [24] ISS0 ... [23:0] ISS
# Data-abort ISS: [24] ISV, [23:22] SAS, [21:16] SRT, [11:10] EA,
#                 [9] FnV, [8] SET, [7] SF, [6] AR, [5] FnV? -> per spec:
#                 [7] SF [6] AR [5] ... WnR is ISS[6]; FSC is ISS[6:0].

EC_TABLE = {
    0x00: ("Undefined Instruction (current EL)", 4),   # 17.80x -> 4 stars
    0x01: ("WFI/WFE trapped", 0),
    0x03: ("PAC instruction (EL0/EL1, FA/PAC)", 0),
    0x0E: ("Illegal Execution State", 2),
    0x15: ("SVC (AArch32)", 0),
    0x17: ("SVC (AArch64)", 0),
    0x18: ("HVC", 0),
    0x19: ("SMC", 0),
    0x20: ("Instruction Abort from lower EL", 3),
    0x21: ("Instruction Abort from current EL", 3),
    0x22: ("PC-alignment fault", 1),
    0x24: ("Data Abort from lower EL", 4),             # 20.77x -> 4 stars
    0x25: ("Data Abort from current EL", 4),
    0x26: ("SP-alignment fault", 4),
    0x28: ("FP/Advanced SIMD trapped", 1),
    0x2C: ("System register trapped (MRS/MSR)", 1),
    0x2D: ("SVE trapped", 1),
    0x2F: ("SError interrupt", 5),                     # 59.35x nested -> 5
    0x30: ("Breakpoint (lower EL)", 3),                # 6.92x -> 3
    0x31: ("Breakpoint (current EL)", 3),
    0x32: ("Software Step (lower EL)", 3),
    0x33: ("Software Step (current EL)", 3),
    0x34: ("Watchpoint (lower EL)", 2),
    0x35: ("Watchpoint (current EL)", 2),
    0x3C: ("BRK (AArch64)", 3),                        # 6.92x -> 3
    0x3E: ("Pointer Authentication failure", 2),
}

FSC_TABLE = {
    0x00: "Address size fault, level 0",
    0x01: "Address size fault, level 1",
    0x02: "Address size fault, level 2",
    0x03: "Address size fault, level 3",
    0x04: "Translation fault, level 0",
    0x05: "Translation fault, level 1",
    0x06: "Translation fault, level 2",
    0x07: "Translation fault, level 3",
    0x09: "Access flag fault, level 1",
    0x0A: "Access flag fault, level 2",
    0x0B: "Access flag fault, level 3",
    0x0D: "Permission fault, level 1",
    0x0E: "Permission fault, level 2",
    0x0F: "Permission fault, level 3",
    0x10: "Synchronous external abort (SEA)",
    0x11: "Tag check fault",
    0x13: "Synchronous external abort on page-table walk, level -1",
    0x14: "Synchronous external abort on page-table walk, level 0",
    0x15: "Synchronous external abort on page-table walk, level 1",
    0x16: "Synchronous external abort on page-table walk, level 2",
    0x17: "Synchronous external abort on page-table walk, level 3",
    0x18: "Synchronous parity/ECC error on memory access",
    0x19: "Synchronous parity/ECC error on page-table walk, level -1",
    0x1A: "Synchronous parity/ECC error on page-table walk, level 0",
    0x1B: "Synchronous parity/ECC error on page-table walk, level 1",
    0x1C: "Synchronous parity/ECC error on page-table walk, level 2",
    0x1D: "Synchronous parity/ECC error on page-table walk, level 3",
    0x21: "Alignment fault",
    0x22: "Background flag fault",
    23:    "Unsupported atomic update",
}


def decode(esr: int) -> dict:
    """Decode one ESR_ELx value into EC/FSC + SDC relevance."""
    ec = (esr >> 26) & 0x3F
    il = (esr >> 25) & 1
    iss = esr & 0x1FFFFFF
    ec_name, weight = EC_TABLE.get(ec, (f"Unknown EC 0x{ec:02x}", 0))

    out = {
        "esr": f"0x{esr:016x}",
        "ec": f"0x{ec:02x}",
        "ec_name": ec_name,
        "il": il,
        "sdc_relevance": "★" * weight if weight else "-",
        "sdc_weight_stars": weight,
    }

    # Data-abort family: decode ISS flags + FSC.
    if ec in (0x24, 0x25):
        isv = (iss >> 24) & 1
        sas = (iss >> 22) & 3
        srt = (iss >> 16) & 0x1F
        wnr = (iss >> 6) & 1
        fsc = iss & 0x3F
        out.update({
            "wnr": wnr,                      # 0=read, 1=write
            "wnr_text": "write" if wnr else "read",
            "isv": isv,                      # syndrome valid (aborting instr info)
            "sas": sas,                      # access size
            "srt": srt,                      # register transfer
            "fsc": f"0x{fsc:02x}",
            "fsc_text": FSC_TABLE.get(fsc, f"unknown FSC 0x{fsc:02x}"),
        })
        if fsc in (0x10, 0x13, 0x14, 0x15, 0x16, 0x17):
            out["sdc_relevance_note"] = ("SEA — check RAS records: "
                                         "no valid record => SDC candidate (§7.3)")
        elif fsc in (0x04, 0x05, 0x06, 0x07):
            # Translation fault with a GOOD page table (spurious) is the
            # core179 signature: RAS-silent L0/L3 translation faults.
            out["sdc_relevance_note"] = ("translation fault — if the page table "
                                         "is intact this is the spurious-SDC "
                                         "signature (core179 family)")
    # Instruction abort family: FSC only.
    elif ec in (0x20, 0x21):
        fsc = iss & 0x3F
        out.update({
            "fsc": f"0x{fsc:02x}",
            "fsc_text": FSC_TABLE.get(fsc, f"unknown FSC 0x{fsc:02x}"),
        })
    # SError: ISS holds AET/EA/FnV; relevance depends on RAS record validity.
    elif ec == 0x2F:
        aet = (iss >> 10) & 7
        out.update({
            "aet": aet,
            "note": ("SError: SDC-relevant IFF no valid RAS Error Record "
                     "accompanies it (§7.3); with a valid record -> loud "
                     "fault, excluded (N3)"),
        })
    return out


def parse_esr_text(text: str):
    """Extract ESR hex values from free log text (e.g. 'ESR = 0x96000044')."""
    # match 0x-prefixed hex with >= 6 digits (typical ESR print width);
    # also catch the 'ESR_ELx = ...' / 'esr=...' spellings implicitly.
    return [int(m, 16) for m in
            re.findall(r"ESR[^\n]{0,20}?0x([0-9a-fA-F]{4,16})", text,
                       re.IGNORECASE)]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("values", nargs="*", help="ESR values (hex, 0x-prefixed or bare)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--stdin", action="store_true",
                    help="read log text from stdin, extract ESR values")
    args = ap.parse_args()

    if args.stdin:
        vals = parse_esr_text(sys.stdin.read())
    else:
        vals = []
        for v in args.values:
            vals.append(int(v, 16) if v.lower().startswith("0x") else int(v, 16))

    results = [decode(v) for v in vals]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    for r in results:
        print(f"ESR {r['esr']}: EC {r['ec']} {r['ec_name']}  "
              f"IL={r['il']}  SDC权重 {r['sdc_relevance']}")
        if "wnr_text" in r:
            print(f"  DABT: WnR={r['wnr']} ({r['wnr_text']}), ISV={r['isv']}, "
                  f"FSC={r['fsc']} — {r['fsc_text']}")
        elif "fsc_text" in r:
            print(f"  FSC={r['fsc']} — {r['fsc_text']}")
        if "sdc_relevance_note" in r:
            print(f"  NOTE: {r['sdc_relevance_note']}")
        if "note" in r:
            print(f"  NOTE: {r['note']}")


if __name__ == "__main__":
    main()
