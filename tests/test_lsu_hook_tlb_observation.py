#!/usr/bin/env python3
"""Static contract for T-series post-lookup/translation evidence.

This test deliberately inspects the C++ source: it must fail before the
observation hooks exist, and it remains runnable without rebuilding gem5.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARM_CC = (ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc").read_text()
ARM_HH = (ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh").read_text()
PROP_CC = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc").read_text()
PROP_HH = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh").read_text()
MMU_CC = (ROOT / "CHAOS/gem5/src/arch/arm/mmu.cc").read_text()

failed = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name
          + ("" if condition or not detail else f"  [{detail}]"))
    if not condition:
        failed.append(name)


def main():
    check("post-lookup kind emitted", 'notePropEvt("tlb_lookup"' in PROP_CC)
    check("post-translation kind emitted",
          'notePropEvt("tlb_translate_result"' in PROP_CC)
    check("translation result is emitted from the MMU completion path",
          "noteTlbTranslationResult" in MMU_CC
          and "noteTlbTranslationResult" in PROP_HH)
    check("lookup only records pending translation state",
          "tlb_pending" in PROP_HH and "tlb_pending" in PROP_CC)
    check("observation API declared",
          "entry_before" in PROP_HH and "candidate_way" in PROP_HH
          and "walk_id" in PROP_HH)
    check("Arm hook captures deterministic entry index",
          "entryIndex(" in ARM_CC and "entry_way" in ARM_CC)
    check("Arm hook snapshots all required entry fields",
          all(token in ARM_CC for token in (
              'vpn=', 'asid=', 'valid=', 'global=',
              'pfn=', 'ap=', 'mtype=', 'page_size=')))
    check("snapshot payload crosses Arm/propagation boundary",
          "entry_before" in ARM_HH and "entry_after" in ARM_HH)
    check("lookup carries identity and selection fields",
          all(token in PROP_CC for token in (
              '{"request_id", std::to_string(req_seq)}',
              '{"walk_id", std::to_string(walk_id)}',
              '{"entry_index", std::to_string(entry_way)}',
              '{"way", std::to_string(candidate_way)}')))
    check("lookup carries complete before/after snapshot",
          '{"state_before", entry_before}' in PROP_CC
          and '{"state_after", entry_after}' in PROP_CC)
    check("translation result records effective PA before/after",
          '{"before", h_before.str()}' in PROP_CC
          and '{"after", h_after.str()}' in PROP_CC)
    check("unchanged effective PA has explicit containment",
          "effective_pa_unchanged" in PROP_CC
          and "translation_blocked" in PROP_CC
          and '{"detection_layer", contained ? "L2" : ""}' in PROP_CC
          and '{"contained", contained ? "1" : "0"}' in PROP_CC)
    check("T05-T07 state/CAM path carries complete entry snapshots",
          "registerTlbStateFault(req_seq" in ARM_CC
          and "state_before, state_after" in ARM_CC
          and "entry_way, candidate_way" in ARM_CC)
    check("T08 lost walk emits explicit translation blocking",
          "walk_refill_lost" in PROP_CC
          and "translation_blocked" in PROP_CC)
    check("fault correlation remains explicit",
          "CORR_SEQ_PRIMARY" in PROP_CC and "CORR_ADDR_FALLBACK" in PROP_CC)
    check("parent-event chain is supplied by unified emitter",
          "ptag_last_event" in PROP_CC and "parent_event_id" in PROP_HH)

    # --- [R6-A] L2 payload must ride REGISTERED PROP-EVT fields ---------------
    # notePropEvt DROPS any key outside PROP_EVT_FIELDS (CHAOSPropagation.cc
    # "unknown field ... dropped"). 'fault' and 'detail' are NOT registered,
    # so the L2 Fault and the containment reason were emitted into the void
    # (invisible in the pilot stream). The fault name must ride 'outcome'
    # (the tlb_fault convention) and the reason must ride a registered field.
    check("L2 translate result carries the Fault in a registered field",
          '"fault", fault_name' not in PROP_CC
          and '{"outcome", fault_name}' in PROP_CC)
    # The L2 disposition vocabulary ("effective_pa_unchanged" /
    # "translation_blocked" / "walk_refill_lost") must ride a REGISTERED
    # field (`field`), never an unregistered bespoke key that notePropEvt
    # would drop. The value is held in `field_reason`; the containment-only
    # projection of it is `reason` (empty when the fault was NOT contained,
    # so an escaped chain can never claim a containment reason).
    check("L2 containment reason rides a registered field, not dropped 'detail'",
          '{"detail", detail}' not in PROP_CC
          and '{"field", field_reason}' in PROP_CC
          and '{"containment_reason", reason}' in PROP_CC)
    check("walk-lost L2 node also uses registered fields",
          '"fault", "translation_blocked"' not in PROP_CC
          and '"field", "walk_refill_lost"' in PROP_CC)
    # --- [R6-B] non-lost walk (T08-b/c/d) still gets a real L2 result --------
    # A completed walk is followed by a real MMU translation completion; the
    # pending lookup must therefore be registered for it too (only the lost
    # walk closes itself early). Without this the T08-b/c/d chain has no L2
    # real-PA/Fault node at all.
    check("non-lost walk registers a pending lookup for the real L2 result",
          PROP_CC.count("tlb_pending[{req_seq, va}] = TlbPending{") >= 3)
    check("walk-fault completion reports an honest, non-fabricated reason",
          "walk_result_reported" in PROP_CC)

    # --- [R6-A2] T-series observe events must ride REGISTERED fields ----------
    # notePropEvt drops any kv key outside PROP_EVT_FIELDS (it warns once and
    # continues). A key that is not registered is therefore INVISIBLE in the
    # pilot stream and in the offline chain checker, so a contract that only
    # greps for the key name in the source proves nothing about the evidence.
    # Parse the registry out of the header and require every key of every
    # T-series observation event to be a member.
    def _registry(which="PROP_EVT_FIELDS"):
        start = PROP_HH.index(which + "[] = {")
        end = PROP_HH.index("};", start)
        return set(re.findall(r'"([a-z_]+)"', PROP_HH[start:end]))

    # The emittable registry is the shared PROP_EVT_FIELDS registry UNION the
    # family-extension registry (containment_layer/_reason). The TLB family
    # deliberately keeps its disposition keys OUT of the shared registry
    # (tools/lsu_prop_fields.py mirrors that one 1:1 and is pinned equal by
    # tests/test_lsu_prop_fields.py), but notePropEvt DOES emit the extension
    # keys — so an ext key is registered evidence, not a dropped key. The
    # separation itself is asserted below so a future drift that puts the
    # containment keys into both arrays is caught.
    reg_shared = _registry()
    reg_ext = _registry("PROP_EVT_EXT_FIELDS")
    reg = reg_shared | reg_ext
    check("family-extension registry parsed (self-check)",
          {"containment_layer", "containment_reason"} <= reg_ext)
    check("family-extension keys stay OUT of the shared registry",
          not ({"containment_layer", "containment_reason"} & reg_shared))

    def _kv_blocks(kind):
        """Every notePropEvt("<kind>", {...}) body, brace-matched."""
        blocks = []
        pat = 'notePropEvt("' + kind + '"'
        pos = 0
        while True:
            i = PROP_CC.find(pat, pos)
            if i < 0:
                break
            j = PROP_CC.index("{", i)
            depth = 0
            for k in range(j, len(PROP_CC)):
                if PROP_CC[k] == "{":
                    depth += 1
                elif PROP_CC[k] == "}":
                    depth -= 1
                    if depth == 0:
                        blocks.append(PROP_CC[j:k + 1])
                        break
            pos = j + 1
        return blocks

    # `reg` (shared ∪ extension, defined above) is the emittable set: a key
    # is only "registered" if some registry array contains it. Shared-only
    # keys are still exercised here so the parse itself is verified.
    check("registry parsed from the header (self-check)",
          {"kind", "fault_id", "outcome", "state_before"} <= reg_shared
          and reg_shared <= reg)

    tlb_obs_kinds = ("tlb_lookup", "tlb_translate_result")
    obs_blocks = {k: _kv_blocks(k) for k in tlb_obs_kinds}
    check("both T-series observation kinds are emitted",
          all(obs_blocks[k] for k in tlb_obs_kinds))
    bad_keys = {
        k: sorted({m for b in blocks for m in re.findall(r'\{"([^"]+)"', b)}
                  - reg)
        for k, blocks in obs_blocks.items()
    }
    check("T-series observe events use only registered PROP-EVT fields",
          not any(bad_keys.values()), str(bad_keys))

    # --- [R6-A3] L1 payload must carry the full entry state it claims ---------
    l1_keys = {'fault_id', 'corr', 'dyn_inst_seq', 'request_id', 'walk_id',
               'va', 'entry_index', 'way', 'field', 'state_before',
               'state_after'}
    for i, b in enumerate(obs_blocks["tlb_lookup"]):
        keys = set(re.findall(r'\{"([^"]+)"', b))
        check(f"tlb_lookup #{i + 1} carries entry/way + request identity",
              l1_keys <= keys, str(sorted(l1_keys - keys)))

    # --- [R6-A4] L2 payload must expose the effective PA *and* the Fault ------
    l2_keys = {'fault_id', 'corr', 'dyn_inst_seq', 'request_id', 'walk_id',
               'va', 'pa', 'entry_index', 'way', 'field', 'before', 'after',
               'state_before', 'state_after', 'outcome', 'detection_layer',
               'contained'}
    for i, b in enumerate(obs_blocks["tlb_translate_result"]):
        keys = set(re.findall(r'\{"([^"]+)"', b))
        check(f"tlb_translate_result #{i + 1} carries PA + Fault + containment",
              l2_keys <= keys, str(sorted(l2_keys - keys)))

    # --- [R6-A5] L5 must be a REAL per-chain outcome, not a lifecycle mark ---
    # The exit callback used to hard-code seen_errant=false for the whole run,
    # so every chain ended on the bare lifecycle marker
    # (outcome=run_end / detection_layer=None / contained=0 / corr=none). The
    # family-aware chain checker rejects exactly that node as L5 evidence and
    # then reports provable_to_L4_then_unknown, i.e. the T-series chain can
    # never be complete no matter how real its L0..L4 nodes are. The errant
    # commit IS observable per chain (the node carries the fault's ptag), so
    # the L5 node must report it for the chain that actually has it.
    check("errant commit is recorded per chain (not as a run-global flag)",
          "errant_ptags" in PROP_HH and "errant_ptags.insert(ptag)" in PROP_CC)
    check("chain_end reports the per-chain errant commit as its outcome",
          "errant_ptags.count(ptag)" in PROP_CC
          and "const bool seen_errant = false;" not in PROP_CC)

    # --- [R6-C] GAP-1: L0 `inj` must record the injection AND its before/after
    # Measured on runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1: the L0 node read
    #   kind=inj ... field=pfn_to_mapped_page before= after=
    # — the injection was named but it could not say WHAT it changed. The T04
    # path builds its detail from old_pfn/new_pfn, keys the unified emitter
    # does NOT lift (it lifts old_addr/new_addr -> before/after, and
    # registerStoreSetFault already uses that convention). An L0 that cannot
    # say before/after is not evidence that an injection happened.
    inj_obs = _kv_blocks("inj")
    check("T-series notePropEvt inj nodes are present", len(inj_obs) >= 2)
    for i, b in enumerate(inj_obs):
        keys = set(re.findall(r'\{"([^"]+)"', b))
        check(f"inj #{i + 1} carries an explicit before/after",
              {"before", "after"} <= keys,
              str(sorted({"before", "after"} - keys)))
    # The T04 pfn inj node is the v1-CSV `inj` (writeNode), whose detail is
    # dual-emitted with the documented lift old_addr/new_addr → before/after.
    # Anchor on the pfn arm's detail builder (unique) and require BOTH lift
    # keys in the same detail string.
    t04 = PROP_CC.find('d << "family=tlb;field=" << mode')
    t04_win = PROP_CC[t04:t04 + 900] if t04 >= 0 else ""
    check("T04 pfn inj detail lifts before/after via old_addr/new_addr",
          t04 >= 0 and ";old_addr=" in t04_win and ";new_addr=" in t04_win)

    # --- [R6-C] GAP-2: L5 evidence must be the REAL detection event ----------
    # Measured: kind=errant_commit corr=taint_prop dyn_inst_seq=391 with EMPTY
    # detection_layer= and outcome=. The errant commit IS the observable
    # detection (the wrong value reached architectural state), so it must name
    # its layer and outcome, and a lifecycle chain_end must never be the ONLY
    # L5 evidence.
    ec = PROP_CC.find('writeNode(ptag, "errant_commit"')
    check("errant_commit emission located", ec >= 0)
    ec_win = PROP_CC[max(0, ec - 1500):ec + 200] if ec >= 0 else ""
    check("errant_commit names its detection layer (the real L5 event)",
          "detection_layer=L5" in ec_win)
    check("errant_commit names its outcome", "outcome=" in ec_win)

    # --- [R6-C] containment must be explicit, never "Unknown" ----------------
    # Unchanged-PA (Masked) / permission-denied / lost-walk chains must close
    # with an explicit containment_layer + containment_reason and justify the
    # later layers N/A(contained) — otherwise the chain checker can only report
    # provable_to_Ln_then_unknown (beyond="Unknown").
    check("containment registry fields exist",
          '"containment_layer"' in PROP_HH and '"containment_reason"' in PROP_HH)
    check("containment rides the contained-L2 outcome path",
          '{"containment_layer"' in PROP_CC
          and '{"containment_reason", reason}' in PROP_CC)
    check("no layer/outcome is ever emitted as Unknown", "=Unknown" not in PROP_CC)
    check("contained chains close chain_end with a real detection layer",
          "containment_ptags" in PROP_HH and "containment_ptags" in PROP_CC
          and '{"detection_layer", "None"}' not in PROP_CC)
    check("Masked (effective PA unchanged) records its containment reason",
          "effective_pa_unchanged" in PROP_CC
          and '{"containment_reason", reason}' in PROP_CC)

    # --- [R6-D/A4] L4 taint_reg must say the taint transition it records ----
    # Measured: kind=taint_reg ... before= after= (the load dest phys reg
    # entered the taint set but the node did not say the cell's taint state
    # changed). The v1-CSV node is dual-emitted, so the pair must ride the
    # documented old_addr/new_addr → before/after lift (same mechanism as
    # registerLSQForwardFault's seq pair / registerRespPairFault's pairing).
    tr = PROP_CC.find('writeNode(hit_ptag, "taint_reg"')
    check("taint_reg emission located", tr >= 0)
    tr_win = PROP_CC[max(0, tr - 900):tr + 200] if tr >= 0 else ""
    check("taint_reg records the cell's taint transition (before/after lift)",
          ";old_addr=" in tr_win and ";new_addr=" in tr_win)

    # --- [R6-D/A10] a squashed load must not emit nothing --------------------
    # noteMemResponse early-returned on isSquashed() BEFORE any emission, so a
    # load that received the wrong response and was then squashed (result
    # discarded, replayed) produced NO node at all — a contain-by-squash event
    # could never fire and the chain looked like it silently disappeared.
    check("squashed loads emit an explicit squash containment event",
          'notePropEvt("squash_masked"' in PROP_CC)
    sq = _kv_blocks("squash_masked")
    check("squash event is emitted in the squashed branch", len(sq) >= 1)
    for i, b in enumerate(sq):
        keys = set(re.findall(r'\{"([^"]+)"', b))
        check(f"squash_masked #{i + 1} records layer/outcome/containment",
              {"outcome", "detection_layer", "contained",
               "containment_layer", "containment_reason"} <= keys,
              str(sorted({"outcome", "detection_layer", "contained",
                          "containment_layer", "containment_reason"} - keys)))
        check(f"squash_masked #{i + 1} uses only registered fields",
              not (keys - reg), str(sorted(keys - reg)))
    check("squash containment is remembered per chain",
          "containment_ptags[hit_ptag]" in PROP_CC)

    # --- [R6-D/A6] the chain must be a real DAG, not "previous event - 1" ----
    # The emitter kept ONE ptag_last_event cursor, so every event's
    # parent_event_id was simply the previous event of the chain — a linear
    # list. A consumer does not descend from the previous event: it descends
    # from the taint_reg/resp that established the taint it consumed. The
    # source event must therefore be carried on the taint entry and named
    # explicitly as the consumer's parent.
    check("taint entries carry the event that established the taint",
          "src_event" in PROP_HH and "src_event" in PROP_CC)
    check("consumer nodes name their taint source as parent_event_id",
          '";parent_event_id="' in PROP_CC)

    if failed:
        print(f"FAILED ({len(failed)}): {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
