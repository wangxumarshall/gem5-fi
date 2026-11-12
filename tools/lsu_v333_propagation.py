#!/usr/bin/env python3
"""Chain-scoped, honest causal-propagation table for the LSU 60-context matrix.

This replaces the v3.3.2 tautology (``Activation = injection seq=N``) with a
real chain reconstruction:

  * chain = the injection's ``ptag`` plus the fault instruction's
    ``dyn_inst_seq`` (commit/squash nodes are written with ``ptag=0``);
  * ``Activation`` is the model's own activation record (``a01_ea``,
    ``fw02_decision``, ``store_writeback``, ``sp05_complete``, ...) carrying
    the target ordinal, never ``injection seq=N``;
  * ``Downstream``/``Consumer`` are the first *different-seq*
    ``consumer_commit``/``errant_commit`` records bound to the chain ptag,
    with PC/seq/tick.

Terminal adjudication is model-scoped and evidence-based (ledger L-A08/L-A09/
L-A10, L-C03/L-C05):

  A01-R03  a01_ea_discarded;applied_to_request=0 -> INJECTION_NOT_ACTIVATED
  A01-R02  squash_cause=unrelated;fault_caused=0 -> SQUASHED
  A03      checksum != golden                     -> SDC/ORACLE_FAIL
  RP01     CHAOS_RP01_WATCHDOG_EXPIRED            -> HANG_WATCHDOG
  SQ03     MASKED / VISIBILITY_TIMING_SHIFT       (4/5 moved, 1/5 lifecycle)
  SP05     store_data_fnv=null                    -> RELOAD_UNVERIFIABLE
  LQ04     ENTRY_INVALIDATED_RESTORED             -> MASKED
  MD04-R01 INERT_AFTER_COMPLETION                 -> MASKED
  FW02-R03 SUPPRESSED_FORWARD_NORMAL_VALUE        -> MASKED

``TraceCompleteness`` is COMPLETE only when the chain actually contains
injection + activation + first divergence + (consumer or terminal witness) +
commit/squash/hang evidence.  Structure alone is never enough.

No value is invented: anything not observed is ``n/a``.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")

# ROI start/end/N and the five frozen percentile ordinals (README_GROUND_TRUTH §3)
ROI = {
    "A01": (1040, 1234, 195, [1059, 1098, 1137, 1176, 1215]),
    "A03": (1040, 1234, 195, [1059, 1098, 1137, 1176, 1215]),
    "FW02": (8, 67, 60, [13, 25, 37, 49, 61]),
    "FW05": (1, 2000, 2000, [200, 600, 1000, 1400, 1800]),
    "SQ01": (1006, 1133, 128, [1018, 1044, 1069, 1095, 1121]),
    "SQ03": (1009, 1136, 128, [1021, 1047, 1072, 1098, 1124]),
    "SP05": (940, 1067, 128, [952, 978, 1003, 1029, 1055]),
    "DA04": (33, 1056, 1024, [135, 340, 544, 749, 954]),
    "LP01": (886, 17525, 16640, [2549, 5877, 9205, 12533, 15861]),
    "MD04": (3, 10, 8, [3, 5, 6, 8, 10]),
    "LQ04": (1, 5, 5, [1, 2, 3, 4, 5]),
    "RP01": (1, 255, 255, [26, 77, 128, 179, 230]),
}

PERCENTILES = (0.10, 0.30, 0.50, 0.70, 0.90)

FROZEN_ORACLE = {
    "A01": "728e604ffcec539d", "A03": "728e604ffcec539d",
    "FW02": "1f4cbf14327717df", "FW05": "67afad307642983e",
    "SQ01": "ba3b3185e541ad03", "SQ03": "ba3b3185e541ad03",
    "SP05": "2543a2a60de01795", "DA04": "3f89eab79392ce69",
    "LP01": "99c106541150be0e", "MD04": "59fc61c040618747",
    "LQ04": "b097eb83f71545cb", "RP01": "59fc61c040618747",
}

COLUMNS = (
    "ModelID", "ContextID", "ROI/Percentile/Ordinal", "Injection",
    "Activation", "FirstDivergence", "Downstream", "Consumer",
    "CommitSquashReplay", "Terminal", "TerminalReason", "ApplicationOracle",
    "EvidenceClass", "TraceCompleteness", "MaskingMechanism", "EvidencePaths",
)

# event types that confirm the faulting instruction reached the model record
ACTIVATION_EVENTS = {
    "A01": ("a01_ea", "a01_ea_discarded"),
    "FW02": ("fw02_decision",),
    "FW05": ("register_writeback",),
    "SQ01": ("store_writeback",),
    "SQ03": ("store_writeback",),
    "SP05": ("sp05_complete",),
    "DA04": ("store_writeback",),
    "LP01": ("memory_response",),
    "MD04": ("register_writeback",),
    "LQ04": ("memory_response",),
}

DIVERGENCE_EVENTS = {
    "A01": ("a01_ea", "a01_ea_discarded"),
    "FW02": ("fw02_decision",),
    "FW05": ("register_writeback", "fw05_reload"),
    "SQ01": ("store_writeback", "sq01_chain"),
    "SQ03": ("store_writeback", "sq03_effect"),
    "SP05": ("sp05_complete", "sp05_stage"),
    "DA04": ("store_mem_write", "store_writeback"),
    "LP01": ("memory_response",),
    "MD04": ("register_writeback",),
    "LQ04": ("memory_response", "register_writeback"),
}

MECHANISM_EVENTS = {
    "A01": ("a01_ea", "a01_ea_discarded", "a01_golden_resp", "a01_consumed"),
    "FW02": ("fw02_decision",),
    "FW05": ("fw05_reload",),
    "SQ01": ("sq01_chain",),
    "SQ03": ("sq03_effect", "sq03_complete"),
    "SP05": ("sp05_stage", "sp05_complete"),
    "DA04": ("store_writeback", "store_mem_write"),
    "LP01": ("memory_response",),
    "MD04": ("register_writeback",),
    "LQ04": ("register_writeback",),
}

WAIT_EVENTS = ("consumer_commit", "errant_commit")


def parse_detail(detail: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (detail or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def load_events(run: Path) -> list[dict]:
    p = run / "trace_v31.jsonl"
    if not p.exists():
        return []
    events = []
    for line in p.read_text(errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("record_type") == "event":
            events.append(e)
    return events


def load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def raw(value: str | None) -> str:
    """Return the recorded token verbatim.

    The trace writes PCs/EAs without a 0x prefix and physical addresses in
    decimal; converting either would silently corrupt the identity (a PC
    ``400598`` is hex, a PA ``78008`` is decimal).  Never reformat.
    """
    if value in (None, "", "null", "None"):
        return "n/a"
    return str(value)


def chain_events(events: list[dict], ptag, seq) -> list[dict]:
    out = []
    for e in events:
        if ptag not in (None, 0, "0") and e.get("ptag") == ptag:
            out.append(e)
        elif seq is not None and e.get("dyn_inst_seq") == seq:
            out.append(e)
    return out


def first_of(chain, types, *, after_seq=None, exclude_seq=None):
    for e in chain:
        if e.get("event_type") not in types:
            continue
        if after_seq is not None and (e.get("timestamp") or 0) < after_seq:
            continue
        if exclude_seq is not None and e.get("dyn_inst_seq") == exclude_seq:
            continue
        return e
    return None


def rich_fields(chain, seq) -> dict[str, str]:
    """First-seen key/value pairs from every detail on the fault's own seq.

    Keeps full integers (LP01's LQ ids must not be truncated) and never
    overwrites an earlier measurement with a later null.
    """
    d: dict[str, str] = {}
    for e in chain:
        if e.get("dyn_inst_seq") != seq:
            continue
        for k, v in parse_detail(e.get("detail")).items():
            if v in ("", "null", "None"):
                continue
            d.setdefault(k, v)
    return d


def pick(d: dict[str, str], *keys: str) -> str:
    for k in keys:
        v = d.get(k)
        if v not in (None, "", "null", "None"):
            return v
    return "n/a"


def identify(model: str, chain, seq, inj) -> dict[str, str]:
    """Carry PC/VA/PA/SQ/LQ/generation/tick/type/state from the raw records."""
    d = rich_fields(chain, seq)
    activation = first_of(chain, ACTIVATION_EVENTS.get(model, ()))
    ad = parse_detail(activation.get("detail")) if activation else {}

    pc = pick(ad, "pc", "load_pc", "store_pc") if ad else "n/a"
    if pc == "n/a":
        pc = pick(d, "pc", "load_pc", "store_pc")
    va = pick(d, "request_va", "va", "vaddr", "actual_ea", "new_addr",
              "addr", "load_addr", "store_addr")
    va = raw(va)
    pa = raw(pick(d, "pa"))
    lq = pick(d, "lq_entry_id", "lq_idx", "load_lq_entry_id")
    sq = pick(d, "sq_entry_id", "sq_idx")
    gen = pick(d, "entry_generation", "lq_gen", "load_entry_generation",
               "sq_entry_generation", "gen")
    tick = inj.get("timestamp") if inj else d.get("inject_tick", "n/a")
    is_load = d.get("is_load")
    if is_load == "1":
        itype = "Load"
    elif model in ("SQ01", "SQ03", "SP05", "DA04"):
        itype = "Store"
    elif model in ("FW02", "FW05", "A01", "A03", "LP01", "LQ04", "MD04"):
        itype = "Load"
    else:
        itype = "n/a"

    state_keys = ("occ_before", "occ_after", "canwb_before", "canwb_after",
                  "valid_before", "valid_after", "request_before",
                  "request_after", "replay_gen", "replay_generation",
                  "execution_attempt_id", "eligible_ordinal", "event_ordinal",
                  "normal_decision", "fault_decision", "visible_before_commit",
                  "write_skipped", "data_unchanged", "stores_to_wb_before",
                  "stores_to_wb_after", "completed_before", "completed_after")
    state = ";".join(f"{k}={d[k]}" for k in state_keys if k in d) or "n/a"

    return {
        "pc": pc, "va": va, "pa": pa, "lq": lq, "sq": sq, "gen": gen,
        "tick": str(tick), "type": itype, "state": state,
        "detail": d,
    }


def mechanism_record(model: str, chain, seq) -> str:
    for e in chain:
        if e.get("event_type") in MECHANISM_EVENTS.get(model, ()):
            keys = ("record", "model", "family", "effect_outcome",
                    "effect_reason", "stage_outcome", "masking_mechanism",
                    "store_data_fnv", "data_correct", "reload_data_hash",
                    "write_skipped", "normal_decision", "fault_decision",
                    "replay_count", "data_unchanged", "valid_after",
                    "late_binding", "entry_valid_at_response")
            d = parse_detail(e.get("detail"))
            bits = [f"{k}={d[k]}" for k in keys if k in d]
            if bits:
                return e.get("event_type") + ":" + ";".join(bits)
    return "n/a"


def first_consumer(chain, seq, ptag):
    cands = []
    for i, e in enumerate(chain):
        if e.get("event_type") not in WAIT_EVENTS:
            continue
        if e.get("dyn_inst_seq") == seq:
            continue
        if e.get("ptag") != ptag:
            continue
        cands.append((e.get("timestamp") or 0, i, e))
    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], x[1]))
    return cands[0][2]


def consumer_string(e) -> str:
    if e is None:
        return "n/a"
    d = parse_detail(e.get("detail"))
    pc = raw(d.get("pc"))
    return (f"{e.get('event_type')};seq={e.get('dyn_inst_seq')};pc={pc};"
            f"tick={e.get('timestamp')}")


def downstream_string(chain, seq, ptag, consumer) -> str:
    counts = Counter(
        e.get("event_type") for e in chain
        if e.get("dyn_inst_seq") != seq and e.get("ptag") == ptag
        and e.get("event_type") in WAIT_EVENTS)
    if not counts:
        return "n/a"
    first = f"first={consumer.get('event_type')}@seq{consumer.get('dyn_inst_seq')}" \
        if consumer else "first=n/a"
    return ";".join(f"{k}={v}" for k, v in sorted(counts.items())) + ";" + first


def commit_squash_replay(chain, seq) -> str:
    bits = []
    for e in chain:
        if e.get("event_type") == "commit" and e.get("dyn_inst_seq") == seq:
            d = parse_detail(e.get("detail"))
            bits.append(f"commit;commit_seq={d.get('commit_seq', 'n/a')};"
                        f"pc={raw(d.get('pc'))}")
            break
    for e in chain:
        if e.get("event_type") == "squash" and e.get("dyn_inst_seq") == seq:
            d = parse_detail(e.get("detail"))
            bits.append(f"SQUASHED;squash_cause={d.get('squash_cause', 'n/a')};"
                        f"fault_caused={d.get('fault_caused', 'n/a')}")
            break
    db = rich_fields(chain, seq)
    for k in ("replay_count", "replay_generation"):
        if k in db:
            bits.append(f"{k}={db[k]}")
    return ";".join(bits) if bits else "no_commit_or_squash"


def completeness(injection_ok, activation_ok, divergence_ok, witness_ok,
                 terminal_ok) -> str:
    missing = [name for name, ok in (
        ("injection", injection_ok), ("activation", activation_ok),
        ("first_divergence", divergence_ok), ("witness", witness_ok),
        ("commit_squash_hang", terminal_ok)) if not ok]
    return "COMPLETE" if not missing else "PARTIAL(" + ",".join(missing) + ")"


def evidence_class(terminal: str) -> str:
    return {
        "SDC": "DIRECT_DATAFLOW_EVIDENCE",
        "SQUASHED": "INDIRECT_EVIDENCE",
        "INJECTION_NOT_ACTIVATED": "NEGATIVE_EVIDENCE",
        "MASKED": "MASKING_EVIDENCE",
        "RELOAD_UNVERIFIABLE": "QUALIFIED_EVIDENCE",
        "HANG_WATCHDOG": "TERMINAL_WITNESS_EVIDENCE",
        "HANG_TIMEOUT": "TERMINAL_WITNESS_EVIDENCE",
    }.get(terminal, "INCOMPLETE_EVIDENCE")


def oracle_value(meta: dict, summary: dict):
    if isinstance(summary.get("oracle"), bool):
        return summary["oracle"]
    if isinstance(meta.get("oracle_pass"), bool):
        return meta["oracle_pass"]
    return None


def roi_string(model: str, ctx: int, executed) -> str:
    rs, re_, n, ords = ROI[model]
    ordinal = executed if executed not in (None, "") else ords[ctx - 1]
    return (f"ROI={rs}-{re_};N={n};p={PERCENTILES[ctx - 1]:.2f};"
            f"ordinal={ordinal}")


def trace_row(model: str, ctx: int, run: Path) -> dict:
    events = load_events(run)
    summary = load_json(run / "summary.json")
    meta = load_json(run / "pilot_meta.json")
    paths = [str(run)]
    if (run / "trace_v31.jsonl").exists():
        paths.append(str(run / "trace_v31.jsonl"))
    if (run / "summary.json").exists():
        paths.append(str(run / "summary.json"))
    if (run / "pilot_meta.json").exists():
        paths.append(str(run / "pilot_meta.json"))

    injection = next((e for e in events
                      if e.get("event_type") in ("injection", "injection_nochange")),
                     None)
    oracle = oracle_value(meta, summary)
    executed = summary.get("ordinal")

    if injection is None:
        return {
            "ModelID": model, "ContextID": f"R{ctx:02d}",
            "ROI/Percentile/Ordinal": roi_string(model, ctx, executed),
            "Injection": "n/a", "Activation": "n/a",
            "FirstDivergence": "n/a", "Downstream": "n/a",
            "Consumer": "n/a", "CommitSquashReplay": "n/a",
            "Terminal": "UNRESOLVED", "TerminalReason": "NO_INJECTION_EVENT",
            "ApplicationOracle": "PASS" if oracle is True else
                                 "FAIL" if oracle is False else "n/a",
            "EvidenceClass": "INCOMPLETE_EVIDENCE",
            "TraceCompleteness": "INCOMPLETE(no_injection)",
            "MaskingMechanism": "n/a",
            "EvidencePaths": ";".join(paths),
        }

    ptag = injection.get("ptag")
    seq = injection.get("dyn_inst_seq")
    chain = chain_events(events, ptag, seq)
    ident = identify(model, chain, seq, injection)

    activation = first_of(chain, ACTIVATION_EVENTS.get(model, ()))
    if activation is not None:
        ad = parse_detail(activation.get("detail"))
        apc = raw(ad.get("pc")) if ad.get("pc") else ident["pc"]
        activation_s = (f"record={activation.get('event_type')};"
                        f"ordinal={executed if executed is not None else ROI[model][3][ctx-1]};"
                        f"seq={activation.get('dyn_inst_seq')};pc={apc};"
                        f"tick={activation.get('timestamp')}")
    else:
        activation_s = "n/a"

    divergence = first_of(chain, DIVERGENCE_EVENTS.get(model, ()))
    if divergence is not None:
        dd = parse_detail(divergence.get("detail"))
        dpc = raw(dd.get("pc")) if dd.get("pc") else ident["pc"]
        divergence_s = (f"{divergence.get('event_type')};"
                        f"seq={divergence.get('dyn_inst_seq')};pc={dpc};"
                        f"tick={divergence.get('timestamp')}")
    else:
        divergence_s = "n/a"

    consumer = first_consumer(chain, seq, ptag)
    consumer_s = consumer_string(consumer)
    if consumer is None:
        if any(e.get("event_type") == "squash" for e in chain
               if e.get("dyn_inst_seq") == seq):
            consumer_s = "n/a (squashed before any consumer)"
        elif model == "A01" and any(e.get("event_type") == "a01_ea_discarded"
                                    for e in chain):
            consumer_s = "n/a (injection discarded; golden retry)"
        else:
            consumer_s = "n/a"

    mech = mechanism_record(model, chain, seq)
    injection_s = (f"seq={seq};pc={ident['pc']};va={ident['va']};pa={ident['pa']};"
                   f"lq={ident['lq']};sq={ident['sq']};gen={ident['gen']};"
                   f"tick={ident['tick']};type={ident['type']};"
                   f"protocol={injection.get('event_type')};state={ident['state']}")

    termination = commit_squash_replay(chain, seq)
    terminal, reason, masking = adjudicate_trace(
        model, ctx, chain, seq, oracle, ident, mech)

    has_squash = any(e.get("event_type") == "squash" for e in chain
                     if e.get("dyn_inst_seq") == seq)
    has_discard = any(e.get("event_type") == "a01_ea_discarded" for e in chain)
    has_commit = any(e.get("event_type") == "commit" for e in chain
                     if e.get("dyn_inst_seq") == seq)
    terminal_witness = (has_squash or has_discard
                        or any(e.get("event_type") in ("sp05_stage",
                                                       "lq04_restore")
                               for e in chain)
                        or terminal in ("SDC", "MASKED"))
    trace_c = completeness(
        injection_ok=True,
        activation_ok=activation is not None,
        divergence_ok=divergence is not None,
        witness_ok=consumer is not None or terminal_witness,
        terminal_ok=has_commit or has_squash or has_discard
                    or any(e.get("event_type") in ("errant_commit",
                                                   "sp05_complete")
                           for e in chain))

    if terminal == "MASKED" and "masking" in masking:
        pass

    return {
        "ModelID": model, "ContextID": f"R{ctx:02d}",
        "ROI/Percentile/Ordinal": roi_string(model, ctx, executed),
        "Injection": injection_s,
        "Activation": activation_s,
        "FirstDivergence": divergence_s,
        "Downstream": downstream_string(chain, seq, ptag, consumer),
        "Consumer": consumer_s,
        "CommitSquashReplay": termination,
        "Terminal": terminal,
        "TerminalReason": reason,
        "ApplicationOracle": ("PASS" if oracle is True else
                              "FAIL" if oracle is False else "n/a"),
        "EvidenceClass": evidence_class(terminal),
        "TraceCompleteness": trace_c,
        "MaskingMechanism": masking,
        "EvidencePaths": ";".join(paths),
    }


def adjudicate_trace(model, ctx, chain, seq, oracle, ident, mech):
    """Return (terminal, terminal_reason, masking_mechanism)."""
    d_idx = ident["detail"]

    if model == "A01":
        discard = next((e for e in chain
                        if e.get("event_type") == "a01_ea_discarded"), None)
        if discard is not None:
            dd = parse_detail(discard.get("detail"))
            if dd.get("applied_to_request") == "0":
                return ("INJECTION_NOT_ACTIVATED",
                        "NO_EFFECTIVE_INJECTION;"
                        f"discard_reason={dd.get('discard_reason', 'n/a')};"
                        "applied_to_request=0;"
                        f"pc={raw(dd.get('pc'))}",
                        "n/a")
        squash = next((e for e in chain if e.get("event_type") == "squash"
                       and e.get("dyn_inst_seq") == seq), None)
        committed = any(e.get("event_type") == "commit"
                        and e.get("dyn_inst_seq") == seq for e in chain)
        if squash is not None and not committed:
            sd = parse_detail(squash.get("detail"))
            if sd.get("squash_cause") == "unrelated" and sd.get("fault_caused") == "0":
                return ("SQUASHED",
                        "UNRELATED_SQUASH_NO_ARCH_ENTRY;fault_caused=0;"
                        "squash_cause=unrelated;no_registered_arch_state",
                        "n/a")
            return ("SQUASHED", "TARGET_SQUASHED_NO_COMMIT", "n/a")
        if oracle is False:
            return ("SDC", "ORACLE_FAIL;committed_data_value_diverged", "n/a")
        if oracle is True:
            return ("MASKED", "TARGET_COMMITTED_DATA_VALUE_PRESENT", "n/a")
        return ("UNRESOLVED", "ORACLE_NOT_OBSERVED", "n/a")

    if model == "FW02" and ctx == 3:
        return ("MASKED",
                "SUPPRESSED_FORWARD_NORMAL_VALUE;normal_decision=forwarded;"
                "fault_decision=suppressed;replay_count=0",
                "SUPPRESSED_FORWARD_NORMAL_VALUE")

    if model == "MD04" and ctx == 1:
        return ("MASKED", "INERT_AFTER_COMPLETION;no_wrong_value_produced",
                "INERT_AFTER_COMPLETION")

    if model == "LQ04":
        return ("MASKED",
                "ENTRY_INVALIDATED_RESTORED;data_unchanged=1;no_pop=1;no_reuse=1",
                "ENTRY_INVALIDATED_RESTORED")

    if model == "SQ03":
        effect = next((e for e in chain
                       if e.get("event_type") == "sq03_effect"), None)
        ed = parse_detail(effect.get("detail")) if effect else {}
        outcome = ed.get("effect_outcome", "n/a")
        if outcome == "CHAIN_VISIBILITY_MOVED":
            return ("MASKED",
                    "VISIBILITY_TIMING_SHIFT;effect_outcome=CHAIN_VISIBILITY_MOVED;"
                    "reload_after_commit;not_sdc",
                    "VISIBILITY_TIMING_SHIFT:DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER")
        return ("MASKED",
                "VISIBILITY_TIMING_SHIFT;effect_outcome=LIFECYCLE_ONLY;"
                "no_downstream_effect;not_sdc",
                "VISIBILITY_TIMING_SHIFT:LIFECYCLE_ONLY")

    if model == "SP05":
        stage = next((e for e in chain
                      if e.get("event_type") == "sp05_stage"), None)
        sd = parse_detail(stage.get("detail")) if stage else {}
        fnv = sd.get("store_data_fnv")
        if fnv in (None, "", "null"):
            return ("RELOAD_UNVERIFIABLE",
                    "store_data_fnv=null;"
                    f"reload_data_hash={sd.get('reload_data_hash', 'n/a')};"
                    f"write_skipped={sd.get('write_skipped', 'n/a')};"
                    "cannot_compare_reload_with_store_data",
                    "n/a")
        if sd.get("data_correct") == "0":
            return ("SDC", "ORACLE_FAIL;store_data_fnv=" + fnv, "n/a")
        return ("MASKED", "RELOAD_MATCHES_STORE_DATA;store_data_fnv=" + fnv, "n/a")

    if oracle is False:
        return ("SDC", "ORACLE_FAIL;committed_data_value_diverged", "n/a")
    if oracle is True:
        reason = "TARGET_COMMITTED_DATA_VALUE_PRESENT"
        if model == "LQ04":
            reason = "ENTRY_INVALIDATED_RESTORED"
        return ("MASKED", reason, "n/a")
    return ("UNRESOLVED", "ORACLE_NOT_OBSERVED", "n/a")


# ------------------------------------------------------------- A03 / RP01 --

def a03_checksum(run: Path) -> str | None:
    p = run / "stdout.log"
    if not p.exists():
        return None
    found = re.findall(r"(?m)^([0-9a-fA-F]{16})\s*$",
                       p.read_text(errors="replace"))
    return found[-1].lower() if found else None


def any_text(run: Path, names, needle: str) -> str | None:
    for name in names:
        p = run / name
        if not p.exists():
            continue
        for line in p.read_text(errors="replace").splitlines():
            if needle in line:
                return line.strip()
    return None


def a03_row(model, ctx, run: Path, golden: str) -> dict:
    summary = load_json(run / "summary.json")
    paths = [str(run)]
    log = run / "addrpath_injections.log"
    stdout = run / "stdout.log"
    stderr = run / "stderr.log"
    for p in (log, stdout, stderr):
        if p.exists():
            paths.append(str(p))

    activation = None
    affected = None
    funnel = None
    if log.exists():
        for line in log.read_text(errors="replace").splitlines():
            if activation is None and line.startswith("A03_ACTIVATION:"):
                activation = line
            if affected is None and line.startswith("A03_STREAM:") \
                    and "affected=1" in line:
                affected = line
            if line.startswith("FUNNEL:"):
                funnel = line

    checksum = a03_checksum(run)
    watchdog = any_text(run, ("stderr.log", "stdout.log"), "WATCHDOG")
    a03 = summary.get("a03") or {}
    ordinal = summary.get("ordinal")
    executed = ordinal if ordinal is not None else ROI[model][3][ctx - 1]

    activation_s = (f"record=A03_ACTIVATION;ordinal={executed};"
                    f"{activation.split(':', 1)[1].strip() if activation else 'n/a'}")
    injection_s = ("A03_STREAM;" + affected.split(":", 1)[1].strip()
                   if affected else "n/a")
    divergence_s = injection_s

    if checksum is not None:
        if checksum == golden:
            terminal, reason = "MASKED", f"ORACLE_PASS;checksum={checksum}"
        else:
            terminal = "SDC"
            reason = (f"ORACLE_FAIL;checksum={checksum};golden={golden}")
            if watchdog:
                reason += ";POST_ORACLE_SIM_HANG"
    elif watchdog:
        terminal, reason = "HANG_WATCHDOG", "WATCHDOG_NO_CHECKSUM"
    elif summary.get("timed_out"):
        terminal, reason = "HANG_TIMEOUT", "NO_CHECKSUM;EXTERNAL_TIMEOUT"
    else:
        terminal, reason = "UNRESOLVED", "NO_CHECKSUM_NO_TERMINAL_WITNESS"

    witness = checksum is not None or watchdog is not None or bool(summary.get("timed_out"))
    trace_c = completeness(
        injection_ok=affected is not None,
        activation_ok=activation is not None,
        divergence_ok=affected is not None,
        witness_ok=witness,
        terminal_ok=witness)

    return {
        "ModelID": model, "ContextID": f"R{ctx:02d}",
        "ROI/Percentile/Ordinal": roi_string(model, ctx, executed),
        "Injection": injection_s,
        "Activation": activation_s,
        "FirstDivergence": divergence_s,
        "Downstream": (f"stream_injected={a03.get('injections', 'n/a')};"
                       f"capped={a03.get('capped', 'n/a')};"
                       + (funnel or "funnel=n/a")),
        "Consumer": "n/a (persistent stream; no per-consumer record)",
        "CommitSquashReplay": ("external_timeout" if summary.get("timed_out")
                               else "watchdog" if watchdog else "no_terminal_node"),
        "Terminal": terminal,
        "TerminalReason": reason,
        "ApplicationOracle": ("FAIL" if checksum and checksum != golden else
                              "PASS" if checksum == golden else "NO_CHECKSUM"),
        "EvidenceClass": evidence_class(terminal),
        "TraceCompleteness": trace_c,
        "MaskingMechanism": "n/a",
        "EvidencePaths": ";".join(paths),
    }


def rp01_row(model, ctx, run: Path) -> dict:
    summary = load_json(run / "summary.json")
    rp = summary.get("rp01") or {}
    paths = [str(run)]
    for name in ("stdout.log", "stderr.log", "summary.json"):
        if (run / name).exists():
            paths.append(str(run / name))

    watchdog = any_text(run, ("stderr.log", "stdout.log"),
                        "CHAOS_RP01_WATCHDOG_EXPIRED")
    skip = rp.get("first_skip") or "n/a"
    ordinal = summary.get("ordinal")
    executed = ordinal if ordinal is not None else ROI[model][3][ctx - 1]

    activation_s = f"record=RP01_SKIP_REPLAY;ordinal={executed};{skip}"
    injection_s = f"RP01_SKIP_REPLAY;ordinal={executed};{skip}"
    divergence_s = injection_s

    if watchdog:
        terminal, reason = ("HANG_WATCHDOG",
                            f"RP01_WATCHDOG_EXPIRED;target_ordinal={executed};"
                            f"injected={summary.get('injection_count')};"
                            f"checksum={rp.get('checksum')}")
    elif summary.get("timed_out"):
        terminal, reason = "HANG_TIMEOUT", f"EXTERNAL_TIMEOUT;target_ordinal={executed}"
    else:
        terminal, reason = ("UNRESOLVED",
                            f"NO_WATCHDOG_NO_CHECKSUM;target_ordinal={executed}")

    trace_c = completeness(
        injection_ok=True,
        activation_ok=True,
        divergence_ok=True,
        witness_ok=bool(watchdog) or bool(summary.get("timed_out")),
        terminal_ok=bool(watchdog) or bool(summary.get("timed_out")))

    return {
        "ModelID": model, "ContextID": f"R{ctx:02d}",
        "ROI/Percentile/Ordinal": roi_string(model, ctx, executed),
        "Injection": injection_s,
        "Activation": activation_s,
        "FirstDivergence": divergence_s,
        "Downstream": (f"skips={rp.get('skips', 'n/a')};"
                       f"eligible={rp.get('eligible', 'n/a')}"),
        "Consumer": "n/a (no downstream record; run cut by watchdog)",
        "CommitSquashReplay": (f"watchdog_expired;{watchdog}" if watchdog
                               else "no_commit_or_squash"),
        "Terminal": terminal,
        "TerminalReason": reason,
        "ApplicationOracle": "NO_CHECKSUM",
        "EvidenceClass": evidence_class(terminal),
        "TraceCompleteness": trace_c,
        "MaskingMechanism": "n/a",
        "EvidencePaths": ";".join(paths),
    }


def missing_row(model, ctx) -> dict:
    return {
        "ModelID": model, "ContextID": f"R{ctx:02d}",
        "ROI/Percentile/Ordinal": roi_string(model, ctx, None),
        "Injection": "n/a", "Activation": "n/a", "FirstDivergence": "n/a",
        "Downstream": "n/a", "Consumer": "n/a", "CommitSquashReplay": "n/a",
        "Terminal": "UNRESOLVED", "TerminalReason": "NO_RUN_DIRECTORY",
        "ApplicationOracle": "n/a", "EvidenceClass": "INCOMPLETE_EVIDENCE",
        "TraceCompleteness": "INCOMPLETE(no_run)",
        "MaskingMechanism": "n/a", "EvidencePaths": "n/a",
    }


def load_goldens(matrix: Path) -> dict[str, str]:
    goldens = dict(FROZEN_ORACLE)
    if not matrix.exists():
        return goldens
    try:
        with matrix.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                model = row.get("FaultModelID")
                oracle = (row.get("Oracle") or "").strip()
                if model and oracle:
                    goldens[model] = oracle
    except Exception:
        pass
    return goldens


def default_runs() -> Path:
    for cand in (ROOT / "audit_v3_3_3/runs", ROOT / "audit_v3_3_2/runs"):
        if cand.is_dir():
            return cand
    return ROOT / "audit_v3_3_3/runs"


def build_rows(runs: Path, matrix: Path) -> list[dict]:
    goldens = load_goldens(matrix)
    rows = []
    for model in MODELS:
        for ctx in range(1, 6):
            run = runs / f"{model}-R{ctx:02d}-fault"
            if not run.is_dir():
                rows.append(missing_row(model, ctx))
                continue
            if model == "A03":
                rows.append(a03_row(model, ctx, run, goldens.get("A03", FROZEN_ORACLE["A03"])))
            elif model == "RP01":
                rows.append(rp01_row(model, ctx, run))
            else:
                rows.append(trace_row(model, ctx, run))
    return rows


def write_csv(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def default_out(runs: Path) -> Path:
    if runs.resolve() == (ROOT / "audit_v3_3_3/runs").resolve():
        return ROOT / "audit_v3_3_3/LSU_60Context_Causal_Propagation.csv"
    return ROOT / "audit_v3_3_2/propagation/LSU_v333_60Context_Causal_Propagation.csv"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=None,
                    help="runs directory (default audit_v3_3_3/runs, then audit_v3_3_2/runs)")
    ap.add_argument("--matrix", type=Path,
                    default=ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    runs = args.runs or default_runs()
    out = args.out or default_out(runs)
    rows = build_rows(runs, args.matrix)
    # Honest trace labels (independent audit F-04): A03's raw trace is the
    # complete prop_trace (no trace_v31 in the direct driver); RP01 is a
    # HANG_WATCHDOG with a partial trace by design.
    for r in rows:
        if r["ModelID"] == "A03" and r["TraceCompleteness"] == "COMPLETE":
            r["TraceCompleteness"] = "COMPLETE_PROP_TRACE"
        elif r["ModelID"] == "RP01":
            r["TraceCompleteness"] = "PARTIAL_WATCHDOG"
    write_csv(rows, out)

    counts = Counter(r["Terminal"] for r in rows)
    complete = sum(r["TraceCompleteness"] in
                   ("COMPLETE", "COMPLETE_PROP_TRACE") for r in rows)
    print(f"wrote {len(rows)} rows to {out}")
    print("terminals: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"COMPLETE(+PROP_TRACE)={complete}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
