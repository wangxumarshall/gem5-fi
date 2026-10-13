#!/usr/bin/env python3
"""[OOO][FIX-B] unit test for tools/ooo_l3.py + commit_diff.py v2 parsing.

Pins the FIX-B L3 propagation-chain contract
(docs/superpowers/plans/2026-10-13-ooo-fixB-l3-propagation.md):

  1. commit_diff parse_line: v1 rows parse as before (seqenc None); v2
     rows (with/without marker) parse with seqenc/nsrc/srcs; a line that
     fits BOTH column contracts is a loud error; a v2-marker file with a
     v1-only row is a loud error; unknown '#' lines are loud errors;
     known annotations (v2 header, squash events) are skipped.
  2. commit_diff compare(): v2 pairs classify on the v1 fields only; the
     JSON carries ref_format/run_format ONLY when v2 rows were present
     (v1-pair JSON stays key-identical).
  3. build_l3 join: the L0 event's sn finds the committed row by seqenc.
  4. BFS: real source->consumer hops via src-triple == dest-triple;
     transitive hops; the kill rule (a later redefinition of the same
     (class,phys) ends that register's match window).
  5. squash path: a squashed instruction whose src triple matches a live
     chain key is a squashed_consumer (committed=false); the injected
     source's own squash is reported (source_squashed).
  6. honest unsupported: v1 ctrace (no seqenc), L0 events without sn,
     unknown components; in-flight (never-committed, never-squashed)
     source -> status ok with zero hops and an explicit caveat.
  7. --fdc windowing: the BFS stops after the first_divergent_commit row.
  8. real L0-parser compatibility: a FIX-B decode_injections.log line
     (ending ', sn=N, faults_injected: 1') flows through the FROZEN
     tools/ooo_observation.parse_injection_log and yields rec["sn"]=N.

Plain-python asserts (repo style; pytest is not installed on this host).
Run: python3 tools/tests/test_ooo_l3.py
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools"))

import commit_diff  # noqa: E402
import ooo_l3  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


# ------------------------------------------------------------- line builders

def v2row(seq, seqenc, tick, pc, op, dests, srcs):
    """dests: [(c,a,p,val16)] ; srcs: [(c,a,p)]"""
    parts = [str(seq), str(seqenc), "0", str(tick), pc, op, str(len(dests))]
    for (c, a, p, v) in dests:
        parts += [str(c), str(a), str(p), v]
    parts.append(str(len(srcs)))
    for (c, a, p) in srcs:
        parts += [str(c), str(a), str(p)]
    return ",".join(parts)


def v1row(seq, tick, pc, op, dests):
    parts = [str(seq), "0", str(tick), pc, op, str(len(dests))]
    for (c, a, p, v) in dests:
        parts += [str(c), str(a), str(p), v]
    return ",".join(parts)


V16 = "0000000000000000"
HDR = ("# ctrace v2 seq,seqencNum,tid,tick,pc,op,ndest"
       "[,class,arch,phys,val]*,nsrc[,class,arch,phys]*")

# ---------------------------------------------------------------- 1. parsing

def test_parse_line():
    print("[1] commit_diff.parse_line v1/v2 detection")
    r1 = commit_diff.parse_line("f", 1, v1row(0, 500, "1000", "add",
                                             [(1, 2, 80, V16)]))
    check("v1 row seqenc is None", r1.seqenc is None)
    check("v1 row nsrc is None", r1.nsrc is None)
    check("v1 row dests parse", r1.dests == [(1, 2, 80, V16)])

    r2 = commit_diff.parse_line("f", 1, v2row(0, 101, 500, "1000", "add",
                                              [(1, 2, 80, V16)],
                                              [(1, 5, 79)]))
    check("v2 row seqenc", r2.seqenc == 101)
    check("v2 row nsrc", r2.nsrc == 1)
    check("v2 row srcs", r2.srcs == [(1, 5, 79)])
    check("v2 row dests parse", r2.dests == [(1, 2, 80, V16)])

    r3 = commit_diff.parse_line("f", 1, v2row(0, 101, 500, "1000", "b",
                                              [], []))
    check("v2 zero-dest zero-src row", r3.ndest == 0 and r3.nsrc == 0
          and r3.seqenc == 101)

    # src phys -1 sentinel (absent phys id)
    r4 = commit_diff.parse_line("f", 1, v2row(0, 101, 500, "1000", "b",
                                              [], [(-1, 3, -1)]))
    check("v2 src -1 sentinels", r4.srcs == [(-1, 3, -1)])

    # both-fit (a REAL v1 phenomenon — e.g. old_no_inj line 275, 14
    # cols): resolves to v1, because a genuine v2 row can never fit v1
    # (v1's ndest column is the v2 op mnemonic, never a uint).
    amb = "0,0,500,1000,add,2,0,2,0,0000000000000002,1,2,3,0000000000000004"
    ramb = commit_diff.parse_line("f", 1, amb)
    check("both-fit line parses as v1", ramb.seqenc is None
          and ramb.ndest == 2
          and ramb.dests == [(0, 2, 0, "0000000000000002"),
                             (1, 2, 3, "0000000000000004")])

    # neither fits
    try:
        commit_diff.parse_line("f", 1, "0,0,500,1000,add,2,1,2")
        check("neither-fit rejected", False)
    except commit_diff.TraceError:
        check("neither-fit rejected", True)

    # v2 marker file with a v1-only row -> loud error
    try:
        commit_diff.parse_line("f", 2, v1row(0, 500, "1000", "add",
                                             [(1, 2, 80, V16)]),
                               declared="v2")
        check("v2-file v1-row rejected", False)
    except commit_diff.TraceError as e:
        check("v2-file v1-row rejected", "声明 v2" in str(e), str(e))

    # unknown '#' annotation -> loud error; known ones pass
    try:
        commit_diff._check_annotation("f", 3, "# whatever")
        check("unknown # rejected", False)
    except commit_diff.TraceError:
        check("unknown # rejected", True)
    commit_diff._check_annotation("f", 3, HDR)
    commit_diff._check_annotation("f", 3, "# squash 5 100")
    commit_diff._check_annotation("f", 3, "# squash 5 100 1 2 80")
    commit_diff._check_annotation("f", 3, "# squash 5 100 1 2 80 -1 3 -1")
    check("known annotations accepted", True)


# -------------------------------------------------------- 2. compare() mixes

def test_compare():
    print("[2] commit_diff.compare v1/v2 pairs")
    with tempfile.TemporaryDirectory() as td:
        ref1 = os.path.join(td, "ref1.csv")
        run1 = os.path.join(td, "run1.csv")
        with open(ref1, "w") as f:
            f.write(v1row(0, 500, "1000", "add", [(1, 2, 80, V16)]) + "\n")
        with open(run1, "w") as f:
            f.write(v1row(0, 500, "1000", "add", [(1, 2, 80, V16)]) + "\n")
        res = commit_diff.compare(ref1, run1, 0)
        check("v1 pair no_divergence",
              res["verdict"] == "no_divergence", res["verdict"])
        check("v1 pair JSON has no format keys",
              "ref_format" not in res and "run_format" not in res)

        ref2 = os.path.join(td, "ref2.csv")
        run2 = os.path.join(td, "run2.csv")
        with open(ref2, "w") as f:
            f.write(HDR + "\n"
                    + v2row(0, 101, 500, "1000", "add",
                            [(1, 2, 80, V16)], [(1, 5, 79)]) + "\n")
        with open(run2, "w") as f:
            f.write(HDR + "\n"
                    + v2row(0, 101, 500, "1000", "add",
                            [(1, 2, 80, V16)], [(1, 5, 79)]) + "\n")
        res2 = commit_diff.compare(ref2, run2, 0)
        check("v2 pair no_divergence (src fields ignored)",
              res2["verdict"] == "no_divergence", res2["verdict"])
        check("v2 pair format keys present",
              res2.get("ref_format") == "v2"
              and res2.get("run_format") == "v2")

        run3 = os.path.join(td, "run3.csv")
        with open(run3, "w") as f:
            f.write(HDR + "\n"
                    + v2row(0, 101, 500, "1000", "add",
                            [(1, 2, 80, "deadbeefdeadbeef")],
                            [(1, 5, 79)]) + "\n")
        res3 = commit_diff.compare(ref2, run3, 0)
        check("v2 val divergence still ⑤数据损坏",
              res3["primary_class"] == "data_corruption",
              res3["primary_class"])

        # annotations in a compared file are skipped, not records
        run4 = os.path.join(td, "run4.csv")
        with open(run4, "w") as f:
            f.write(HDR + "\n")
            f.write("# squash 900 9999 1 2 80\n")
            f.write(v2row(0, 101, 500, "1000", "add",
                          [(1, 2, 80, V16)], [(1, 5, 79)]) + "\n")
        res4 = commit_diff.compare(ref2, run4, 0)
        check("squash annotation skipped in compare",
              res4["verdict"] == "no_divergence"
              and res4["run_instructions"] == 1)


# ------------------------------------------------------------ 3-7. build_l3

def write_ctrace(td, name, lines):
    p = os.path.join(td, name)
    with open(p, "w") as f:
        for l in lines:
            f.write(l + "\n")
    return p


def ev(sn=None, **kw):
    d = dict(tick=400000, site="fetch_decode", mode="opcode_bitflip",
             pc="0x400ab0", orig_enc="0x8b020020", new_enc="0x8b020021",
             bits="[7]")
    if sn is not None:
        d["sn"] = sn
    d.update(kw)
    return d


def test_build_l3_chain():
    print("[3-4] build_l3 join + BFS + kill rule")
    with tempfile.TemporaryDirectory() as td:
        lines = [HDR,
                 # filler rows before the source
                 v2row(8, 99, 480, "ff0", "movz", [(1, 1, 70, V16)], []),
                 # source: sn=101 defines phys 80 (arch 5)
                 v2row(10, 101, 500, "1000", "add",
                       [(1, 5, 80, V16)], [(1, 1, 70)]),
                 # hop 1: reads (1,5,80), defines (1,6,81)
                 v2row(11, 102, 510, "1004", "sub",
                       [(1, 6, 81, V16)], [(1, 5, 80)]),
                 # hop 2 (transitive): reads (1,6,81), defines (1,7,82)
                 v2row(12, 103, 520, "1008", "orr",
                       [(1, 7, 82, V16)], [(1, 6, 81)]),
                 # redefinition of phys 80 by an UNRELATED writer:
                 # not a consumer (reads (1,4,70)), kills live key (1,80)
                 v2row(13, 104, 530, "100c", "add",
                       [(1, 5, 80, V16)], [(1, 4, 70)]),
                 # post-kill read of phys 80: NOT a consumer (dead value)
                 v2row(14, 105, 540, "1010", "eor",
                       [(1, 8, 83, V16)], [(1, 5, 80)]),
                 ]
        p = write_ctrace(td, "ctrace.csv", lines)
        res = ooo_l3.build_l3("decode", [ev(sn=101)], p)
        check("status ok", res["status"] == "ok", res.get("caveat"))
        check("method source_read", res["method"] == "source_read")
        check("source row found by seqenc",
              res["source_row"]["seqencNum"] == 101
              and res["source_row"]["seq"] == 10)
        check("injected passthrough",
              res["injected"]["seqencNum"] == 101
              and res["injected"]["orig"] == "0x8b020020")
        check("two hops", len(res["hops"]) == 2,
              json.dumps(res["hops"], default=str))
        if len(res["hops"]) == 2:
            h1, h2 = res["hops"]
            check("hop1 via src (1,5,80)",
                  h1["via_src"] == {"class": 1, "arch": 5, "phys": 80}
                  and h1["seq"] == 11 and h1["committed"] is True)
            check("hop2 transitive via (1,6,81)",
                  h2["via_src"] == {"class": 1, "arch": 6, "phys": 81}
                  and h2["seq"] == 12)
        check("kill rule: no hop at seq 14",
              all(h["seq"] != 14 for h in res["hops"]))


def test_build_l3_squash():
    print("[5] build_l3 squash-path consumers")
    with tempfile.TemporaryDirectory() as td:
        lines = [HDR,
                 v2row(10, 201, 500, "1000", "add",
                       [(1, 2, 60, V16)], []),
                 "# squash 202 5050 1 2 60",     # squashed consumer
                 "# squash 203 5100 1 9 99",     # unrelated squashed inst
                 v2row(11, 204, 520, "1004", "sub",
                       [(1, 3, 61, V16)], [(1, 2, 60)]),
                 ]
        p = write_ctrace(td, "ctrace_sq.csv", lines)
        res = ooo_l3.build_l3("decode", [ev(sn=201)], p)
        check("status ok", res["status"] == "ok")
        sq = res["squashed_consumers"]
        check("squashed_consumers is a list", isinstance(sq, list), sq)
        check("exactly one squashed consumer", len(sq) == 1, sq)
        if isinstance(sq, list) and len(sq) == 1:
            check("squashed consumer fields",
                  sq[0]["seqencNum"] == 202 and sq[0]["committed"] is False
                  and sq[0]["via_src"] == {"class": 1, "arch": 2,
                                           "phys": 60})
        check("committed hop still found", len(res["hops"]) == 1)

        # source itself squashed: no committed row for sn
        lines2 = [HDR,
                  v2row(10, 301, 500, "1000", "add", [(1, 2, 60, V16)], []),
                  "# squash 302 5500 1 2 60",
                  ]
        p2 = write_ctrace(td, "ctrace_sq2.csv", lines2)
        res2 = ooo_l3.build_l3("decode", [ev(sn=302)], p2)
        check("squashed source: status ok", res2["status"] == "ok")
        check("squashed source flagged",
              res2.get("source_squashed") is True
              and res2["source_committed"] is False)
        check("squashed source: zero hops", res2["hops"] == [])

        # source never committed, never squashed (in flight)
        res3 = ooo_l3.build_l3("decode", [ev(sn=999)], p2)
        check("in-flight source: status ok, no hops",
              res3["status"] == "ok" and res3["hops"] == []
              and res3["source_committed"] is False
              and res3.get("source_squashed") is False)


def test_build_l3_unsupported():
    print("[6] build_l3 honest unsupported paths")
    with tempfile.TemporaryDirectory() as td:
        # v1 trace: no seqenc column -> unsupported
        p1 = write_ctrace(td, "v1.csv", [
            v1row(0, 500, "1000", "add", [(1, 2, 80, V16)]),
            v1row(1, 510, "1004", "sub", [(1, 3, 81, V16)]),
        ])
        res = ooo_l3.build_l3("decode", [ev(sn=101)], p1)
        check("v1 trace unsupported", res["status"] == "unsupported"
              and "v1" in res["reason"], res.get("reason"))

        # L0 events without sn -> unsupported
        p2 = write_ctrace(td, "v2b.csv", [HDR, v2row(0, 101, 500, "1000",
                                                     "add",
                                                     [(1, 2, 80, V16)], [])])
        res2 = ooo_l3.build_l3("decode", [ev(sn=None)], p2)
        check("no-sn L0 unsupported", res2["status"] == "unsupported"
              and "sn" in res2["reason"], res2.get("reason"))

        # no events at all -> unsupported
        res3 = ooo_l3.build_l3("decode", [], p2)
        check("no L0 events unsupported", res3["status"] == "unsupported")

        # unknown component -> unsupported
        res4 = ooo_l3.build_l3("bpu", [ev(sn=101)], p2)
        check("unknown component unsupported",
              res4["status"] == "unsupported")


def test_build_l3_fdc():
    print("[7] build_l3 first_divergent_commit window")
    with tempfile.TemporaryDirectory() as td:
        lines = [HDR,
                 v2row(10, 401, 500, "1000", "add",
                       [(1, 5, 80, V16)], []),
                 v2row(11, 402, 510, "1004", "sub",
                       [(1, 6, 81, V16)], [(1, 5, 80)]),
                 v2row(12, 403, 520, "1008", "orr",
                       [(1, 7, 82, V16)], [(1, 6, 81)]),
                 ]
        p = write_ctrace(td, "ctrace_fdc.csv", lines)
        res = ooo_l3.build_l3("decode", [ev(sn=401)], p,
                              first_divergent_commit=11)
        check("fdc window: hop at 11 kept",
              [h["seq"] for h in res["hops"]] == [11],
              json.dumps(res["hops"], default=str))
        check("fdc passthrough",
              res["first_divergent_commit"] == 11)

        # FIX-RB: the pipeline passes the l2 first-divergent RECORD
        # (a dict with "seq"), not a bare int -- both must window
        # identically and the result echoes the original argument.
        res_d = ooo_l3.build_l3("decode", [ev(sn=401)], p,
                                first_divergent_commit={
                                    "seq": 11, "class": "data_corruption"})
        check("fdc dict: same window as int",
              res_d["status"] == res["status"] == "ok"
              and [h["seq"] for h in res_d["hops"]] ==
              [h["seq"] for h in res["hops"]],
              json.dumps(res_d["hops"], default=str))
        check("fdc dict: echoed verbatim",
              res_d["first_divergent_commit"] ==
              {"seq": 11, "class": "data_corruption"},
              repr(res_d.get("first_divergent_commit")))
        # a dict without a usable integer seq: no bound (honest caveat),
        # never a TypeError, never a fabricated bound
        res_b = ooo_l3.build_l3("decode", [ev(sn=401)], p,
                                first_divergent_commit={"no_seq": True})
        check("fdc unusable form: no bound, no crash",
              res_b["status"] == "ok"
              and [h["seq"] for h in res_b["hops"]] == [11, 12]
              and "without a usable integer seq" in res_b["caveat"]
              and "no window bound applied" in res_b["caveat"],
              "hops=%r caveat=%r"
              % ([h["seq"] for h in res_b["hops"]],
                 res_b.get("caveat")))


def test_l0_log_contract():
    print("[8] FIX-B decode log line through the FROZEN L0 parser")
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "decode_injections.log")
        # exact FIX-B shape: injection success line, sn before the
        # line-final marker (deferred write completes at build join)
        with open(log, "w") as f:
            f.write("Tick: 400000, Site: fetch_decode, mode=opcode_bitflip"
                    ", pc=0x400ab0, orig_enc=0x8b020020"
                    ", new_enc=0x8b020021, bits=[7]"
                    ", orig_mnemonic=add, new_mnemonic=add"
                    ", macroop_new=0, sn=4321"
                    ", faults_injected: 1\n")
        import ooo_observation
        parsed = ooo_observation.parse_injection_log(log, "decode")
        check("L0 parser sees 1 event", parsed["injected"] == 1
              and len(parsed["events"]) == 1)
        rec = parsed["events"][0]
        check("L0 event carries sn", rec.get("sn") == 4321, rec)
        check("L0 event carries enc fields",
              rec.get("orig_enc") == "0x8b020020"
              and rec.get("new_enc") == "0x8b020021"
              and rec.get("bits") == "[7]")
        # and build_l3 accepts the parsed events directly
        with tempfile.TemporaryDirectory() as td2:
            ctr = write_ctrace(td2, "c.csv", [HDR,
                                              v2row(10, 4321, 500, "1000",
                                                    "add",
                                                    [(1, 5, 80, V16)],
                                                    [])])
            res = ooo_l3.build_l3("decode", parsed["events"], ctr)
            check("build_l3 via L0 parser events",
                  res["status"] == "ok"
                  and res["source_row"]["seqencNum"] == 4321)


def test_build_l3_rename_map_join():
    print("[9] rename/rat map-entry join (map_bitflip family, no sn)")
    with tempfile.TemporaryDirectory() as td:
        # L0 event shape: parse_injection_log of a rename_injections.log
        # map_bitflip2_adj line (class/arch are STRINGS; no sn exists).
        ev = {"tick": 100, "site": "rename_setEntry",
              "mode": "map_bitflip2_adj", "class": "vec", "arch": "V1",
              "old_phys": 1, "new_phys": 13, "bits": "(2,3)",
              "faults_injected": 1,
              "raw": "Tick: 100, Site: rename_setEntry, "
                     "mode=map_bitflip2_adj, class=vec, arch=V1, "
                     "old_phys=1, new_phys=13, faults_injected: 1"}
        lines = [HDR,
                 # pre-injection row (tick < seed tick): the corrupted
                 # definer cannot commit before its own rename
                 v2row(0, 9, 50, "401000", "mov", [(2, 1, 1, V16)],
                       [(2, 1, 1)]),
                 # THE CORRUPTED DEFINER: the injector mutates the
                 # by-ref phys_reg of setEntry, so this row's dest IS
                 # the corrupted mapping (2,1,13) -> the join anchor
                 v2row(1, 10, 150, "401004", "fadd", [(2, 1, 13, V16)],
                       []),
                 # hop1: reader of the corrupted mapping (src 2,1,13)
                 v2row(2, 11, 200, "401008", "cmeq", [(2, 2, 20, V16)],
                       [(2, 1, 13)]),
                 # hop2: downstream consumer of hop1's dest
                 v2row(3, 12, 250, "40100c", "fmla", [(2, 3, 21, V16)],
                       [(2, 2, 20)]),
                 # V1 re-pointed (dest 2,1,30): ends nothing of ours
                 v2row(4, 13, 300, "401010", "mov", [(2, 1, 30, V16)], []),
                 # phys reuse: a LATER legit re-allocation of phys 13 as
                 # V1's dest KILLS the live key (2,13) ...
                 v2row(5, 14, 350, "401014", "mov", [(2, 1, 13, V16)], []),
                 # ... so this later (2,1,13) reader is a reader of the
                 # NEW legitimate value, NOT a consumer of ours
                 v2row(6, 15, 400, "401018", "cmeq", [(2, 4, 40, V16)],
                       [(2, 1, 13)]),
                 # CONSUMER re-definition (the real-data 5326 pattern):
                 # a chain consumer of hop2's dest that also re-defines
                 # (2,1,13) -- its dest re-seeds live[(2,13)] with ITS
                 # (corrupted-derived) output, so the NEXT (2,1,13)
                 # reader IS a real hop (consumer test runs BEFORE the
                 # kill; the kill only fires for non-consumer rows)
                 v2row(7, 16, 450, "40101c", "fmla", [(2, 1, 13, V16)],
                       [(2, 3, 21)]),
                 v2row(8, 17, 500, "401020", "cmeq", [(2, 5, 60, V16)],
                       [(2, 1, 13)]),
                 ]
        p = write_ctrace(td, "rat_join.csv", lines)
        r = ooo_l3.build_l3("rat", [ev], p)

        def _seqs(res):
            hops = res.get("hops")
            return [h["seq"] for h in hops] if isinstance(hops, list) \
                else None

        check("rat join: status ok source_read",
              r["status"] == "ok" and r["method"] == "source_read",
              "%r %r" % (r.get("status"), r.get("method")))
        check("rat join: hops 2,3,7,8 (non-consumer kill excludes 6; "
              "consumer-redef re-seed includes 8)",
              _seqs(r) == [2, 3, 7, 8],
              json.dumps(r.get("hops"), default=str))
        check("rat join: hop3 via hop2's dest (consumer redef)",
              r["hops"][2]["via_src"] == {"class": 2, "arch": 3,
                                          "phys": 21},
              repr(r["hops"][2].get("via_src")))
        _via0 = (r["hops"][0].get("via_src")
                 if isinstance(r.get("hops"), list) and r["hops"]
                 and isinstance(r["hops"][0], dict) else None)
        check("rat join: hop1 via_src == corrupted mapping",
              _via0 == {"class": 2, "arch": 1, "phys": 13},
              repr(_via0))
        check("rat join: source_map_entry recorded",
              r.get("source_map_entry") == {"class": 2, "arch": 1,
                                            "old_phys": 1, "new_phys": 13,
                                            "tick": 100},
              repr(r.get("source_map_entry")))
        check("rat join: source_row IS the corrupted definer",
              isinstance(r.get("source_row"), dict)
              and r["source_row"]["seqencNum"] == 10
              and r["source_row"]["seq"] == 1,
              repr(r.get("source_row")))
        # int-typed tags join identically (hand-built event dicts)
        ev_int = dict(ev)
        ev_int["class"], ev_int["arch"] = 2, 1
        r_int = ooo_l3.build_l3("rename", [ev_int], p)
        check("rat join: int tags + 'rename' component identical",
              _seqs(r_int) == [2, 3, 7, 8],
              json.dumps(r_int.get("hops"), default=str))
        # zero-reader: the corrupted definer never commits (no dest
        # (2,1,13) row at/after the injection tick at all)
        lines_b = [l for l in lines if not l.startswith("1,10,")
                   and not l.startswith("2,11,") and not l.startswith("3,12,")
                   and not l.startswith("5,14,") and not l.startswith("6,15,")
                   and not l.startswith("7,16,") and not l.startswith("8,17,")]
        p_b = write_ctrace(td, "rat_noreader.csv", lines_b)
        r_b = ooo_l3.build_l3("rat", [ev], p_b)
        check("rat zero-reader: ok + empty hops + honest caveat",
              r_b["status"] == "ok"
              and (r_b.get("hops") == [] or r_b.get("hops") is None)
              and "never committed" in (r_b.get("caveat") or ""),
              "status=%r caveat=%r" % (r_b.get("status"),
                                       r_b.get("caveat")))
        # neither sn nor map tags -> honest unsupported
        r_c = ooo_l3.build_l3("rat", [{"tick": 100, "mode": "map_bitflip"}],
                              p)
        check("rat no join keys: unsupported with both keys named",
              r_c["status"] == "unsupported"
              and "sn" in r_c["reason"] and "new_phys" in r_c["reason"],
              repr(r_c.get("reason")))
        # sn still wins when present (rename dest_reg_sub family)
        r_d = ooo_l3.build_l3("rat", [dict(ev, sn=11)], p)
        check("rat sn priority: sn join used when present",
              r_d.get("source_row") is not None
              and r_d["source_row"]["seqencNum"] == 11,
              repr(r_d.get("source_row")))
        # int-class ("X"-family) seeds map class 0
        ev_x = dict(ev, arch="X5", old_phys=7, new_phys=9)
        ev_x["class"] = "int"
        lines_x = [HDR,
                   v2row(7, 70, 400, "402000", "add", [(0, 5, 9, V16)],
                         []),
                   v2row(8, 71, 450, "402004", "sub", [(0, 3, 50, V16)],
                         [(0, 5, 9)])]
        p_x = write_ctrace(td, "rat_int.csv", lines_x)
        r_x = ooo_l3.build_l3("rat", [ev_x], p_x)
        check("rat int-class join: class 0 via X-arch",
              r_x["status"] == "ok" and _seqs(r_x) == [8]
              and isinstance(r_x.get("hops"), list) and r_x["hops"]
              and r_x["hops"][0]["via_src"]["phys"] == 9
              and r_x["source_row"]["seqencNum"] == 70,
              json.dumps(r_x.get("hops"), default=str))


def main():
    test_parse_line()
    test_compare()
    test_build_l3_chain()
    test_build_l3_squash()
    test_build_l3_unsupported()
    test_build_l3_fdc()
    test_l0_log_contract()
    test_build_l3_rename_map_join()
    print()
    if FAILURES:
        print("FAILED: %d checks: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
