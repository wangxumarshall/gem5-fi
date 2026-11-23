#!/usr/bin/env python3
"""Software state-flow reconstruction for the LSU E2E causal graphs.

This module answers two questions that the previous round answered by
temporal adjacency:

1. Which hash event updates which software accumulator, and is the
   predecessor relation a *real* renamed-register def/use relation?
2. What exact expression produced the final OUTPUT marker, and which
   state producers feed each operand of that expression?

Every relation is built from committed-instruction physical-register
def/use records, with the actual operand values and the static
disassembly.  Value equality alone is never used to create an edge; it is
only used to corroborate a def/use relation that the trace already shows.
"""
from __future__ import annotations

import collections

import e2e_strict_data as D


MAX_CHAIN = 40


def _disp(pc):
    return "0x%x" % pc if isinstance(pc, int) else pc


def _insn_desc(row):
    return {
        "dyn_inst_seq": row.seq,
        "pc": _disp(row.pc),
        "op": row.op,
        "disasm": row.disasm,
        "ctrace_line": row.line,
        "tick": row.tick,
    }


def _static(row, disasm):
    info = disasm.get(row.pc) if disasm else None
    return info if info else (row.op, "")


def _eval_row(row, disasm, values):
    """Recompute a committed instruction from its actual operands.

    Returns (ok, produced_value, reason).  ``ok=False`` means semantics are
    unsupported or the recomputation does not match the committed value;
    such an instruction can never upgrade an edge.
    """
    mnem, operands = _static(row, disasm)
    cls = row.dsts[0][0] if row.dsts else 0
    phys = row.dsts[0][2] if row.dsts else None
    # Conditional-select aliases (cinc/cneg/cinv) read PSTATE flags, which
    # the commit trace records as class-6 sources:
    # arch 0=C, 1=Z, 2=N, 3=V (verified against the committed cmp/subs row).
    fv = {}
    for (c2, a2, _p2), v2 in zip(row.srcs, row.srcvals):
        if c2 == 6 and v2 is not None:
            fv[a2] = v2
    flags = {"C": fv.get(0, 0), "Z": fv.get(1, 0),
             "N": fv.get(2, 0), "V": fv.get(3, 0)}
    try:
        outs, _flags = D.evaluate(mnem, operands, values, flags)
    except D.SemanticsError as exc:
        return False, None, "unsupported_semantics:%s" % exc
    if not outs or phys is None:
        return False, None, "no_destination"
    recorded = row.value_of(cls, phys)
    if recorded is None:
        return False, outs[0], "no_recorded_destination_value"
    if (outs[0] & D.MASK64) != (recorded & D.MASK64):
        return False, outs[0], "recomputed_value_mismatch"
    return True, outs[0], "recomputed_and_matched"


class StoreIndex:
    """Committed store versions for resolving spilled accumulator reloads."""

    def __init__(self, trace, disasm, archmem):
        self.rows = []
        for r in trace.rows:
            acc = archmem.accesses.get(r.idx) if archmem else None
            if not acc or "value" not in acc:
                continue
            info = disasm.get(r.pc) if disasm else None
            if not info:
                continue
            ops = D.split_ops(info[1])
            data_reg = D.parse_reg(ops[0]) if ops else None
            self.rows.append({
                "idx": r.idx, "seq": r.seq, "pc": r.pc,
                "addr": acc["addr"], "width": acc["width"],
                "value": acc["value"],
                "data_arch": data_reg[1] if data_reg else None,
                "row": r, "mnem": acc["mnem"],
            })
        self.rows.sort(key=lambda x: x["idx"])

    def version_before(self, addr, width, idx):
        """Latest committed store covering the load bytes before idx."""
        for s in reversed(self.rows):
            if s["idx"] >= idx:
                continue
            a, w = s["addr"], s["width"]
            if a <= addr and addr + width <= a + w:
                return s
        return None


def _dst_phys(row):
    for (_c, _a, p, _v) in row.dsts:
        if p is not None and p >= 0:
            return (_c, p)
    return None


def resolve_producer(trace, disasm, cls, phys, before_idx, stores=None,
                     archmem=None, max_steps=MAX_CHAIN):
    """Follow copies (and stack spills) to the instruction that produced a value.

    The return record names the terminal *instruction instance* by its
    commit-trace index.  Two observations that resolve to the same terminal
    index are therefore genuinely the same produced value, not merely two
    equal numbers.
    """
    chain = []
    seen = set()
    cur_cls, cur_phys = cls, phys
    idx = before_idx
    for _ in range(max_steps):
        key = (cur_cls, cur_phys, idx)
        if key in seen:
            return {"found": False, "reason": "copy_cycle", "chain": chain}
        seen.add(key)
        d = trace.defining_insn(cur_cls, cur_phys, idx)
        if d is None:
            return {"found": False, "reason": "no_defining_instruction",
                    "chain": chain, "phys": cur_phys}
        val = d.value_of(cur_cls, cur_phys)
        rec = {"def_idx": d.idx, "def_seq": d.seq, "phys": cur_phys,
               "class_": cur_cls, "value": val, **_insn_desc(d)}
        src = D.copy_source(d, disasm)
        if src is not None:
            rec["follow"] = "copy"
            chain.append(rec)
            cur_cls, cur_phys = src[0], src[2]
            idx = d.idx
            continue
        mnem, operands = _static(d, disasm)
        if mnem.lower() in ("ldr", "ldur", "ldar", "ldaxr") and stores:
            vals = D.row_src_map(d)
            aw = D.memory_address(mnem, operands, vals)
            if aw is not None:
                addr, width, _ = aw
                st = stores.version_before(addr, width, d.idx)
                load_value = val
                # A spill reload is only a copy of the stored value if the
                # committed load actually returns that stored version.  A
                # suppressed/corrupted write makes this false; in that case
                # the load is the real producer of the delivered value.
                stored_matches = (
                    st is not None and load_value is not None and
                    (st["value"] & D.MASK64) == (load_value & D.MASK64))
                if st is not None and st["data_arch"] is not None and \
                        stored_matches:
                    rec["follow"] = "spill"
                    rec["spill_store_seq"] = st["seq"]
                    rec["spill_addr"] = _disp(addr)
                    chain.append(rec)
                    cur_cls, cur_phys = 0, None
                    # locate the data register's physical definition
                    srcp = None
                    for (c, a, p) in st["row"].srcs:
                        if c == 0 and a == st["data_arch"] and p >= 0:
                            srcp = (c, p)
                            break
                    if srcp is None:
                        return {"found": False, "reason": "spill_source_missing",
                                "chain": chain}
                    cur_cls, cur_phys = srcp
                    idx = st["row"].idx
                    continue
        rec["follow"] = "terminal"
        chain.append(rec)
        eval_ok, evaluated, why = _eval_row(d, disasm, D.row_src_map(d))
        return {
            "found": val is not None,
            "terminal": d, "def_idx": d.idx, "def_seq": d.seq,
            "phys": cur_phys, "class_": cur_cls, "value": val,
            "mnem": mnem, "operands": operands,
            "semantics_ok": eval_ok, "semantics_reason": why,
            "evaluated": evaluated,
            "init": mnem.lower() in ("mov", "movz", "movn", "movk") and
            len(D.real_sources(d)) == 0,
            "chain": chain,
        }
    return {"found": False, "reason": "max_chain_depth", "chain": chain}


def _slot(trace, disasm, group, slot, stores=None, archmem=None):
    src, val, arch = group.slot_source(slot)
    if src is None:
        return {"slot": slot, "found": False,
                "reason": "marker_slot_has_no_register_source"}
    cls, phys = src
    res = resolve_producer(trace, disasm, cls, phys, group.idxs[slot],
                           stores, archmem)
    res.update({
        "slot": slot, "marker_value": val, "arg_phys": phys,
        "arg_arch": arch,
        "value_matches_slot": (res.get("value") is not None and
                               val is not None and
                               (res["value"] & D.MASK64) ==
                               (val & D.MASK64)),
    })
    return res


def analyze_hash_streams(trace, disasm, hash_events, hash_records,
                         stores=None, archmem=None):
    """Reconstruct per-accumulator hash state streams from real def/use.

    ``hash_events`` and ``hash_records`` are parallel (the SWEvent and the
    record produced by ``verify_hash_events``).
    """
    per = []
    for i, (e, h) in enumerate(zip(hash_events, hash_records)):
        rec = {
            "index": i, "seq": e.seq, "site": e.site,
            "iteration": e.order,
            "input": _slot(trace, disasm, e.group, 1, stores, archmem),
            "before": _slot(trace, disasm, e.group, 2, stores, archmem),
            "after": _slot(trace, disasm, e.group, 3, stores, archmem),
            "transition_verified": h.get("transition_verified"),
            "marker_instruction_seqs": e.group.seqs,
            "ctrace_line": e.group.lines[3],
        }
        # A slot is only usable if its terminal instruction actually
        # produced the marker's recorded value.
        rec["provenance_ok"] = all(
            rec[k].get("found") and rec[k].get("value_matches_slot")
            for k in ("input", "before", "after"))
        per.append(rec)

    after_by_def = collections.defaultdict(list)
    for r in per:
        if r["after"].get("found"):
            after_by_def[r["after"]["def_idx"]].append(r["index"])

    links = []
    ambiguity = []
    for r in per:
        b = r["before"]
        if not b.get("found"):
            r["predecessor"] = None
            r["predecessor_reason"] = "before_producer_unresolved"
            continue
        cands = [j for j in after_by_def.get(b["def_idx"], [])
                 if j != r["index"] and per[j]["seq"] < r["seq"]]
        if not cands:
            r["predecessor"] = None
            r["predecessor_reason"] = "stream_root"
            continue
        if len(cands) > 1:
            ambiguity.append({"event": r["index"], "candidates": cands})
            cands = [max(cands)]
        j = cands[0]
        a = per[j]
        value_ok = (a["after"].get("value") is not None and
                    b.get("value") is not None and
                    (a["after"]["value"] & D.MASK64) ==
                    (b["value"] & D.MASK64))
        semantic_ok = bool(a.get("transition_verified") and
                           r.get("transition_verified"))
        ok = value_ok and semantic_ok and a["provenance_ok"] and \
            r["provenance_ok"]
        r["predecessor"] = j
        r["predecessor_reason"] = (
            "same_terminal_def_instance" if ok else
            ("value_mismatch" if not value_ok else
             "semantic_transition_unverified"))
        links.append({
            "source": j, "target": r["index"], "verified": ok,
            "terminal_def_idx": b["def_idx"],
            "terminal_def_seq": b["def_seq"],
            "source_after_value": a["after"].get("value"),
            "target_before_value": b.get("value"),
            "same_def_instance": True,
            "value_matches": value_ok,
            "fnv_transitions_verified": semantic_ok,
            "source_phys": a["after"].get("phys"),
            "target_phys": b.get("phys"),
            "reason": r["predecessor_reason"],
        })

    # Stream identity = connected components of verified links.
    parent = list(range(len(per)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for l in links:
        if l["verified"]:
            union(l["source"], l["target"])
    components = collections.defaultdict(list)
    for i in range(len(per)):
        components[find(i)].append(i)
    stream_ids = {}
    by_stream = {}
    for n, (root, members) in enumerate(sorted(
            components.items(), key=lambda kv: per[min(kv[1])]["seq"])):
        sid = "S%d" % (n + 1)
        by_stream[sid] = sorted(members)
        for m in members:
            stream_ids[m] = sid

    def digest(r):
        return {
            "index": r["index"], "seq": r["seq"], "site": r["site"],
            "iteration": r["iteration"],
            "stream": stream_ids.get(r["index"]),
            "predecessor": r.get("predecessor"),
            "predecessor_reason": r.get("predecessor_reason"),
            "provenance_ok": r["provenance_ok"],
            "before_terminal_def_seq": r["before"].get("def_seq"),
            "after_terminal_def_seq": r["after"].get("def_seq"),
            "before_value": _hex(r["before"].get("value")),
            "after_value": _hex(r["after"].get("value")),
            "input_value": _hex(r["input"].get("value")),
            "before_phys": r["before"].get("phys"),
            "after_phys": r["after"].get("phys"),
        }

    roots = [r["index"] for r in per
             if r.get("predecessor") is None]
    tails = {}
    for i in range(len(per)):
        if not any(l["source"] == i for l in links if l["verified"]):
            tails[stream_ids.get(i)] = i
    return {
        "events": [digest(r) for r in per],
        "records": per,
        "links": links,
        "streams": by_stream,
        "roots": roots,
        "tails": tails,
        "ambiguity": ambiguity,
        "verified_links": sum(1 for l in links if l["verified"]),
        "unverified_links": sum(1 for l in links if not l["verified"]),
        "events_with_unresolved_before": sum(
            1 for r in per if not r["before"].get("found")),
        "events_with_bad_provenance": sum(
            1 for r in per if not r["provenance_ok"]),
    }


def _hex(v):
    return None if v is None else "0x%x" % (v & D.MASK64)


def _operand_roles(def_row, disasm, slot_sources):
    """Map the static source operands of the output expression to slots.

    slot_sources: {2: source arch of the before-slot argument, 3: ...}.
    Only arch identity is accepted; equal values are not enough.
    """
    info = _static(def_row, disasm)
    ops = D.split_ops(info[1])
    roles = []
    for tok in ops[1:]:
        reg = D.parse_reg(tok.split(",")[0].strip())
        if reg and reg[0] not in ("zr", "sp"):
            roles.append(reg[1])
    out = {}
    for slot, arch in slot_sources.items():
        if arch in roles:
            out[slot] = roles.index(arch)
    return roles, out


def analyze_output_expression(trace, disasm, output_group, hash_analysis,
                              stores=None, archmem=None):
    """Verify the final OUTPUT marker's actual computation.

    Returns a record with the expression instruction, recomputed value,
    operand provenance and the state producer for each operand.  The
    caller may only create a final-output edge when ``verified`` is true.
    """
    slots = {s: _slot(trace, disasm, output_group, s, stores, archmem)
             for s in (1, 2, 3)}
    a, b, c = (output_group.vals[1], output_group.vals[2],
               output_group.vals[3])
    # The expression that produces slot 1: follow value-preserving copies
    # until the real producing instruction (eor/madd/... or an init).
    src1 = output_group.slot_source(1)[0]
    if src1 is None:
        return {"verified": False, "reason": "output_slot_1_unresolved",
                "slots": slots, "a": _hex(a), "b": _hex(b), "c": _hex(c)}
    cur = (src1[0], src1[1])
    idx = output_group.idxs[1]
    copy_chain = []
    d1 = None
    for _ in range(16):
        d = trace.defining_insn(cur[0], cur[1], idx)
        if d is None:
            break
        cs = D.copy_source(d, disasm)
        if cs is not None:
            copy_chain.append(d)
            cur = (cs[0], cs[2])
            idx = d.idx
            continue
        d1 = d
        break
    if d1 is None:
        return {"verified": False, "reason": "output_expression_missing",
                "slots": slots, "a": _hex(a), "b": _hex(b), "c": _hex(c)}
    mnem, operands = _static(d1, disasm)
    values = D.row_src_map(d1)
    eval_ok, evaluated, why = _eval_row(d1, disasm, values)

    # Which state produced each operand?  Resolve the marker slot to its
    # terminal instruction instance and identify a hash event with the
    # same after-terminal, or a non-hash state update, or a constant.
    hash_by_after = {}
    for i, r in enumerate(hash_analysis["records"]):
        if r["after"].get("found"):
            hash_by_after[r["after"]["def_idx"]] = i

    def producer(slot):
        s = slots[slot]
        if not s.get("found"):
            return {"kind": "unresolved", "reason": s.get("reason")}
        prod = hash_by_after.get(s["def_idx"])
        if prod is not None:
            return {"kind": "hash_accumulator", "hash_event": prod,
                    "def_seq": s["def_seq"], "value": s.get("value"),
                    "stream": hash_analysis["events"][prod]["stream"]}
        if s.get("init"):
            return {"kind": "constant", "value": s.get("value"),
                    "def_seq": s["def_seq"]}
        return {"kind": "state_update", "def_seq": s["def_seq"],
                "op": s.get("mnem"), "disasm": s["terminal"].disasm,
                "value": s.get("value"),
                "semantics_ok": s.get("semantics_ok")}

    # Match each expression operand to an OUTPUT slot by the *producer
    # instruction instance* the operand resolves to.  Register numbers on
    # the marker row are copies and are not identities by themselves.
    op_prod = []
    for (c2, a2, p2) in D.real_sources(d1):
        pr = resolve_producer(trace, disasm, c2, p2, d1.idx,
                              stores, archmem)
        op_prod.append({"arch": a2, "producer": pr,
                        "value": values.get(a2)})
    role_map = {}
    for slot in (2, 3):
        for oi, op in enumerate(op_prod):
            if op["producer"].get("def_idx") == slots[slot].get("def_idx"):
                role_map[slot] = oi
                break
    role_value_ok = {}
    for slot in (2, 3):
        oi = role_map.get(slot)
        role_value_ok[slot] = bool(
            oi is not None and op_prod[oi]["value"] is not None and
            (op_prod[oi]["value"] & D.MASK64) ==
            (output_group.vals[slot] & D.MASK64))

    prod_b, prod_c = producer(2), producer(3)
    operand_producers = {2: prod_b, 3: prod_c, 1: producer(1)}
    both = (2 in role_map and 3 in role_map and
            role_value_ok[2] and role_value_ok[3])
    formula_ok = False
    formula = None
    expected = None
    if both and mnem.lower() == "eor":
        expected = (b ^ c) & D.MASK64
        formula = "b XOR c"
        formula_ok = bool(eval_ok and a == expected)
    elif both and mnem.lower() == "add":
        expected = (b + c) & D.MASK64
        formula = "b + c"
        formula_ok = bool(eval_ok and a == expected)
    elif both:
        expected = evaluated
        formula = "%s(%s)" % (mnem, operands)
        formula_ok = bool(eval_ok and a == evaluated)
    else:
        # Identity: the OUTPUT operand *is* the single accumulator state.
        expected = slots[1].get("value")
        formula = "identity"
        formula_ok = bool(
            eval_ok and expected is not None and
            (expected & D.MASK64) == a and
            slots[1].get("def_idx") == d1.idx)

    identity = not both
    verified = bool(
        eval_ok and formula_ok and
        slots[1].get("value") is not None and
        (slots[1]["value"] & D.MASK64) == a and
        (identity or both))
    participating = ({1: operand_producers[1]} if identity else
                     {2: prod_b, 3: prod_c})
    return {
        "verified": verified,
        "reason": (None if verified else
                   (why if not eval_ok else
                    ("operand_role_unresolved" if not formula_ok else
                     "slot_value_mismatch"))),
        "a": _hex(a), "b": _hex(b), "c": _hex(c),
        "expression": {
            "def_seq": d1.seq, "pc": _disp(d1.pc), "op": mnem,
            "disasm": d1.disasm, "operands": operands,
            "ctrace_line": d1.line,
            "recomputed": _hex(evaluated), "evaluated": eval_ok,
            "semantics_reason": why,
        },
        "formula": formula,
        "formula_expected": _hex(expected),
        "formula_verified": formula_ok,
        "is_copy": identity,
        "operand_roles": {str(k): v for k, v in role_map.items()},
        "operand_role_values_verified": {str(k): v
                                         for k, v in role_value_ok.items()},
        "operand_producers": {str(k): v for k, v in participating.items()},
        "all_slot_producers": {str(k): v
                               for k, v in operand_producers.items()},
        "slots": {str(k): {"found": v.get("found"),
                           "def_seq": v.get("def_seq"),
                           "phys": v.get("phys"),
                           "value": _hex(v.get("value")),
                           "marker_value": _hex(v.get("marker_value")),
                           "value_matches_slot": v.get("value_matches_slot")}
                  for k, v in slots.items()},
        "a_equals_b_xor_c": (a == ((b ^ c) & D.MASK64)),
    }
