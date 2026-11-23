#!/usr/bin/env python3
"""Paper-faithful pairing: unfiltered three-proxy corpus, coverage-region matching.

This is the counterpart of ``pairgen.py``: generation follows SiliFuzz §2.4
verbatim (ifuzz with no instruction filter, the Capstone decoder proxy and the
Unicorn emulator proxy driven by libFuzzer), and the *only* targeting happens
afterwards, when a stream is selected for a sdcfuzz template by comparing the
coverage region each of them occupies **inside the proxy itself**.

Coverage region
---------------
``R(x) = union over the 32-bit words of x of F(w)  minus  F(nop)``

``F(w)`` is the set of SanitizerCoverage counters set inside the instrumented
Capstone library while the proxy decodes ``w``.  Capstone's proxy decodes one
instruction per input, so a template's region is necessarily the union over its
instructions; the same definition is applied to candidate streams, which keeps
the comparison symmetric.  Counters come from the very instrumentation libFuzzer
uses, read back through ``tools/covfingerprint``.

Stages: corpus -> regions -> verify -> report
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
IFUZZ = BIN / "ifuzzgen"
SF_FIX = BIN / "sf_fix"
SF_PLAYER = BIN / "sf_player"
SF_CHECKER = BIN / "sf_checker"
FLEET = ROOT / "tools" / "fleet.py"
COVSRC = ROOT / "tools" / "covfingerprint"
CAP_LIB = ROOT / "third_party" / "capstone-build" / "libcapstone.a"
CAP_INC = ROOT / "third_party" / "capstone" / "include"
UC_LIB = ROOT / "third_party" / "unicorn-build" / "libunicorn.a"
UC_INC = ROOT / "third_party" / "unicorn" / "include"

sys.path.insert(0, str(ROOT / "tools"))
import sfsnapshot  # noqa: E402

CODE_BASE = sfsnapshot.CODE_BASE
DEFAULT_SEEDS = ROOT.parent / "sdcfuzz" / "upstream" / "seeds"
NOP = 0xD503201F

MODULES = {
    "c": "cache / L2-L3 eviction",
    "e": "execution unit carry chains",
    "f": "FSU special operands",
    "i": "instruction fetch / branch",
    "l": "load-store disambiguation",
    "m": "MMU / TLB / cross-page",
    "o": "out-of-order ROB / mispredict",
    "v": "vector FSU power stress",
}


def log(msg):
    print("[paper] " + msg, flush=True)


def run(cmd, timeout=3600, check=True):
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s\n%s"
                         % (proc.returncode, " ".join(cmd),
                            proc.stdout[-3000:], proc.stderr[-3000:]))
    return proc


def sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def words_of(data: bytes):
    return [int.from_bytes(data[i:i + 4], "little") for i in range(0, len(data) - 3, 4)]


# --------------------------------------------------------------------------
# coverage fingerprints
# --------------------------------------------------------------------------
def ensure_drivers(work: Path):
    bindir = work / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    cap = bindir / "cov_cap"
    uc = bindir / "cov_uc"
    stubs = str(COVSRC / "covstubs.cc")
    if not cap.exists():
        run(["clang++", "-O1", "-g", "-fuse-ld=lld", "-I", CAP_INC,
             COVSRC / "covdrv_capstone.cc", stubs, CAP_LIB, "-o", cap, "-lpthread"])
        log("built %s" % cap)
    if not uc.exists():
        run(["clang++", "-O1", "-g", "-fuse-ld=lld", "-I", UC_INC,
             COVSRC / "covdrv_unicorn.cc", stubs, UC_LIB, "-o", uc, "-lpthread", "-lm"])
        log("built %s" % uc)
    return cap, uc


def cap_batch(driver: Path, words, tmp: Path):
    """Fingerprint every distinct word in one driver process."""
    uniq = sorted(set(words))
    raw = b"".join(w.to_bytes(4, "little") for w in uniq)
    tmp.write_bytes(raw)
    out = run([driver, "--batch", tmp]).stdout.splitlines()
    if len(out) != len(uniq):
        raise SystemExit("fingerprint count mismatch: %d vs %d" % (len(out), len(uniq)))
    table = {}
    for w, line in zip(uniq, out):
        parts = line.split(",")
        ok = parts[0] == "1"
        mn = parts[1] if len(parts) > 1 else "-"
        table[w] = (ok, mn, frozenset(int(x) for x in parts[2:] if x))
    return table


def uc_region(driver: Path, data: bytes, tmp: Path):
    tmp.write_bytes(data)
    line = run([driver, tmp]).stdout.strip()
    return frozenset(int(x) for x in line.split(",") if x)


# --------------------------------------------------------------------------
# stage: corpus (paper §2.4, no targeting)
# --------------------------------------------------------------------------
def corpus(args):
    work = Path(args.work)
    cand = work / "cand"
    for sub in ("ifuzz", "capstone", "unicorn"):
        (cand / sub).mkdir(parents=True, exist_ok=True)
    snaps = work / "corpus"
    if args.reuse_corpus:
        log("reuse-corpus: skipping generation and fixing, re-indexing only")
        stats = work / "corpus.fix.json"
        payload = json.loads(stats.read_text()) if stats.exists() else {"reused": True}
        accepted = sorted(snaps.rglob("*.sfs"))
        provenance = {}
        counts = {}
        for sub in ("ifuzz", "capstone", "unicorn"):
            files = [p for p in (cand / sub).rglob("*") if p.is_file()]
            counts[sub] = len(files)
            for p in files:
                provenance[sha256_file(p)] = sub
        by_source = Counter()
        meta_by_snap = {}
        table_words = None
        for p in accepted:
            s = sfsnapshot.load(str(p))
            m = json.loads(s.meta)
            code = None
            for mm in s.mappings:
                if mm.start == CODE_BASE:
                    code = mm.data
                    break
            payload_code = code[:-4] if code else b""
            code_sha = sha256_bytes(payload_code)
            src = provenance.get(code_sha)
            if src is None:
                if table_words is None:
                    tj = work / "table_base.json"
                    run([IFUZZ, "-table-json", tj])
                    table_words = {e["as_uint32"] for e in json.loads(tj.read_text())}
                words = words_of(payload_code)
                src = "ifuzz" if all(x in table_words for x in words) else "proxy"
            by_source[src] += 1
            meta_by_snap[p.name] = {
                "source": src, "candidate_sha256": code_sha,
                "code_bytes": len(payload_code),
                "pc_offset": s.end_states[0].regs.pc - CODE_BASE,
                "signal": s.end_states[0].signal,
            }
        (work / "corpus.json").write_text(json.dumps({
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "candidates": counts, "fixer": payload,
            "accepted": len(accepted), "accepted_by_source": dict(by_source),
            "snapshots": meta_by_snap,
        }, indent=2) + "\n")
        log("corpus: %d snapshots (%s)" % (len(accepted), dict(by_source)))
        return

    if snaps.exists():
        shutil.rmtree(snaps)
    snaps.mkdir(parents=True)

    log("ifuzz: %d candidates (default table, no filters)" % args.ifuzz_n)
    run([IFUZZ, "-n", args.ifuzz_n, "-seed", args.seed, "-out", cand / "ifuzz"], timeout=1800)

    log("capstone proxy: %ds libFuzzer" % args.cap_seconds)
    run([BIN / "capstone_fuzz", "-max_total_time=%d" % args.cap_seconds,
         "-max_len=64", "-print_final_stats=1", cand / "capstone"], timeout=args.cap_seconds + 600)

    log("unicorn proxy: %ds libFuzzer" % args.uc_seconds)
    run([BIN / "unicorn_fuzz", "-max_total_time=%d" % args.uc_seconds,
         "-max_len=4096", "-print_final_stats=1", cand / "unicorn"], timeout=args.uc_seconds + 900)

    # provenance: hash -> source, so every accepted snapshot can be attributed
    provenance = {}
    counts = {}
    for sub in ("ifuzz", "capstone", "unicorn"):
        files = [p for p in (cand / sub).rglob("*") if p.is_file()]
        counts[sub] = len(files)
        for p in files:
            provenance[sha256_file(p)] = sub
        log("%s: %d candidate files" % (sub, len(files)))

    stats = work / "corpus.fix.json"
    run([SF_FIX, "--in", cand / "ifuzz", "--in", cand / "capstone", "--in", cand / "unicorn",
         "--out", snaps, "--source", "paper-three-proxies",
         "--ref-cores", args.ref_cores, "--repeat", "3", "--jobs", "8",
         "--timeout-ms", "3000", "--stats", stats], timeout=7200)
    payload = json.loads(stats.read_text())
    log("fixer: %s" % json.dumps(payload))

    accepted = sorted(snaps.rglob("*.sfs"))
    by_source = Counter()
    meta_by_snap = {}
    for p in accepted:
        s = sfsnapshot.load(str(p))
        m = json.loads(s.meta)
        code = None
        for mm in s.mappings:
            if mm.start == CODE_BASE:
                code = mm.data
                break
        code_sha = sha256_bytes(code[:-4] if code else b"")
        src = provenance.get(code_sha, "unknown")
        by_source[src] += 1
        meta_by_snap[p.name] = {
            "source": src,
            "candidate_sha256": code_sha,
            "code_bytes": len(code) - 4 if code else 0,
            "pc_offset": s.end_states[0].regs.pc - CODE_BASE,
            "signal": s.end_states[0].signal,
        }
    (work / "corpus.json").write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "candidates": counts,
        "fixer": payload,
        "accepted": len(accepted),
        "accepted_by_source": dict(by_source),
        "snapshots": meta_by_snap,
    }, indent=2) + "\n")
    log("corpus: %d snapshots (%s)" % (len(accepted), dict(by_source)))


# --------------------------------------------------------------------------
# stage: regions + selection
# --------------------------------------------------------------------------
def discover_templates(seeds_dir: Path):
    return [(p.name.split("_")[0], p) for p in sorted(seeds_dir.glob("*.S"))
            if not p.name.startswith("asm_common")]


def regions(args):
    work = Path(args.work)
    cap, uc = ensure_drivers(work)
    corpus = json.loads((work / "corpus.json").read_text())
    snaps = sorted((work / "corpus").rglob("*.sfs"))
    if not snaps:
        raise SystemExit("empty corpus")

    tmp = work / "words.bin"
    seeds_dir = Path(args.seeds).resolve()
    templates, tmpl_words = {}, {}
    for tidy, src in discover_templates(seeds_dir):
        obj = work / ("%s.o" % tidy)
        run(["gcc", "-c", "-I", seeds_dir, src, "-o", obj])
        raw = work / ("%s.text" % tidy)
        run(["objcopy", "-O", "binary", "--only-section=.text", obj, raw])
        data = raw.read_bytes()
        templates[tidy] = {
            "id": tidy, "module": MODULES.get(tidy[0], "unknown"),
            "source": src.name, "source_sha256": sha256_file(src),
            "insns": len(data) // 4, "text_sha256": sha256_bytes(data),
        }
        tmpl_words[tidy] = words_of(data)

    snap_code = {}
    for p in snaps:
        s = sfsnapshot.load(str(p))
        code = None
        for mm in s.mappings:
            if mm.start == CODE_BASE:
                code = mm.data
                break
        if code is None or len(code) < 8:
            continue
        snap_code[p.name] = code[:-4]

    all_words = [NOP]
    for w in tmpl_words.values():
        all_words += w
    for d in snap_code.values():
        all_words += words_of(d)
    log("fingerprinting %d distinct words" % len(set(all_words)))
    fp = cap_batch(cap, all_words, tmp)
    def fset(w):
        """Counters of a word, empty when the decoder rejected it."""
        v = fp.get(w)
        return v[2] if v and v[0] else frozenset()

    def mnem(w):
        v = fp.get(w)
        return v[1] if v and v[0] else None

    base = fset(NOP)

    def region(words):
        out = set()
        for w in words:
            out |= fset(w)
        return out - base

    regions_t = {t: region(w) for t, w in tmpl_words.items()}
    # Distinct decoder paths (fingerprint identities), not counter counts: a
    # two-instruction stream can repeat one path and inflate counter recall,
    # which is not "covering the template's region".
    tmpl_mn = {t: {mnem(w) for w in wl if mnem(w)} for t, wl in tmpl_words.items()}
    templates_mn = tmpl_mn
    for t, r in regions_t.items():
        templates[t]["region_size"] = len(r)
        templates[t]["distinct_forms"] = len({tuple(sorted(fset(w) - base)) for w in tmpl_words[t]
                                              if fset(w)})

    # Per-snapshot region and its precision against every template.  Computing
    # the full 20 x N table once keeps the per-template pass cheap and makes the
    # "which other templates share this region" question answerable.
    snap_region, snap_insns, snap_mn, stats = {}, {}, {}, {}
    snap_mn_all = {}   # every snapshot, including 1-instruction ones
    for name, data in snap_code.items():
        w = words_of(data)
        snap_insns[name] = len(w)
        snap_mn_all[name] = {mnem(x) for x in w if mnem(x)}
        r = region(w)
        if not r:
            continue
        decoded = sum(1 for x in w if fp.get(x) and fp[x][0])
        if len(r) < args.min_region or decoded < args.min_decoded:
            continue
        snap_region[name] = r
        snap_mn[name] = {mnem(x) for x in w if mnem(x)}

    for tidy, rt in regions_t.items():
        for name, rs in snap_region.items():
            inter = len(rs & rt)
            p = inter / len(rs)
            rec = inter / len(rt) if rt else 0.0
            f1 = 0.0 if p + rec == 0 else 2 * p * rec / (p + rec)
            tf = templates_mn[tidy]
            hit = len(snap_mn[name] & tf)
            mprec = hit / len(snap_mn[name]) if snap_mn[name] else 0.0
            mrec = hit / len(tf) if tf else 0.0
            stats.setdefault(name, {})[tidy] = (p, rec, f1, mprec, mrec)

    selection = {}
    for tidy, t in templates.items():
        meta_all = corpus["snapshots"]
        rt_mn = templates_mn[tidy]

        def trailer_ok(n):
            return meta_all[n]["pc_offset"] >= meta_all[n]["code_bytes"] - 4

        def shared(n):
            return sorted(o for o in templates
                          if o != tidy and stats[n][o][0] >= 0.9)

        # Purity (share of the stream's mnemonics the template also uses) and
        # decoder-path precision (counter overlap) are the two consistency
        # axes; random paper-faithful streams trade both against coverage, so
        # the ladder is reported and the operating point is explicit.
        stages = [(1.0, 0.95), (0.9, 0.9), (0.8, 0.9), (0.8, 0.8),
                  (0.7, 0.7), (0.5, 0.5), (0.0, 0.0)]
        ladder, chosen_row = [], None
        for mn_gate, ct_gate in stages:
            pool = [n for n in snap_region
                    if stats[n][tidy][3] >= mn_gate
                    and stats[n][tidy][0] >= ct_gate
                    and trailer_ok(n)]
            row = {"mnemonic_purity_gate": mn_gate, "counter_precision_gate": ct_gate,
                   "available": len(pool)}
            if pool:
                shared_n = {n: len(shared(n)) for n in pool}
                pool.sort(key=lambda n: (-stats[n][tidy][4], shared_n[n],
                                         -stats[n][tidy][0],
                                         abs(snap_insns[n] - t["insns"])))
                n = pool[0]
                row.update({
                    "snapshot": n,
                    "purity": round(stats[n][tidy][3], 4),
                    "coverage": round(stats[n][tidy][4], 4),
                    "counter_precision": round(stats[n][tidy][0], 4),
                    "counter_recall": round(stats[n][tidy][1], 4),
                    "insns": snap_insns[n], "shared": shared_n[n],
                })
                if chosen_row is None and mn_gate >= args.operate_purity:
                    chosen_row = row
            ladder.append(row)
        if chosen_row is None:
            # No stream satisfies the operating purity; take the purest feasible
            # stage rather than the largest stream, otherwise the pair leaves
            # the template's region entirely.
            rows = [r for r in ladder if "snapshot" in r]
            if not rows:
                raise SystemExit("%s: no stream reaches the trailer" % tidy)
            chosen_row = rows[0]
        chosen = chosen_row["snapshot"]
        p, rec, f1, mprec, mrec = stats[chosen][tidy]
        meta = meta_all[chosen]
        best = {
            "ladder": [{k: v for k, v in r.items() if k != "snapshot"} for r in ladder],
            "operating_point": {"mnemonic_purity": round(mprec, 4),
                                "counter_precision": round(p, 4),
                                "coverage": round(mrec, 4)},
            "ceiling": {
                # exhaustive over the corpus, not over the ladder picks
                "max_coverage_any_purity": round(
                    max(stats[n][tidy][4] for n in snap_region), 4),
                "max_coverage_at_full_purity": round(
                    max((stats[n][tidy][4] for n in snap_region
                         if stats[n][tidy][3] >= 1.0 and trailer_ok(n)), default=0.0), 4),
                "max_insns_at_full_purity": max(
                    (snap_insns[n] for n in snap_region
                     if stats[n][tidy][3] >= 1.0 and trailer_ok(n)), default=0),
            },
            "snapshot": chosen, "candidate_sha256": meta["candidate_sha256"],
            "source": meta["source"], "insns": snap_insns[chosen],
            "precision": round(p, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "mnemonic_precision": round(mprec, 4), "mnemonic_recall": round(mrec, 4),
            "template_mnemonics": sorted(rt_mn),
            "stream_mnemonics": sorted(snap_mn[chosen]),
            "foreign_mnemonics": sorted(snap_mn[chosen] - rt_mn),
            "trailer": True, "pc_offset": meta["pc_offset"], "code_bytes": meta["code_bytes"],
            "region_size": len(snap_region[chosen]),
            "template_region_size": len(regions_t[tidy]),
            "shared_with": shared(chosen),
            "match": ("exact" if mprec >= 1.0 and mrec >= 1.0 else
                      "pure" if mprec >= 1.0 else
                      "near" if mprec >= args.operate_purity else "partial"),
        }
        alt = sorted((n for n in snap_region if n != chosen
                      and stats[n][tidy][3] >= args.operate_purity and trailer_ok(n)),
                     key=lambda n: -stats[n][tidy][4])[:3]
        best["alternatives"] = [{
            "snapshot": n, "purity": round(stats[n][tidy][3], 4),
            "coverage": round(stats[n][tidy][4], 4),
            "insns": snap_insns[n], "source": meta_all[n]["source"],
        } for n in alt]
        selection[tidy] = best

        b_uc = uc_region(uc, NOP.to_bytes(4, "little"), tmp)
        r_uc_t = uc_region(uc, (work / ("%s.text" % tidy)).read_bytes(), tmp) - b_uc
        r_uc_s = uc_region(uc, snap_code[chosen], tmp) - b_uc
        inter = len(r_uc_s & r_uc_t)
        best["unicorn"] = {
            "template_size": len(r_uc_t), "stream_size": len(r_uc_s),
            "precision": round(inter / len(r_uc_s), 4) if r_uc_s else 0.0,
            "recall": round(inter / len(r_uc_t), 4) if r_uc_t else 0.0,
        }
        log("%s: %s insns=%d purity=%.2f cover=%.2f (%d/%d mn) counter p=%.2f shared=%s"
            % (tidy, chosen[:12], snap_insns[chosen], mprec, mrec,
               len(snap_mn[chosen] & rt_mn), len(rt_mn), p, best["shared_with"]))

    # What the corpus as a whole can reach, independent of any selection:
    # a template mnemonic that no snapshot ever contains cannot be paired at all.
    reach = {}
    mn_counts = Counter()
    for mns in snap_mn_all.values():
        for m in mns:
            mn_counts[m] += 1
    for tidy in templates:
        counts = {m: mn_counts.get(m, 0) for m in sorted(templates_mn[tidy])}
        reach[tidy] = {
            "template_mnemonics": len(templates_mn[tidy]),
            "reachable": sum(1 for v in counts.values() if v),
            "missing": sorted(m for m, v in counts.items() if not v),
            "counts": counts,
        }
        rare = {m: v for m, v in counts.items() if 0 < v <= 10}
        log("%s: mnemonic counts %s%s" % (tidy, counts,
                                          ("; rare<=10: %s" % rare) if rare else ""))

    (work / "selection.json").write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reachability": reach,
        "templates": templates,
        "selection": selection,
        "fingerprint": {"driver_cap_sha256": sha256_file(cap),
                        "driver_uc_sha256": sha256_file(uc),
                        "baseline_counters": len(base),
                        "distinct_words": len(set(all_words)),
                        "candidates_measured": len(snap_region)},
    }, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: verify
# --------------------------------------------------------------------------
def parse_json_lines(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def verify(args):
    work = Path(args.work)
    sel = json.loads((work / "selection.json").read_text())
    selection = sel["selection"]
    vdir = work / "verify"
    vdir.mkdir(exist_ok=True)
    all_snaps = work / "snapshots_all"
    if all_snaps.exists():
        shutil.rmtree(all_snaps)
    all_snaps.mkdir()

    out = {}
    for tidy, s in selection.items():
        snap = next((work / "corpus").rglob(s["snapshot"]))
        loaded = sfsnapshot.load(str(snap))
        code = None
        for mm in loaded.mappings:
            if mm.start == CODE_BASE:
                code = mm.data
                break
        if code is None:
            raise SystemExit("%s: no code mapping" % tidy)
        payload = code[:-4]
        if sha256_bytes(payload) != s["candidate_sha256"]:
            raise SystemExit("%s: snapshot code differs from the selected candidate" % tidy)
        audit = {
            "snapshot": snap.name,
            "snapshot_sha256": sha256_file(snap),
            "snapshot_bytes": snap.stat().st_size,
            "code_sha256": sha256_bytes(payload),
            "insns": len(payload) // 4,
            "region_precision": s["precision"],
            "region_recall": s["recall"],
            "region_f1": s["f1"],
            "region_match": s["match"],
            "mnemonic_precision": s.get("mnemonic_precision"),
            "mnemonic_recall": s.get("mnemonic_recall"),
            "template_mnemonics": s.get("template_mnemonics", []),
            "stream_mnemonics": s.get("stream_mnemonics", []),
            "foreign_mnemonics": s.get("foreign_mnemonics", []),
            "unicorn": s["unicorn"],
            "source": s["source"],
            "pc_offset": s["pc_offset"],
            "code_bytes": s["code_bytes"],
            "trailer": s["trailer"],
            "signal": loaded.end_states[0].signal,
            "end_states": len(loaded.end_states),
        }
        replays = []
        for core in (0, 32, 64, 96):
            proc = run([SF_PLAYER, "--snapshot", snap, "--core", str(core), "--repeat", "3"])
            runs = parse_json_lines(proc.stdout)
            if len(runs) != 3 or not all(r.get("ok") and r.get("match") for r in runs):
                raise SystemExit("%s: replay failed on core %d" % (tidy, core))
            replays.append({"core": core, "runs": runs})
        audit["replay"] = replays
        shutil.copy2(snap, all_snaps / (tidy + ".sfs"))
        out[tidy] = audit
        log("%s: audit+replay ok (p=%.3f r=%.3f trailer=%s)"
            % (tidy, s["precision"], s["recall"], s["trailer"]))

    checks = {}
    for mode, extra in (("sweep", []), ("sampled", ["--batch-size", "50", "--execs-per-batch", "1000"])):
        proc = run([SF_CHECKER, "--corpus", all_snaps, "--cores", args.cores,
                    "--seconds", str(args.sweep_seconds), "--mode", mode,
                    "--out", vdir / ("check-" + mode)] + extra,
                   timeout=args.sweep_seconds + 600)
        summary = parse_json_lines(proc.stdout)[-1]
        checks[mode] = summary
        if summary["mismatches"] or summary["errors"] or summary["executions"] == 0:
            raise SystemExit("%s checker reported a problem: %s" % (mode, summary))
        log("%s: executions=%s mismatches=%s" % (mode, summary["executions"], summary["mismatches"]))

    proc = run([sys.executable, FLEET, "--corpus", all_snaps, "--db", vdir / "fleet.db",
                "--out-root", vdir / "fleet", "--cores", args.cores,
                "--window-cores", "4", "--window-seconds", str(args.fleet_seconds),
                "--windows", str(args.fleet_windows), "--mode", "sweep"],
               timeout=args.fleet_seconds * args.fleet_windows + 900)
    checks["fleet"] = {"summary": proc.stdout.strip().splitlines()[-1:]}
    log("fleet: %s" % checks["fleet"]["summary"])

    (vdir / "verify.json").write_text(json.dumps({"checks": checks, "pairs": out}, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: report
# --------------------------------------------------------------------------
def report(args):
    work = Path(args.work)
    sel = json.loads((work / "selection.json").read_text())
    templates = sel["templates"]
    selection = sel["selection"]
    corpus = json.loads((work / "corpus.json").read_text())
    ver = json.loads((work / "verify" / "verify.json").read_text())
    checks = ver["checks"]

    pairs = []
    for tidy, s in selection.items():
        a = ver["pairs"][tidy]
        pairs.append({
            "template": templates[tidy],
            "stream": {
                "snapshot": a["snapshot"], "snapshot_sha256": a["snapshot_sha256"],
                "candidate_sha256": a["code_sha256"], "insns": a["insns"],
                "source": a["source"], "region_size": s["region_size"],
                "precision": a["region_precision"], "recall": a["region_recall"],
                "f1": a["region_f1"], "match": a["region_match"],
                "mnemonic_precision": a.get("mnemonic_precision"),
                "mnemonic_recall": a.get("mnemonic_recall"),
                "template_mnemonics": a.get("template_mnemonics", []),
                "stream_mnemonics": a.get("stream_mnemonics", []),
                "foreign_mnemonics": a.get("foreign_mnemonics", []),
                "unicorn": a["unicorn"],
                "pc_offset": a["pc_offset"], "code_bytes": a["code_bytes"],
                "trailer": a["trailer"], "shared_with": s.get("shared_with", []),
            },
            "alternatives": s.get("alternatives", []),
            "replay": {"cores": [r["core"] for r in a["replay"]], "runs_per_core": 3},
        })

    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": os.uname().nodename, "machine": os.uname().machine,
        "mode": "paper-faithful",
        "generation": {
            "ifuzz": "syzkaller arm64 user-mode table, no filters, defaults (1..24 insns)",
            "capstone_proxy": "bin/capstone_fuzz (libFuzzer, 1 instruction per input)",
            "unicorn_proxy": "bin/unicorn_fuzz (libFuzzer, 4 KiB @0x10000000, 1000 insns)",
            "fixer": "--ref-cores 0,32,64,96 --repeat 3, default 4 data pages, no targeting flags",
            "candidates": corpus["candidates"], "fixer_stats": corpus["fixer"],
            "accepted": corpus["accepted"], "accepted_by_source": corpus["accepted_by_source"],
        },
        "region_definition": {
            "formula": "R(x) = union(F(w) for w in words(x)) - F(nop)",
            "F": "SanitizerCoverage counters inside instrumented libcapstone for decoding w",
            "rationale": "Capstone proxy decodes one instruction per input, so a template's "
                         "region is the union over its instructions; same rule for streams",
            "driver": [sha256_file(work / "bin" / "cov_cap"), sha256_file(work / "bin" / "cov_uc")],
        },
        "reachability": sel.get("reachability", {}),
        "pairs": pairs,
        "corpus_checks": checks,
    }
    (work / "final").mkdir(exist_ok=True)
    (work / "final" / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    def fmt(x):
        return "%.3f" % x

    lines = [
        "# 严格按原文的三代理语料与「覆盖区域」配对（ARM64，2026-11-23）",
        "",
        "生成端完全不做定向：ifuzz（默认表、无过滤）、Capstone 代理、Unicorn 代理；",
        "定向只发生在事后——按每条流在 **代理内部** 占据的解码区域与模板比对。",
        "",
        "## 语料",
        "",
        "| 来源 | 候选 | 修复后收录 |",
        "| --- | --- | --- |",
    ]
    for src, n in corpus["candidates"].items():
        lines.append("| %s | %d | %d |" % (src, n, corpus["accepted_by_source"].get(src, 0)))
    lines += [
        "| 合计 | %d | %d |" % (sum(corpus["candidates"].values()), corpus["accepted"]),
        "",
        "fixer 拒绝：%s" % json.dumps(corpus["fixer"]["reasons"], ensure_ascii=False),
        "",
        "## 区域配对",
        "",
        "`R(x) = ∪ F(w) − F(nop)`，`F(w)` 为代理解码 `w` 时在插桩 Capstone 内命中的计数器集合。",
        "",
        "| 模板 | 模板指令 | 流指令 | 纯度 | 覆盖(助记符) | 计数器精确率 | 计数器召回 | 匹配 | 来源 | 区域共享 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for p in pairs:
        s = p["stream"]
        shared = p.get("shared_with") or []
        lines.append("| %s | %d | %d | %s | %d/%d | %s | %s | %s | %s | %s |" % (
            p["template"]["id"], p["template"]["insns"], s["insns"],
            fmt(s["mnemonic_precision"]),
            len(s["stream_mnemonics"]) - len(s["foreign_mnemonics"]),
            len(s.get("template_mnemonics") or []),
            fmt(s["precision"]), fmt(s["recall"]), s["match"], s["source"],
            ", ".join(shared) if shared else "—"))
    lines += [
        "",
        "## Unicorn 侧（执行区域，次要口径）",
        "",
        "Capstone 代理只解码一条指令，所以上面的区域是**解码路径**的并集；Unicorn 侧只能按整条流测量，",
        "且其覆盖率由 TCG/派遣代码主导（任意输入都命中 ~1346 个计数器），信号很弱，仅作辅助核对。",
        "",
        "| 模板 | 模板执行区域 | 流执行区域 | 精确率 | 召回率 |",
        "| --- | --- | --- | --- | --- |",
    ] + [
        "| %s | %d | %d | %s | %s |" % (
            p["template"]["id"], p["stream"]["unicorn"]["template_size"],
            p["stream"]["unicorn"]["stream_size"],
            fmt(p["stream"]["unicorn"]["precision"]), fmt(p["stream"]["unicorn"]["recall"]))
        for p in pairs
    ] + [
        "",
        "## 语料可达性（选流之前就存在的上限）",
        "",
        "统计口径：{:,} 条语料**全部**计入（含单指令快照），表中数字是「含该助记符的快照条数」。"
        .format(corpus["accepted"]),
        "",
        "| 模板 | 模板助记符 | 有出现 | 稀有(≤10 条) | 从未出现 |",
        "| --- | --- | --- | --- | --- |",
    ] + [
        "| %s | %d | %d | %s | %s |" % (
            k, v["template_mnemonics"], v["reachable"],
            ", ".join("%s×%d" % (m, c) for m, c in sorted(v["counts"].items()) if 0 < c <= 10) or "—",
            ", ".join(v.get("missing") or []) or "—")
        for k, v in (sel.get("reachability") or {}).items()
    ] + [
        "",
        "典型例子：o2 的 `b.ne` 出现 0 次（ifuzz 的 B.cond 条目只编码 b.eq，代理也没随机到）；",
        "v1/v6 的 `dup` 各 15 条；v5 的 LSE 里 casa/casal/ldadd 各 1 条，其余 4 种为 0。",
        "也就是说这些区域「能到但极稀有」，稀有到凑不出「两条以上且在区域内」的流。",
        "",
        "## 机群校验",
        "",
        "| 模式 | 核 | 执行次数 | 不匹配 | 错误 |",
        "| --- | --- | --- | --- | --- |",
        "| sweep | %s | %s | %s | %s |" % (
            checks["sweep"]["cores"], checks["sweep"]["executions"],
            checks["sweep"]["mismatches"], checks["sweep"]["errors"]),
        "| sampled 50/1000 | %s | %s | %s | %s |" % (
            checks["sampled"]["cores"], checks["sampled"]["executions"],
            checks["sampled"]["mismatches"], checks["sampled"]["errors"]),
        "",
        "## 与 pairgen.py（定向生成）的区别",
        "",
        "- 本流程的候选**不受任何指令类约束**：v5 的 LSE、v6 的 CRC 只能来自代理语料，",
        "  而不是靠给 ifuzz 打补丁。",
        "- 因此「一个模板对应一条流」的含义也随之改变：不再是「覆盖模板全部编码类」，",
        "  而是「流占据的解码区域落在模板区域之内（精确率）并尽量多覆盖（召回率）」。",
        "- 精确率 = |R(流)∩R(模板)| / |R(流)|；召回率 = |R(流)∩R(模板)| / |R(模板)|。",
        "  单个快照很短，召回率天然受限；这是原文「覆盖无关生成」的直接后果，不做粉饰。",
        "",
    ]
    (work / "final" / "pairs.md").write_text("\n".join(lines))
    if args.copy_to:
        dest = Path(args.copy_to)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / "final" / "manifest.json", dest / "manifest.json")
        shutil.copy2(work / "final" / "pairs.md", dest / "pairs.md")
        shutil.copytree(work / "snapshots_all", dest / "snapshots", dirs_exist_ok=True)
        log("copied to %s" % dest)
    log("report: %d pairs" % len(pairs))


# --------------------------------------------------------------------------
def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--work", required=True)
        p.add_argument("--seeds", default=str(DEFAULT_SEEDS))

    p = sub.add_parser("corpus"); common(p)
    p.add_argument("--ifuzz-n", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--cap-seconds", type=int, default=180)
    p.add_argument("--uc-seconds", type=int, default=180)
    p.add_argument("--ref-cores", default="0,32,64,96")
    p.add_argument("--reuse-corpus", action="store_true",
                   help="skip generation/fixing, only rebuild corpus.json")

    p = sub.add_parser("regions"); common(p)
    p.add_argument("--precision", type=float, default=0.9)
    p.add_argument("--min-region", type=int, default=16)
    p.add_argument("--min-decoded", type=int, default=2)
    p.add_argument("--operate-purity", type=float, default=0.8)
    p.add_argument("--min-counter-precision", type=float, default=0.9)

    p = sub.add_parser("verify"); common(p)
    p.add_argument("--cores", default="0-127")
    p.add_argument("--sweep-seconds", type=int, default=30)
    p.add_argument("--fleet-seconds", type=int, default=60)
    p.add_argument("--fleet-windows", type=int, default=2)

    p = sub.add_parser("report"); common(p)
    p.add_argument("--copy-to", default="")
    p.add_argument("--sweep-seconds", type=int, default=30)
    p.add_argument("--fleet-seconds", type=int, default=60)
    p.add_argument("--fleet-windows", type=int, default=2)

    p = sub.add_parser("all"); common(p)
    p.add_argument("--ifuzz-n", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--cap-seconds", type=int, default=180)
    p.add_argument("--uc-seconds", type=int, default=180)
    p.add_argument("--ref-cores", default="0,32,64,96")
    p.add_argument("--reuse-corpus", action="store_true",
                   help="skip generation/fixing, only rebuild corpus.json")
    p.add_argument("--precision", type=float, default=0.9)
    p.add_argument("--min-region", type=int, default=16)
    p.add_argument("--min-decoded", type=int, default=2)
    p.add_argument("--operate-purity", type=float, default=0.8)
    p.add_argument("--min-counter-precision", type=float, default=0.9)
    p.add_argument("--cores", default="0-127")
    p.add_argument("--sweep-seconds", type=int, default=30)
    p.add_argument("--fleet-seconds", type=int, default=60)
    p.add_argument("--fleet-windows", type=int, default=2)
    p.add_argument("--copy-to", default="")

    args = ap.parse_args()
    Path(args.work).mkdir(parents=True, exist_ok=True)
    if args.cmd in ("corpus", "all"):
        corpus(args)
    if args.cmd in ("regions", "all"):
        regions(args)
    if args.cmd in ("verify", "all"):
        verify(args)
    if args.cmd in ("report", "all"):
        report(args)


if __name__ == "__main__":
    main()
