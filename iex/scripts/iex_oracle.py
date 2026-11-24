#!/usr/bin/env python3
"""Independent bigint oracle for the frozen IEX v3 model/context matrix.

All arithmetic is recomputed from the frozen 28_Context_5x7 inputs.  The
guest workload never derives its expected values from the target operation;
the driver only materialises path markers and stores the observed raw value.
"""
import json
import os

MASK = 0xA5A5A5A5A5A5A5A5
M64 = (1 << 64) - 1

MODELS = [
    "IEX-M001", "IEX-M002", "IEX-M003", "IEX-M004",
    "IEX-M005", "IEX-M006", "IEX-M007",
]
CONTEXTS = ["C01", "C02", "C03", "C04", "C05"]
TIMINGS = ["T01", "T02", "T03"]
PERCENTILES = {"T01": 0.10, "T02": 0.50, "T03": 0.90}

# Frozen 28 inputs (A, B) and the context-local final constants that are not
# simple model arithmetic (C03 isolation constants, M005/M006 sentinels).
INPUTS = {
    "IEX-M001": {
        "C01": (0x00000000FFFFFFFF, 0x0000000000000001),
        "C02": (0x0000000080000000, 0x0000000080000000),
        "C03": (0x00000000FFFFFFFF, 0x0000000000000001),
        "C04": (0x00000000FFFFFFFF, 0x0000000000000001),
        "C05": (0x00000000FFFFFFFF, 0x0000000000000001),
    },
    "IEX-M002": {
        "C01": (0x0000000000000001, 0x0000000000000000),
        "C02": (0x0000000000000003, 0x0000000000000001),
        "C03": (0x0000000000000001, 0x0000000000000000),
        "C04": (0x0000000000000001, 0x0000000000000000),
        "C05": (0x0000000000000001, 0x0000000000000000),
    },
    "IEX-M003": {
        "C01": (0x00000000FFFFFFFF, 0x00000001FFFFFFFF),
        "C02": (0x0000000100000001, 0xFFFFFFFFFFFFFFFF),
        "C03": (0x00000000FFFFFFFF, 0x00000001FFFFFFFF),
        "C04": (0x00000000FFFFFFFF, 0x00000001FFFFFFFF),
        "C05": (0x00000000FFFFFFFF, 0x00000001FFFFFFFF),
    },
    "IEX-M004": {
        "C01": (0x0000000000000001, 0x0000000000000001),
        "C02": (0x0000000000000064, 0x000000000000000A),
        "C03": (0x0000000000000001, 0x0000000000000001),
        "C04": (0x0000000000000001, 0x0000000000000001),
        "C05": (0x0000000000000001, 0x0000000000000001),
    },
    "IEX-M005": {
        "C01": (0x0000000000000007, 0x0000000000000007),
        "C02": (0x0000000000000007, 0x0000000000000007),
        "C03": (0x0000000000000007, 0x0000000000000007),
        "C04": (0x0000000000000007, 0x0000000000000007),
        "C05": (0x0000000000000007, 0x0000000000000007),
    },
    "IEX-M006": {
        "C01": (0x0000000000000000, 0x0000000000000000),
        "C02": (0x0000000000000000, 0x0000000000000001),
        "C03": (0x0000000000000000, 0x0000000000000000),
        "C04": (0x0000000000000000, 0x0000000000000000),
        "C05": (0x0000000000000000, 0x0000000000000000),
    },
    "IEX-M007": {
        "C01": (0x0000000000000001, 0),
        "C02": (0x0000000080000000, 0),
        "C03": (0x0000000000000001, 0),
        "C04": (0x0000000000000001, 0),
        "C05": (0x0000000000000001, 0),
    },
}

C03_FINAL = 0x0123456789ABCDEF
C05_GOLD = 0x00000000000000A1
C05_FAULT = 0x0000000000000051

# M005 path markers (taken / fall-through). C01/C03/C04/C05 use EQ with
# a==b; C02 uses NE with a==b.
M005_MARKERS = {
    "C01": {"eq_taken": 0xA1, "eq_fall": 0x51},
    "C02": {"ne_taken": 0xA2, "ne_fall": 0x52},
    "C03": {"eq_taken": 0xA1, "eq_fall": 0x51},
    "C04": {"eq_taken": 0xA1, "eq_fall": 0x51},
    "C05": {"eq_taken": 0xA1, "eq_fall": 0x51},
}

# M006 CSEL operands (op1 = selected on EQ, op2 = selected on NE).
M006_CSEL = {
    "C01": (0xC1, 0x31),
    "C02": (0xC3, 0x33),
    "C03": (0xC1, 0x31),
    "C04": (0xC1, 0x31),
    "C05": (0xC1, 0x31),
}


def ror64(x, n):
    return ((x >> n) | (x << (64 - n))) & M64


def chain_c04(raw):
    t1 = (raw ^ MASK) & M64
    t2 = (t1 + 17) & M64
    t3 = ror64(t2, 7)
    t4 = (t3 + ((t3 << 1) & M64)) & M64
    return t4, (t4 ^ MASK) & M64


def clz64(a):
    assert a != 0
    return 64 - a.bit_length()


def model_raw(model, a, b, ctx):
    """Return (golden_raw, fault_raw_if_committed) for the model operation."""
    if model == "IEX-M001":
        g = (a + b) & M64
        c32 = ((a & 0xFFFFFFFF) + (b & 0xFFFFFFFF)) >> 32
        f = (g - (1 << 32)) & M64 if c32 == 1 else g
        return g, f
    if model == "IEX-M002":
        eff = b & 0x3F
        g = (a << eff) & M64
        f = (a << (eff ^ 1)) & M64
        return g, f
    if model == "IEX-M003":
        g = ((a * b) >> 64) & M64
        f = (g - 1) & M64
        return g, f
    if model == "IEX-M004":
        assert b > 0 and a >= b
        g = a // b
        f = 0
        return g, f
    if model == "IEX-M005":
        if ctx == "C02":
            taken = not (a == b)          # B.NE with a == b is false
            m = M005_MARKERS[ctx]
            return (m["ne_taken"] if taken else m["ne_fall"],
                    m["ne_fall"] if taken else m["ne_taken"])
        taken = (a == b)                  # B.EQ with a == b is true
        m = M005_MARKERS[ctx]
        return (m["eq_taken"] if taken else m["eq_fall"],
                m["eq_fall"] if taken else m["eq_taken"])
    if model == "IEX-M006":
        z = (a == b)
        op1, op2 = M006_CSEL[ctx]
        g = op1 if z else op2
        f = op2 if z else op1
        return g, f
    if model == "IEX-M007":
        g = clz64(a)
        return g, g + 1
    raise KeyError(model)


def context_vectors(model, ctx):
    a, b = INPUTS[model][ctx]
    g_raw, f_raw = model_raw(model, a, b, ctx)
    if ctx in ("C01", "C02"):
        final_g, final_f = g_raw, f_raw
        aux_g = (final_g ^ MASK) & M64
        aux_f = (final_f ^ MASK) & M64
    elif ctx == "C03":
        final_g = final_f = C03_FINAL
        aux_g = aux_f = 0
    elif ctx == "C04":
        final_g, aux_g = chain_c04(g_raw)
        final_f, aux_f = chain_c04(f_raw)
    elif ctx == "C05":
        # target raw is compared with the context-local golden; both the
        # golden and fault runs materialise one of two fixed markers.
        final_g = C05_GOLD if g_raw == g_raw else C05_FAULT
        final_f = C05_GOLD if f_raw == g_raw else C05_FAULT
        aux_g = (final_g ^ MASK) & M64
        aux_f = (final_f ^ MASK) & M64
    else:
        raise KeyError(ctx)
    return {
        "model": model, "context": ctx, "a": a, "b": b,
        "local_golden": g_raw, "local_fault": f_raw,
        "final_golden": final_g, "final_fault": final_f,
        "aux_golden": aux_g, "aux_fault": aux_f,
    }


def all_vectors():
    return {f"{m}-{c}": context_vectors(m, c)
            for m in MODELS for c in CONTEXTS}


def verify_against_workbook(path):
    """Cross-check the independent oracle against 28_Context_5x7."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["28_Context_5x7"]
    hdr = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(hdr)}
    mismatches = []
    checked = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[idx["ContextKey"]]:
            continue
        m = row[idx["ModelID"]]
        c = row[idx["ContextID"]]
        v = context_vectors(m, c)
        checked += 1
        for key, exp_key in (
            ("local_golden", "LocalGolden_hex"),
            ("local_fault", "LocalFault_hex"),
            ("final_golden", "FinalGolden_hex"),
            ("final_fault", "FinalFault_if_committed_hex"),
            ("aux_golden", "GoldenAux_hex"),
            ("aux_fault", "FaultAux_if_committed_hex"),
        ):
            want = int(str(row[idx[exp_key]]), 16)
            if v[key] != want:
                mismatches.append({
                    "context": f"{m}-{c}", "field": key,
                    "oracle": f"0x{v[key]:016X}",
                    "workbook": f"0x{want:016X}",
                })
    return {"checked_contexts": checked, "mismatches": mismatches}


def _default_workbook():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(root, "inputs",
                     "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx"),
        os.path.join(os.path.dirname(root), "inputs",
                     "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", default=_default_workbook())
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "oracle", "oracle_vectors.json"))
    args = ap.parse_args()
    vec = all_vectors()
    check = verify_against_workbook(args.workbook)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"mask": MASK, "spec": "IEX_WHEN_5x3_v3_2026-11-23",
                   "vectors": vec, "workbook_check": check}, f, indent=2)
    print(f"oracle contexts={len(vec)} checked={check['checked_contexts']} "
          f"mismatches={len(check['mismatches'])}")
    if check["mismatches"]:
        for m in check["mismatches"][:20]:
            print(m)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
