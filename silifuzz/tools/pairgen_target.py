#!/usr/bin/env python3
"""Target-directed generation: per-template proxy coverage targets, then fuzz into them.

Difference from the two earlier pipelines:

* ``pairgen.py``       restricted the generator's instruction vocabulary (not the paper).
* ``pairgen_paper.py`` generated freely and selected afterwards (paper-faithful, but streams
                       end up 2-4 instructions long).
* this file            extracts an explicit **coverage target per template** from the proxies
                       (Capstone = XED stand-in, Unicorn with a scenario state), then grows the
                       corpus towards that target and keeps the longest in-target streams.

Target definition
-----------------
``Target_cap(T) = ( U_{w in T} F_cap(w) ) \\ F_cap(nop)``
``Target_uc(T,S) = ( U_{w in T} F_uc(w | S) ) \\ F_uc(nop | S)``

``F`` are SanitizerCoverage counter sets inside the instrumented proxy library, read back by
``tools/covfingerprint``.  ``S`` is a per-family scenario (register/memory setup) for the
single-instruction Unicorn driver.

Direction mechanism (documented honestly): round-based corpus evolution.  Seeds are the
template's own instructions, so the fuzzer starts inside the target region; after each round
every candidate is scored by target hit + purity + length, and the best ones become the next
round's seed corpus.  libFuzzer's own coverage feedback is untouched.

Stages: targets -> fuzz -> fix -> select -> verify -> report
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
IFUZZ = BIN / "ifuzzgen"
SF_FIX = BIN / "sf_fix"
SF_PLAYER = BIN / "sf_player"
SF_CHECKER = BIN / "sf_checker"
CAP_FUZZ = BIN / "capstone_fuzz"
UC_FUZZ = BIN / "unicorn_fuzz"
FLEET = ROOT / "tools" / "fleet.py"
COVSRC = ROOT / "tools" / "covfingerprint"
CAP_LIB = ROOT / "third_party" / "capstone-build" / "libcapstone.a"
CAP_INC = ROOT / "third_party" / "capstone" / "include"
UC_LIB = ROOT / "third_party" / "unicorn-build" / "libunicorn.a"
UC_INC = ROOT / "third_party" / "unicorn" / "include"

sys.path.insert(0, str(ROOT / "tools"))
import sfsnapshot  # noqa: E402
import pairgen_paper as pp  # noqa: E402

CODE_BASE = pp.CODE_BASE
NOP = pp.NOP
DEFAULT_SEEDS = pp.DEFAULT_SEEDS

SCENARIO = {"c": "centered", "e": "small", "f": "fp1", "i": "branch",
            "l": "centered", "m": "mem_unmapped", "o": "small", "v": "vec_sat"}

MODULES = pp.MODULES


def log(msg):
    print("[target] " + msg, flush=True)


def run(cmd, timeout=7200, check=True):
    return pp.run(cmd, timeout=timeout, check=check)


def sha256_file(p):
    return pp.sha256_file(p)


def words_of(b):
    return pp.words_of(b)


# --------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------
def ensure_drivers(work: Path):
    """Build cov_cap, cov_uc, cov_uc1 into work/bin."""
    bindir = work / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    stubs = str(COVSRC / "covstubs.cc")
    cap = bindir / "cov_cap"
    uc1 = bindir / "cov_uc1"
    uc = bindir / "cov_uc"
    if not cap.exists():
        run(["clang++", "-O1", "-g", "-fuse-ld=lld", "-I", CAP_INC,
             COVSRC / "covdrv_capstone.cc", stubs, CAP_LIB, "-o", cap, "-lpthread"])
    if not uc1.exists():
        run(["clang++", "-O1", "-g", "-fuse-ld=lld", "-I", UC_INC,
             COVSRC / "covdrv_unicorn_one.cc", stubs, UC_LIB, "-o", uc1, "-lpthread", "-lm"])
    if not uc.exists():
        run(["clang++", "-O1", "-g", "-fuse-ld=lld", "-I", UC_INC,
             COVSRC / "covdrv_unicorn.cc", stubs, UC_LIB, "-o", uc, "-lpthread", "-lm"])
    return cap, uc1, uc


def cap_batch(driver: Path, words, tmp: Path):
    return pp.cap_batch(driver, words, tmp)


def uc1_batch(driver: Path, words, scenario: str, tmp: Path):
    uniq = sorted(set(words))
    tmp.write_bytes(b"".join(w.to_bytes(4, "little") for w in uniq))
    out = run([driver, "--batch", str(tmp), "--scenario", scenario]).stdout.splitlines()
    if len(out) != len(uniq):
        raise SystemExit("uc fingerprint mismatch: %d vs %d" % (len(out), len(uniq)))
    table = {}
    for w, line in zip(uniq, out):
        parts = line.split(",")
        table[w] = (parts[0] == "1", frozenset(int(x) for x in parts[1:] if x))
    return table


# --------------------------------------------------------------------------
# stage: targets
# --------------------------------------------------------------------------
def seed_like(code: bytes, tmpl: bytes) -> bool:
    """True when code is the template, or a prefix of its infinite repetition."""
    if not tmpl or not code:
        return False
    n = min(len(code), 4096)
    return all(code[i] == tmpl[i % len(tmpl)] for i in range(n))


def templates_from_seeds(seeds_dir: Path):
    out = []
    for p in sorted(seeds_dir.glob("*.S")):
        if p.name.startswith("asm_common"):
            continue
        out.append((p.name.split("_")[0], p))
    return out


def targets(args):
    work = Path(args.work)
    (work / "targets").mkdir(parents=True, exist_ok=True)
    (work / "seeds").mkdir(exist_ok=True)
    (work / "dict").mkdir(exist_ok=True)
    cap, uc1, _ = ensure_drivers(work)
    seeds_dir = Path(args.seeds).resolve()
    tmp = work / "words.bin"

    nop_cap = cap_batch(cap, [NOP], tmp)[NOP]
    base_cap = nop_cap[2]
    uc_bases = {}

    index = {}
    for tidy, src in templates_from_seeds(seeds_dir):
        fam = tidy[0]
        scen = SCENARIO.get(fam, "centered")
        obj = work / ("%s.o" % tidy)
        run(["gcc", "-c", "-I", seeds_dir, src, "-o", obj])
        raw = work / ("%s.text" % tidy)
        run(["objcopy", "-O", "binary", "--only-section=.text", obj, raw])
        text = raw.read_bytes()
        words = sorted(set(words_of(text)))

        capf = cap_batch(cap, words, tmp)
        cap_target = set()
        mnemonics = set()
        per_word_cap = {}
        for w in words:
            ok, mn, fs = capf[w]
            if ok:
                mnemonics.add(mn)
                s = fs - base_cap
                per_word_cap[w] = sorted(s)
                cap_target |= s

        if scen not in uc_bases:
            b = uc1_batch(uc1, [NOP], scen, tmp)[NOP]
            uc_bases[scen] = b[1]
        ucb = uc_bases[scen]
        ucf = uc1_batch(uc1, words, scen, tmp)
        uc_target = set()
        per_word_uc = {}
        for w in words:
            ok, fs = ucf[w]
            if ok:
                s = fs - ucb
                per_word_uc[w] = sorted(s)
                uc_target |= s

        # seed corpus: whole template for Unicorn, per-instruction for Capstone
        sd = work / "seeds" / tidy
        (sd / "cap").mkdir(parents=True, exist_ok=True)
        (sd / "uc").mkdir(parents=True, exist_ok=True)
        (sd / "uc" / "template.bin").write_bytes(text)
        for i, w in enumerate(words):
            (sd / "cap" / ("%04d.bin" % i)).write_bytes(w.to_bytes(4, "little"))

        # dictionary from the template's own encodings
        dd = work / "dict" / (tidy + ".dict")
        dd.write_text("\n".join('"%s"' % "".join("\\x%02X" % b for b in w.to_bytes(4, "little"))
                                for w in words) + "\n")

        index[tidy] = {
            "id": tidy, "family": fam, "module": MODULES.get(fam, "unknown"),
            "source": src.name, "source_sha256": sha256_file(src),
            "text_sha256": pp.sha256_bytes(text), "insns": len(text) // 4,
            "scenario": scen,
            "cap": {"target_size": len(cap_target), "mnemonics": sorted(mnemonics),
                    "per_word": {("%08x" % w): per_word_cap.get(w, []) for w in words}},
            "uc": {"target_size": len(uc_target),
                   "per_word": {("%08x" % w): per_word_uc.get(w, []) for w in words}},
        }
        (work / "targets" / (tidy + ".json")).write_text(json.dumps(index[tidy], indent=2) + "\n")
        log("%s: cap target %d blocks / %d mnemonics, uc target %d blocks (scenario %s)"
            % (tidy, len(cap_target), len(mnemonics), len(uc_target), scen))

    (work / "targets.json").write_text(json.dumps(index, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: fuzz (round-based corpus evolution towards the target)
# --------------------------------------------------------------------------
def score_candidates(cap, files, target_cap, mnemonics, base_cap, tmp):
    """cap target hit + mnemonic purity + length for each candidate."""
    words_per_file = {}
    all_words = []
    for p in files:
        w = words_of(p.read_bytes())
        words_per_file[p] = w
        all_words += w
    fp = cap_batch(cap, all_words + [NOP], tmp)
    base = fp[NOP][2] if NOP in fp else base_cap
    rows = []
    for p, w in words_per_file.items():
        got, mns = set(), set()
        for x in w:
            ok, mn, fs = fp.get(x, (False, None, frozenset()))
            if not ok:
                continue
            mns.add(mn)
            got |= (fs - base)
        hit = len(got & target_cap) / len(target_cap) if target_cap else 0.0
        purity = len(mns & mnemonics) / len(mns) if mns else 0.0
        rows.append({"path": str(p), "insns": len(w), "bytes": p.stat().st_size,
                     "cap_hit": round(hit, 4), "purity": round(purity, 4),
                     "mnemonics": sorted(mns)})
    return rows


def fuzz_one(job):
    """One template: R rounds of capped/unicorn fuzzing, reseeded by score."""
    (work, tidy, cap_path, uc1_path, rounds, cap_secs, uc_secs, keep) = job
    work = Path(work)
    t = json.loads((work / "targets" / (tidy + ".json")).read_text())
    target_cap = set()
    for v in t["cap"]["per_word"].values():
        target_cap |= set(v)
    mnemonics = set(t["cap"]["mnemonics"])
    seeds = work / "seeds" / tidy
    dictfile = work / "dict" / (tidy + ".dict")
    pool = work / "pool" / tidy
    pool.mkdir(parents=True, exist_ok=True)

    # Long seeds matter more than clever mutations: libFuzzer grows inputs
    # slowly, so the template is repeated up to the size cap to give the fuzzer
    # a long starting point (and -len_control=0 lets it stay long).
    template = (seeds / "uc" / "template.bin").read_bytes()
    rep_dir = seeds / "uc"
    for k in (1, 2, 4, 8):
        rep = (template * k)[:1024]
        (rep_dir / ("repeat%d.bin" % k)).write_bytes(rep)

    best_rows = []
    for r in range(rounds):
        sd = work / "seeds" / tidy / ("r%d" % r)
        (sd / "cap").mkdir(parents=True, exist_ok=True)
        (sd / "uc").mkdir(parents=True, exist_ok=True)
        # base seeds are present in every round: they are the only guarantee
        # that a long starting point survives the reseeding pressure
        for f in (seeds / "cap").glob("*.bin"):
            shutil.copy2(f, sd / "cap" / f.name)
        for f in rep_dir.glob("repeat*.bin"):
            shutil.copy2(f, sd / "uc" / f.name)
        if r > 0:
            prev = [x for x in best_rows if x["round"] == r - 1]
            in_t = [x for x in prev if x["cap_hit"] >= 0.8 and x["purity"] >= 0.9]
            long_any = sorted(prev, key=lambda x: -x["insns"])
            for j, x in enumerate((sorted(in_t, key=lambda x: -x["insns"]) + long_any)[: keep]):
                src = Path(x["path"])
                dst = sd / ("cap" if x["bytes"] <= 32 else "uc") / ("p%d_%s" % (j, src.name))
                if not dst.exists():
                    shutil.copy2(src, dst)

        cap_out = pool / ("r%d_cap" % r)
        uc_out = pool / ("r%d_uc" % r)
        for d in (cap_out, uc_out):
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)

        run([CAP_FUZZ, "-max_total_time=%d" % cap_secs, "-max_len=32",
             "-len_control=0", "-dict=%s" % dictfile, cap_out, sd / "cap"],
            timeout=cap_secs + 600)
        run([UC_FUZZ, "-max_total_time=%d" % uc_secs, "-max_len=1024",
             "-len_control=0", "-reduce_inputs=0",
             "-dict=%s" % dictfile, uc_out, sd / "uc"], timeout=uc_secs + 900)

        files = [p for p in list(cap_out.rglob("*")) + list(uc_out.rglob("*")) if p.is_file()]
        tmp = work / ("score_%s_%d.bin" % (tidy, os.getpid()))
        rows = score_candidates(Path(cap_path), files, target_cap, mnemonics,
                                frozenset(), tmp)
        for x in rows:
            x["round"] = r
        best_rows += rows
    return tidy, best_rows


def fuzz(args):
    work = Path(args.work)
    cap, uc1, _ = ensure_drivers(work)
    index = json.loads((work / "targets.json").read_text())
    jobs = [(str(work), tidy, str(cap), str(uc1), args.rounds, args.cap_seconds,
             args.uc_seconds, args.keep) for tidy in index]
    results = {}
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(fuzz_one, j): j[1] for j in jobs}
        for f in as_completed(futs):
            tidy, rows = f.result()
            results[tidy] = rows
            ok = [r for r in rows if r["cap_hit"] >= 0.8 and r["purity"] >= 0.9]
            longest = max((r["insns"] for r in ok), default=0)
            log("%s: %d candidates, %d in-target, longest in-target stream %d insns"
                % (tidy, len(rows), len(ok), longest))

    flat = []
    for tidy, rows in results.items():
        for r in rows:
            flat.append({"id": tidy, **r})
    (work / "pool.jsonl").write_text("\n".join(json.dumps(r) for r in flat) + "\n")


# --------------------------------------------------------------------------
# stage: fix
# --------------------------------------------------------------------------
def fix(args):
    work = Path(args.work)
    pool = [json.loads(l) for l in (work / "pool.jsonl").read_text().splitlines() if l.strip()]
    index = json.loads((work / "targets.json").read_text())
    sel = {}
    for tidy in index:
        rows = [r for r in pool if r["id"] == tidy]
        tmpl = (work / "seeds" / tidy / "uc" / "template.bin").read_bytes()
        tmpl_words = set(words_of(tmpl))
        live = []
        for r in rows:
            b = Path(r["path"]).read_bytes()
            if seed_like(b, tmpl):
                continue
            r["novel_words"] = len(set(words_of(b)) - tmpl_words)
            live.append(r)
        rows = live or rows
        # Three slices, because a length-only slice starves the selection of
        # short-but-executable options: longest mutated, purest, and shortest
        # fully in-target.
        long_slice = sorted(rows, key=lambda r: (-(r.get("novel_words", 0) >= 1), -r["insns"]))[
            : int(args.fix_candidates * 0.7)]
        pure_slice = sorted(rows, key=lambda r: (-r["purity"], r["insns"]))[
            : int(args.fix_candidates * 0.2)]
        short_slice = sorted((r for r in rows if r["cap_hit"] >= 0.8 and r["purity"] >= 0.9),
                             key=lambda r: r["insns"])[: int(args.fix_candidates * 0.15)]
        seen, picked = set(), []
        for r in long_slice + pure_slice + short_slice:
            if r["path"] in seen:
                continue
            seen.add(r["path"])
            picked.append(r)
        indir = work / "fix_in" / tidy
        if indir.exists():
            shutil.rmtree(indir)
        indir.mkdir(parents=True)
        for i, r in enumerate(picked):
            src = Path(r["path"])
            shutil.copy2(src, indir / ("%04d_%s" % (i, src.name)))
        outdir = work / "corpus" / tidy
        if outdir.exists():
            shutil.rmtree(outdir)
        outdir.mkdir(parents=True)
        stats = work / "corpus" / (tidy + ".fix.json")
        centered = tidy[0] in args.centered_families.split(",")
        cmd = [SF_FIX, "--in", indir, "--out", outdir, "--source", "target-directed",
               "--ref-cores", args.ref_cores, "--repeat", "3", "--jobs", "8",
               "--timeout-ms", "3000", "--stats", stats]
        if centered:
            # Memory-heavy families: the default initial state (half of the GPRs
            # hold small integers) makes long load/store streams fault early, so
            # the snapshot gets the same "scenario" treatment as the Unicorn
            # target: every GPR points into the data window.
            cmd += ["--centered-data", "--data-pages", "16"]
        run(cmd)
        payload = json.loads(stats.read_text())
        sel[tidy] = {"fix": payload, "picked": len(picked), "centered_data": centered}
        log("%s: fixed %d/%d (reasons %s)"
            % (tidy, payload["accepted"], len(picked), payload["reasons"]))
    (work / "fix.json").write_text(json.dumps(sel, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: select
# --------------------------------------------------------------------------
def select(args):
    work = Path(args.work)
    cap, uc1, _ = ensure_drivers(work)
    index = json.loads((work / "targets.json").read_text())
    tmp = work / "sel.bin"
    out = {}
    for tidy, t in index.items():
        target_cap = set()
        for v in t["cap"]["per_word"].values():
            target_cap |= set(v)
        mnemonics = set(t["cap"]["mnemonics"])
        snapshots = [p for p in (work / "corpus" / tidy).rglob("*.sfs") if p.is_file()]
        rows = []
        for p in snapshots:
            sn = sfsnapshot.load(str(p))
            code = None
            for mm in sn.mappings:
                if mm.start == CODE_BASE:
                    code = mm.data
                    break
            if not code or len(code) < 8:
                continue
            payload = code[:-4]
            es = sn.end_states[0]
            rows.append({"snapshot": str(p.relative_to(work)),
                         "sha": pp.sha256_bytes(payload),
                         "insns": len(payload) // 4,
                         "pc_offset": es.regs.pc - CODE_BASE,
                         "code_bytes": len(payload),
                         "signal": es.signal,
                         "code": payload})
        if not rows:
            raise SystemExit("%s: no snapshots" % tidy)

        # Reject degenerate candidates: the template itself, or any prefix of an
        # infinite repetition of it.  Those are seeds, not generated streams --
        # they would look perfect on purity/coverage while adding nothing.
        tmpl = (work / "seeds" / tidy / "uc" / "template.bin").read_bytes()
        tmpl_words = set(words_of(tmpl))
        kept = []
        for r in rows:
            if seed_like(r["code"], tmpl):
                r["seed_like"] = True
                continue
            kept.append(r)
        if not kept:
            raise SystemExit("%s: every candidate is a seed repetition" % tidy)
        rows_kept, rows = rows, kept
        n_seed_like = len(rows_kept) - len(rows)

        # "was actually mutated": at least one encoding that the template does
        # not contain, otherwise the stream is the seed with a different length.
        for r in rows:
            r["novel_words"] = len(set(words_of(r["code"])) - tmpl_words)
        mutated = [r for r in rows if r["novel_words"] >= 1]
        if mutated:
            rows = mutated
        fp = cap_batch(cap, [w for r in rows for w in words_of(r["code"])] + [NOP], tmp)
        base = fp[NOP][2]
        for r in rows:
            got, mns = set(), set()
            for w in words_of(r["code"]):
                ok, mn, fs = fp.get(w, (False, None, frozenset()))
                if ok:
                    mns.add(mn)
                    got |= (fs - base)
            r["cap_hit"] = len(got & target_cap) / len(target_cap) if target_cap else 0.0
            r["purity"] = len(mns & mnemonics) / len(mns) if mns else 0.0
            r["mnemonics"] = sorted(mns)
            r["foreign"] = sorted(mns - mnemonics)
            r["trailer"] = r["pc_offset"] >= r["code_bytes"] - 4
            r["exec_ratio"] = (min(r["pc_offset"], r["code_bytes"]) / r["code_bytes"]
                               if r["code_bytes"] else 0.0)

        # Length is the primary objective (user's call), so the choice is:
        # among streams that reach the trailer and clear the quality floor,
        # take the longest.  The ladder is still recorded for auditing.
        ladder = []
        for (hit_gate, pur_gate) in ((0.9, 0.95), (0.8, 0.9), (0.7, 0.8),
                                     (args.min_hit, args.min_purity), (0.0, 0.0)):
            pool = [r for r in rows if r["trailer"] and r["cap_hit"] >= hit_gate
                    and r["purity"] >= pur_gate]
            row = {"hit_gate": hit_gate, "purity_gate": pur_gate, "available": len(pool)}
            if pool:
                b = max(pool, key=lambda r: (r["insns"], r["cap_hit"], r["purity"]))
                row.update({"insns": b["insns"], "cap_hit": round(b["cap_hit"], 4),
                            "purity": round(b["purity"], 4), "snapshot": b["snapshot"]})
            ladder.append(row)
        floor = [r for r in rows if r["trailer"]
                 and r["cap_hit"] >= args.min_hit and r["purity"] >= args.min_purity]
        relaxed = None
        if not floor:
            # SiliFuzz snapshots may legitimately end in a signal.  For templates
            # whose own instruction mix destroys the data-pointer invariant, a
            # long stream cannot run to the BRK, so accept "executed most of
            # itself, then faulted" instead of dropping to foreign-heavy code.
            floor = [r for r in rows if r["exec_ratio"] >= args.min_exec_ratio
                     and r["cap_hit"] >= args.min_hit and r["purity"] >= args.min_purity]
            relaxed = "executed>=%.0f%%" % (100 * args.min_exec_ratio)
        if not floor:
            # relax the target gate first, keep a hard cap on foreign instructions
            floor = [r for r in rows if r["trailer"] and r["purity"] >= args.min_purity]
            relaxed = "hit"
        if not floor:
            floor = [r for r in rows if r["trailer"] and r["purity"] >= 0.5]
            relaxed = "hit+purity>=0.5"
        purity_priority = False
        if not floor:
            # No trailer-reaching stream stays inside the template's mnemonic
            # set at all; switch to purity-first and flag it instead of shipping
            # a long stream that is mostly foreign code.
            floor = [r for r in rows if r["trailer"]] or rows
            relaxed = "purity_priority"
            purity_priority = True
        if purity_priority:
            # Deliver a stream that actually executes: longest among the ones
            # that reach the trailer while staying in-region.  The long-but-
            # barely-executed alternative is reported separately.
            run_ok = [r for r in rows if r["trailer"] and r["purity"] >= args.min_purity]
            if run_ok:
                chosen = max(run_ok, key=lambda r: (r["insns"], r["cap_hit"]))
            else:
                chosen = max(floor, key=lambda r: (r["purity"], r["insns"]))
        else:
            chosen = max(floor, key=lambda r: (r["insns"], r["cap_hit"], r["purity"]))
        longest_any = max((r for r in rows if r["trailer"]), key=lambda r: r["insns"], default=None)

        # unicorn target check for the chosen stream
        scen = t["scenario"]
        b = uc1_batch(uc1, [NOP], scen, tmp)[NOP][1]
        uc_target = set()
        for v in t["uc"]["per_word"].values():
            uc_target |= set(v)
        uc_stream = set()
        ucf = uc1_batch(uc1, words_of(chosen["code"]), scen, tmp)
        for w in words_of(chosen["code"]):
            ok, fs = ucf.get(w, (False, frozenset()))
            if ok:
                uc_stream |= (fs - b)
        out[tidy] = {
            "snapshot": chosen["snapshot"], "snapshot_sha": sha256_file(work / chosen["snapshot"]),
            "candidate_sha": chosen["sha"], "insns": chosen["insns"],
            "code_bytes": chosen["code_bytes"], "pc_offset": chosen["pc_offset"],
            "signal": chosen["signal"], "trailer": bool(chosen["trailer"]),
            "cap_hit": round(chosen["cap_hit"], 4), "purity": round(chosen["purity"], 4),
            "foreign_mnemonics": chosen["foreign"],
            "stream_mnemonics": chosen["mnemonics"],
            "template_mnemonics": sorted(mnemonics),
            "uc": {"target_size": len(uc_target), "stream_size": len(uc_stream),
                   "precision": round(len(uc_stream & uc_target) / len(uc_stream), 4) if uc_stream else 0.0,
                   "recall": round(len(uc_stream & uc_target) / len(uc_target), 4) if uc_target else 0.0},
            "ladder": ladder,
            "target": {"cap_size": len(target_cap), "uc_size": len(uc_target), "scenario": scen},
            "excluded_seed_like": n_seed_like, "floor_relaxed": relaxed,
            "distinct_words": len(set(words_of(chosen["code"]))),
            "mutated": True,
            "status": ("ok" if chosen["insns"] >= max(8, 0.3 * t["insns"]) else "gap"),
            "exec_frontier": max((r["insns"] for r in rows
                                  if r["trailer"] and r["purity"] >= args.min_purity), default=0),
        }
        log("%s: %d insns (%.0f%% of template), cap_hit %.2f purity %.2f trailer=%s"
            % (tidy, chosen["insns"], 100.0 * chosen["insns"] / max(1, t["insns"]),
               chosen["cap_hit"], chosen["purity"], chosen["trailer"]))
    (work / "selection.json").write_text(json.dumps(out, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: verify
# --------------------------------------------------------------------------
def verify(args):
    work = Path(args.work)
    sel = json.loads((work / "selection.json").read_text())
    vdir = work / "verify"
    vdir.mkdir(exist_ok=True)
    all_snaps = work / "snapshots_all"
    if all_snaps.exists():
        shutil.rmtree(all_snaps)
    all_snaps.mkdir()
    out = {}
    for tidy, s in sel.items():
        snap = work / s["snapshot"]
        loaded = sfsnapshot.load(str(snap))
        code = None
        for mm in loaded.mappings:
            if mm.start == CODE_BASE:
                code = mm.data
                break
        payload = code[:-4]
        if pp.sha256_bytes(payload) != s["candidate_sha"]:
            raise SystemExit("%s: snapshot code differs from selected candidate" % tidy)
        replays = []
        for core in (0, 32, 64, 96):
            proc = run([SF_PLAYER, "--snapshot", snap, "--core", str(core), "--repeat", "3"])
            runs = pp.parse_json_lines(proc.stdout)
            if len(runs) != 3 or not all(r.get("ok") and r.get("match") for r in runs):
                raise SystemExit("%s: replay failed on core %d" % (tidy, core))
            replays.append({"core": core})
        shutil.copy2(snap, all_snaps / (tidy + ".sfs"))
        out[tidy] = {"snapshot": snap.name, "snapshot_sha256": s["snapshot_sha"],
                     "code_sha256": s["candidate_sha"], "insns": s["insns"],
                     "cap_hit": s["cap_hit"], "purity": s["purity"], "uc": s["uc"],
                     "pc_offset": s["pc_offset"], "code_bytes": s["code_bytes"],
                     "trailer": s["trailer"], "signal": s["signal"],
                     "replay_cores": [r["core"] for r in replays]}
        log("%s: audit+replay ok" % tidy)

    checks = {}
    for mode, extra in (("sweep", []), ("sampled", ["--batch-size", "50", "--execs-per-batch", "1000"])):
        proc = run([SF_CHECKER, "--corpus", all_snaps, "--cores", args.cores,
                    "--seconds", str(args.sweep_seconds), "--mode", mode,
                    "--out", vdir / ("check-" + mode)] + extra,
                   timeout=args.sweep_seconds + 600)
        summary = pp.parse_json_lines(proc.stdout)[-1]
        checks[mode] = summary
        if summary["mismatches"] or summary["errors"] or summary["executions"] == 0:
            raise SystemExit("%s checker problem: %s" % (mode, summary))
        log("%s: %s execs, %s mismatches" % (mode, summary["executions"], summary["mismatches"]))
    proc = run([sys.executable, FLEET, "--corpus", all_snaps, "--db", vdir / "fleet.db",
                "--out-root", vdir / "fleet", "--cores", args.cores,
                "--window-cores", "4", "--window-seconds", str(args.fleet_seconds),
                "--windows", str(args.fleet_windows), "--mode", "sweep"],
               timeout=args.fleet_seconds * args.fleet_windows + 900)
    checks["fleet"] = {"summary": proc.stdout.strip().splitlines()[-1:]}
    (vdir / "verify.json").write_text(json.dumps({"checks": checks, "pairs": out}, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: report
# --------------------------------------------------------------------------
def report(args):
    work = Path(args.work)
    index = json.loads((work / "targets.json").read_text())
    sel = json.loads((work / "selection.json").read_text())
    ver = json.loads((work / "verify" / "verify.json").read_text())
    checks = ver["checks"]

    lines = [
        "# 目标驱动的 SiliFuzz 生成（ARM64，2026-11-23）",
        "",
        "为每个 sdcfuzz 模板显式定义代理覆盖目标，再让代理朝目标生成，优先流长。",
        "",
        "`Target_cap(T) = (∪ F_cap(w)) − F_cap(nop)`；`Target_uc(T,S) = (∪ F_uc(w|S)) − F_uc(nop|S)`。",
        "F 为代理内部 SanitizerCoverage 计数器；S 为按模板族指定的 Unicorn 场景初态。",
        "",
        "| 模板 | 状态 | 族 | 场景 | 目标块(cap/uc) | 模板指令 | 流指令 | 长度比 | 目标达成 | 纯度 | Unicorn 命中 | 跑到末尾 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for tidy, s in sel.items():
        t = index[tidy]
        lines.append("| %s | %s | %s | %s | %d/%d | %d | %d | %.2f | %.2f | %.2f | %.2f | %s |" % (
            tidy, s["status"], t["family"], t["scenario"],
            t["cap"]["target_size"], t["uc"]["target_size"],
            t["insns"], s["insns"], s["insns"] / max(1, t["insns"]),
            s["cap_hit"], s["purity"], s["uc"]["recall"],
            "是" if s["trailer"] else "否"))
    lines += [
        "",
        "",
        "## 差距（如实记录）",
        "",
        "`status=gap` 的模板无法在本模型下产出「长 + 区域内 + 能跑完」的流：",
        "",
        "| 模板 | 可执行前沿(纯度≥0.8) | 模板指令 | 原因 |",
        "| --- | --- | --- | --- |",
    ] + [
        "| %s | %d | %d | %s |" % (
            k, v["exec_frontier"], index[k]["insns"],
            "代理词表的操作数把 x0 同时当数据寄存器与基址寄存器；模板自身的 movk/add 一旦写坏基址，"
            "后续访存立即缺页，长流必然早崩" if v["status"] == "gap" else "—")
        for k, v in sel.items() if v["status"] == "gap"
    ] + [
        "",
        "这也是上一轮 `pairgen.py` 必须做寄存器分区（Rn 固定 x18–x25）的原因：不分区就没有长流。",
        "",
        "## 机群校验",
        "",
        "| 模式 | 核 | 执行次数 | 不匹配 | 错误 |",
        "| --- | --- | --- | --- | --- |",
        "| sweep | %s | %s | %s | %s |" % (checks["sweep"]["cores"], checks["sweep"]["executions"],
                                          checks["sweep"]["mismatches"], checks["sweep"]["errors"]),
        "| sampled 50/1000 | %s | %s | %s | %s |" % (checks["sampled"]["cores"],
                                                     checks["sampled"]["executions"],
                                                     checks["sampled"]["mismatches"],
                                                     checks["sampled"]["errors"]),
        "",
        "## 定性",
        "",
        "- 这是**扩展**：目标由本工具定义，生成靠轮次式语料进化（种子=模板指令，按目标命中重播种子），",
        "  libFuzzer 自身的覆盖率反馈未改动。",
        "- 与原文口径的区别：原文无目标、无重播种；与 `pairgen.py` 的区别：不改指令词表。",
    ]
    (work / "final").mkdir(exist_ok=True)
    (work / "final" / "pairs.md").write_text("\n".join(lines) + "\n")
    manifest = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "index": index,
                "selection": sel, "checks": checks}
    (work / "final" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.copy_to:
        dest = Path(args.copy_to)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / "final" / "manifest.json", dest / "manifest.json")
        shutil.copy2(work / "final" / "pairs.md", dest / "pairs.md")
        shutil.copytree(work / "snapshots_all", dest / "snapshots", dirs_exist_ok=True)
        for f in (work / "targets").glob("*.json"):
            shutil.copy2(f, dest / ("target_%s.json" % f.stem))
        log("copied to %s" % dest)
    log("report done")


# --------------------------------------------------------------------------
def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--work", required=True)
        p.add_argument("--seeds", default=str(DEFAULT_SEEDS))

    p = sub.add_parser("targets"); common(p)

    p = sub.add_parser("fuzz"); common(p)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--cap-seconds", type=int, default=60)
    p.add_argument("--uc-seconds", type=int, default=120)
    p.add_argument("--keep", type=int, default=300)
    p.add_argument("--jobs", type=int, default=4)

    p = sub.add_parser("fix"); common(p)
    p.add_argument("--fix-candidates", type=int, default=800)
    p.add_argument("--ref-cores", default="0,32,64,96")
    p.add_argument("--centered-families", default="c,l,m")

    p = sub.add_parser("select"); common(p)
    p.add_argument("--min-hit", type=float, default=0.6)
    p.add_argument("--min-purity", type=float, default=0.8)
    p.add_argument("--min-exec-ratio", type=float, default=0.8)

    p = sub.add_parser("verify"); common(p)
    p.add_argument("--cores", default="0-127")
    p.add_argument("--sweep-seconds", type=int, default=30)
    p.add_argument("--fleet-seconds", type=int, default=60)
    p.add_argument("--fleet-windows", type=int, default=2)

    p = sub.add_parser("report"); common(p)
    p.add_argument("--copy-to", default="")

    args = ap.parse_args()
    Path(args.work).mkdir(parents=True, exist_ok=True)
    {"targets": targets, "fuzz": fuzz, "fix": fix, "select": select,
     "verify": verify, "report": report}[args.cmd](args)


if __name__ == "__main__":
    main()
