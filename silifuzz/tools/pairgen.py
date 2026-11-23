#!/usr/bin/env python3
"""Pair every sdcfuzz microarchitectural template with one SiliFuzz stream.

The pipeline is the SiliFuzz one end to end:

    template (.S) -> instruction-class contract
                  -> ifuzz generation restricted to those classes
                  -> candidate selection (full class coverage, min JS divergence)
                  -> sf_fix   (end-state repair on reference cores)
                  -> sf_player (replay on 4 cores)
                  -> sf_checker (128-core sweep + 50/1000 sampling)
                  -> fleet.py  (4-core windows)

"Correspondence" is defined on the instruction *encoding class* reported by
ifuzz's own decoder (arm64.ParseInsn), not on objdump text: objdump rewrites
MOVZ/CMP/SUBS into aliases (mov/cmp/subs) and would silently break the match.

Every stage writes JSON evidence; ``report`` merges it into a manifest and a
human-readable table.  A pair only counts as delivered when the snapshot that
was replayed is the snapshot that was audited.

Usage:
  pairgen.py analyze  --work work/pairs-YYYYMMDD
  pairgen.py generate --work ... --n 400
  pairgen.py fix      --work ...
  pairgen.py verify   --work ... --sweep-seconds 30 --fleet-seconds 60
  pairgen.py report   --work ... [--copy-to DIR]
  pairgen.py all      --work ... --copy-to DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IFUZZ = ROOT / "bin" / "ifuzzgen"
SF_FIX = ROOT / "bin" / "sf_fix"
SF_PLAYER = ROOT / "bin" / "sf_player"
SF_CHECKER = ROOT / "bin" / "sf_checker"
FLEET = ROOT / "tools" / "fleet.py"

sys.path.insert(0, str(ROOT / "tools"))
import sfsnapshot  # noqa: E402

CODE_BASE = sfsnapshot.CODE_BASE
DEFAULT_SEEDS = ROOT.parent / "sdcfuzz" / "upstream" / "seeds"
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


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def log(msg):
    print("[pairgen] " + msg, flush=True)


def run(cmd, timeout=1800, check=True):
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise SystemExit(
            "command failed (%d): %s\nstdout:\n%s\nstderr:\n%s"
            % (proc.returncode, " ".join(cmd), proc.stdout[-4000:], proc.stderr[-4000:])
        )
    return proc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def words_from_bytes(data: bytes):
    n = len(data) // 4
    return [int.from_bytes(data[i * 4 : i * 4 + 4], "little") for i in range(n)]


def words_from_object(path: Path):
    proc = run(["objdump", "-d", path])
    out = []
    for line in proc.stdout.splitlines():
        m = re.match(r"^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s", line)
        if m:
            out.append(int(m.group(1), 16))
    return out


def alias_set(name: str):
    """objdump-style vocabulary of a table entry name."""
    out = set()
    for part in name.split(","):
        tok = part.strip().split(" ")[0].strip().lower()
        if tok:
            out.add(tok)
    return out


BRANCH_CLASSES = {"B", "B.cond", "CBZ", "CBNZ", "TBZ", "TBNZ"}


def branch_displacement(word: int, cls: str):
    """Signed displacement field of a branch encoding, or None if not a branch."""
    if cls == "B":
        return word & 0x3FFFFFF
    if cls in ("B.cond", "CBZ", "CBNZ"):
        return (word >> 5) & 0x7FFFF
    if cls in ("TBZ", "TBNZ"):
        return (word >> 5) & 0x3FFF
    return None


REG_FIELDS = ("Rn", "Rd", "Rm", "Rt", "Rt2", "Ra", "Rs")
BASE_REGS = (18, 19, 20, 21, 22, 23, 24, 25)
DATA_REGS = tuple(r for r in range(31) if r not in BASE_REGS)


def build_variants(table, classes, per_entry=8, seed=1):
    """Assembler-validated register variants of every allowed encoding.

    The upstream field tables are not always aligned with the encoding (some
    put Rm at bit 20), so a blind write produces unallocated or re-classified
    words.  Every candidate here must (a) still classify to the same ifuzz
    class and (b) decode to a real instruction.
    """
    import random
    rng = random.Random(seed)
    kept, dropped_class, dropped_invalid, no_fields = set(), 0, 0, 0
    for e in table.entries:
        if e["name"] not in classes or e["pseudo"]:
            continue
        regs = [f for f in e.get("fields") or [] if f["name"] in REG_FIELDS]
        if not regs:
            # No field table: the word cannot be varied, keep it as it is.
            if encoding_valid(e["as_uint32"]):
                kept.add(e["as_uint32"])
            no_fields += 1
            continue
        added = 0
        for _ in range(per_entry):
            w = e["as_uint32"]
            chosen = {}
            for f in regs:
                pool = BASE_REGS if f["name"] == "Rn" else DATA_REGS
                reg = rng.choice(pool)
                if f["name"] == "Rt2" and reg == chosen.get("Rt"):
                    continue
                chosen[f["name"]] = reg
                mask = ((1 << f["len"]) - 1) << f["start"]
                w = (w & ~mask) | (reg << f["start"])
            if table.classify(w) != e["name"]:
                dropped_class += 1
                continue
            if not encoding_valid(w):
                dropped_invalid += 1
                continue
            kept.add(w)
            added += 1
        if added == 0 and encoding_valid(e["as_uint32"]):
            # Every variant was rejected; fall back to the upstream word.
            kept.add(e["as_uint32"])
    return sorted(kept), {"variants_kept": len(kept), "dropped_reclassified": dropped_class,
                          "dropped_invalid": dropped_invalid, "entries_without_fields": no_fields}


class Table:
    """Mirror of arm64.ParseInsn: first entry whose masked opcode matches wins."""

    def __init__(self, entries):
        self.entries = entries

    @classmethod
    def load(cls, path: Path, lse=True):
        cmd = [IFUZZ]
        if lse:
            cmd.append("-lse")
            cmd.append("-branch-ext")
            cmd.append("-vec-ext")
        cmd += ["-table-json", path]
        run(cmd)
        data = json.loads(path.read_text())
        return cls([e for e in data if not e["pseudo"]])

    def classify(self, word: int):
        for e in self.entries:
            if word & e["mask"] == e["opcode"]:
                return e["name"]
        return None

    def opcodes_for(self, names):
        return sorted(
            {e["as_uint32"] for e in self.entries if e["name"] in names and not e["pseudo"]}
        )

    def names_for_mnemonic(self, mnemonic: str):
        return sorted(e["name"] for e in self.entries if mnemonic in alias_set(e["name"]))


_ENCODING_VALIDITY = {}


def encoding_valid(word: int) -> bool:
    """Ask the system disassembler whether a single word is allocated.

    The upstream ifuzz table contains words the architecture leaves
    unallocated (e.g. 32-bit ADD with ROR shift); executing one raises SIGILL,
    which would end a stream before it runs its body.
    """
    if word in _ENCODING_VALIDITY:
        return _ENCODING_VALIDITY[word]
    fd, path = tempfile.mkstemp(suffix=".bin")
    try:
        os.write(fd, word.to_bytes(4, "little"))
        os.close(fd)
        out = run(["objdump", "-D", "-b", "binary", "-m", "aarch64", path]).stdout
        ok = "undefined" not in out and ".inst" not in out
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    _ENCODING_VALIDITY[word] = ok
    return ok


def jensen_shannon(c1: Counter, c2: Counter) -> float:
    keys = set(c1) | set(c2)
    n1 = sum(c1.values()) or 1
    n2 = sum(c2.values()) or 1
    js = 0.0
    for k in keys:
        p = c1.get(k, 0) / n1
        q = c2.get(k, 0) / n2
        m = (p + q) / 2
        if p > 0:
            js += 0.5 * p * math.log(p / m, 2)
        if q > 0:
            js += 0.5 * q * math.log(q / m, 2)
    return js


# --------------------------------------------------------------------------
# stage: analyze
# --------------------------------------------------------------------------
def discover_templates(seeds_dir: Path):
    out = []
    for p in sorted(seeds_dir.glob("*.S")):
        if p.name.startswith("asm_common"):
            continue
        tidy = p.name.split("_")[0]
        out.append((tidy, p))
    return out


def analyze(args):
    work = Path(args.work)
    seeds_dir = Path(args.seeds).resolve()
    for sub in ("filters", "pool", "selected", "snapshots", "verify", "final", "obj"):
        (work / sub).mkdir(parents=True, exist_ok=True)
    table = Table.load(work / "table_lse.json")

    templates = {}
    for tidy, src in discover_templates(seeds_dir):
        obj = work / "obj" / (tidy + ".o")
        run(["gcc", "-c", "-I", seeds_dir, src, "-o", obj])
        words = words_from_object(obj)
        classes = [table.classify(w) for w in words]
        unknown = [(hex(w)) for w, c in zip(words, classes) if c is None]
        if unknown:
            raise SystemExit("%s: %d instruction(s) outside the ifuzz vocabulary: %s"
                             % (tidy, len(unknown), ", ".join(unknown[:8])))
        counts = Counter(classes)
        # A zero-displacement branch is a self-loop: the fixer can only reject
        # such a stream as a timeout, so the allow-list keeps the class but
        # drops the degenerate encoding.
        usable = set()
        for e in table.entries:
            if e["pseudo"] or e["name"] not in counts:
                continue
            if e["name"] in BRANCH_CLASSES and branch_displacement(e["as_uint32"], e["name"]) == 0:
                continue
            usable.add(e["name"])
        if not usable:
            raise SystemExit("%s: no usable classes" % tidy)
        allowed, varstats = build_variants(table, usable, per_entry=args.variants,
                                           seed=args.seed)
        if not allowed:
            raise SystemExit("%s: no encodings selectable" % tidy)
        filt = work / "filters" / (tidy + ".opcodes")
        body = ["# validated word list for %s (%s)" % (tidy, src.name),
                "# <hex word>\t<ifuzz class>; every word decodes and classifies as labelled"]
        body += ["0x%08x\t%s" % (v, table.classify(v)) for v in allowed]
        filt.write_text("\n".join(body) + "\n")
        templates[tidy] = {
            "id": tidy,
            "module": MODULES.get(tidy[0], "unknown"),
            "source": src.name,
            "source_sha256": sha256_file(src),
            "object_sha256": sha256_file(obj),
            "total_insns": len(words),
            "classes": sorted(counts),
            "class_counts": dict(sorted(counts.items())),
            "allowed_encodings": len(allowed),
            "filter": str(filt.relative_to(work)),
            "unknown": unknown,
            "variant_stats": varstats,
        }
        log("%s: %d insns, %d classes, %d validated encodings (reclassified %d, "
            "unallocated %d)"
            % (tidy, len(words), len(counts), len(allowed),
               varstats["dropped_reclassified"], varstats["dropped_invalid"]))

    (work / "templates.json").write_text(json.dumps(
        {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "templates": templates},
        indent=2, ensure_ascii=False) + "\n")
    log("analyze: %d templates" % len(templates))


# --------------------------------------------------------------------------
# stage: generate
# --------------------------------------------------------------------------
def generate(args):
    work = Path(args.work)
    meta = json.loads((work / "templates.json").read_text())
    templates = meta["templates"]
    table = Table.load(work / "table_lse.json")
    selected = {}

    for tidy, t in templates.items():
        k = len(t["classes"])
        lo = max(t["total_insns"], int(2.5 * k))
        hi = lo + 6
        best = None
        rounds = []
        for r in range(5):
            pool = work / "pool" / tidy / ("r%d" % r)
            if pool.exists():
                shutil.rmtree(pool)
            manifest = work / "pool" / tidy / ("r%d.jsonl" % r)
            seed = args.seed + r * 7919
            run([IFUZZ, "-n", args.n, "-seed", seed, "-min-insns", lo,
                 "-max-insns", hi, "-lse", "-branch-ext", "-vec-ext", "-balance-classes",
                 "-words", work / t["filter"],
                 "-out", pool, "-manifest", manifest])
            cands = sorted(pool.rglob("*.bin"))
            scored = []
            invalid_rejected = 0
            for c in cands:
                data = c.read_bytes()
                words = words_from_bytes(data)
                cls = [table.classify(w) for w in words]
                if any(x is None for x in cls):
                    continue
                if not all(encoding_valid(w) for w in words):
                    invalid_rejected += 1
                    continue
                cover = set(cls) & set(t["classes"])
                if len(cover) < k:
                    scored.append((len(cover) / k, c, cls))
                    continue
                hist = Counter(cls)
                js = jensen_shannon(Counter(t["class_counts"]), hist)
                ratio = len(cls) / max(1, t["total_insns"])
                scored.append((1.0, c, cls, js, ratio))
            full = [s for s in scored if s[0] == 1.0]
            rounds.append({"round": r, "seed": seed, "len_lo": lo, "len_hi": hi,
                           "generated": len(cands), "full_coverage": len(full),
                           "invalid_encodings": invalid_rejected})
            log("%s r%d: %d candidates, %d full-coverage, %d with unallocated words (len %d-%d)"
                % (tidy, r, len(cands), len(full), invalid_rejected, lo, hi))
            if full:
                full.sort(key=lambda s: (s[3], abs(s[4] - 1.0), sha256_file(s[1])))
                best = full[0]
                break
            lo += 8
            hi += 8
        if best is None:
            raise SystemExit("%s: no candidate achieved full class coverage" % tidy)

        cov, path, cls, js, ratio = best
        data = path.read_bytes()
        digest = sha256_bytes(data)
        # Keep a ranked pool: the fixer later rejects streams that die before
        # reaching their trailer (self-zeroing x0 + load, undefined encodings),
        # so selection cannot be decided from static scoring alone.
        ranked = sorted(
            [s for s in scored if s[0] == 1.0],
            key=lambda s: (s[3], abs(s[4] - 1.0), sha256_file(s[1])),
        )[: args.keep]
        alt_dir = work / "alt" / tidy
        if alt_dir.exists():
            shutil.rmtree(alt_dir)
        alt_dir.mkdir(parents=True)
        pool_meta = []
        for _, cand_path, cand_cls, cand_js, cand_ratio in ranked:
            cand_data = cand_path.read_bytes()
            cand_sha = sha256_bytes(cand_data)
            (alt_dir / (cand_sha + ".bin")).write_bytes(cand_data)
            pool_meta.append({"sha256": cand_sha, "insns": len(cand_cls),
                              "length_ratio": round(cand_ratio, 3),
                              "js_divergence": round(cand_js, 6),
                              "class_counts": dict(sorted(Counter(cand_cls).items()))})
        (work / "alt" / (tidy + ".json")).write_text(json.dumps(pool_meta, indent=2) + "\n")

        out_dir = work / "selected" / tidy
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        (out_dir / (digest + ".bin")).write_bytes(data)
        selected[tidy] = {
            "id": tidy,
            "candidate_sha256": digest,
            "insns": len(cls),
            "length_ratio": round(ratio, 3),
            "coverage": 1.0,
            "js_divergence": round(js, 6),
            "classes": sorted(set(cls)),
            "class_counts": dict(sorted(Counter(cls).items())),
            "missing_classes": sorted(set(t["classes"]) - set(cls)),
            "extra_classes": sorted(set(cls) - set(t["classes"])),
            "seed_path": str(path.relative_to(work)),
            "rounds": rounds,
            "pool_size": len(pool_meta),
        }
        log("%s: selected %s (%d insns, JS=%.4f)" % (tidy, digest[:12], len(cls), js))

    (work / "selected.json").write_text(json.dumps(
        {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "selected": selected},
        indent=2, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# stage: fix
# --------------------------------------------------------------------------
def fix(args):
    """Repair every ranked candidate and keep only streams that reach their end.

    sf_fix is the execution oracle here: a candidate that faults on instruction
    3 (typically a table word zeroing x0 followed by a load through x0) produces
    a perfectly deterministic snapshot, but it never exercises the template's
    instruction mix.  Snapshots whose end-state PC stops short of the trailer
    are recorded and discarded, and the next candidate is taken instead.
    """
    work = Path(args.work)
    templates = json.loads((work / "templates.json").read_text())["templates"]
    results = {}
    for tidy, t in templates.items():
        alt_dir = work / "alt" / tidy
        if not (work / "alt" / (tidy + ".json")).exists():
            raise SystemExit("%s: no candidate pool, run generate first" % tidy)
        pool = json.loads((work / "alt" / (tidy + ".json")).read_text())
        by_fnv = {}
        for p in pool:
            data = (alt_dir / (p["sha256"] + ".bin")).read_bytes()
            by_fnv[sfsnapshot.fnv1a64(data)] = p
        out_dir = work / "snapshots_alt" / tidy
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        stats = work / "snapshots_alt" / (tidy + ".fix.json")
        run([SF_FIX, "--in", alt_dir, "--out", out_dir,
             "--source", "ifuzz-pair-lse",
             "--ref-cores", args.ref_cores, "--repeat", args.repeat,
             "--jobs", "8", "--centered-data", "--data-pages", "16",
             "--timeout-ms", "3000", "--stats", stats])
        payload = json.loads(stats.read_text())

        deep, shallow = [], []
        for sp in sorted(out_dir.rglob("*.sfs")):
            snap = sfsnapshot.load(str(sp))
            meta = json.loads(snap.meta)
            cand = by_fnv.get(int(meta["candidate"], 16))
            if cand is None:
                continue
            code_bytes = int(meta.get("code_bytes", cand["insns"] * 4))
            es = snap.end_states[0]
            rec = {
                "path": str(sp), "snapshot": sp.name, "candidate_sha256": cand["sha256"],
                "insns": cand["insns"], "js_divergence": cand["js_divergence"],
                "length_ratio": cand["length_ratio"], "code_bytes": code_bytes,
                "pc_offset": es.regs.pc - CODE_BASE, "signal": es.signal,
                "sig_addr": es.sig_addr,
            }
            # Reaching the trailer means landing on (or on the last instruction
            # of) the appended BRK.  A PC past the trailer means a forward
            # branch skipped the tail into padding, which is not a clean body
            # execution.
            landed = code_bytes - 4 <= rec["pc_offset"] <= code_bytes
            (deep if landed else shallow).append(rec)
        if not deep:
            raise SystemExit("%s: none of %d accepted snapshots reached its trailer"
                             % (tidy, len(shallow)))
        deep.sort(key=lambda r: (r["js_divergence"], abs(r["length_ratio"] - 1.0),
                                 r["candidate_sha256"]))
        pick = deep[0]
        dest = work / "snapshots" / tidy
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        final = dest / Path(pick["path"]).name
        shutil.copy2(pick["path"], final)
        results[tidy] = {
            "candidate_sha256": pick["candidate_sha256"],
            "snapshot": final.name,
            "snapshot_path": str(final.relative_to(work)),
            "snapshot_sha256": sha256_file(final),
            "insns": pick["insns"],
            "js_divergence": pick["js_divergence"],
            "length_ratio": pick["length_ratio"],
            "code_bytes": pick["code_bytes"],
            "pc_offset": pick["pc_offset"],
            "signal": pick["signal"],
            "sig_addr": pick["sig_addr"],
            "pool_size": len(pool),
            "accepted": payload["accepted"],
            "accept_reasons": payload["reasons"],
            "deep": len(deep),
            "shallow": len(shallow),
            "shallow_examples": [
                {"candidate_sha256": r["candidate_sha256"], "pc_offset": r["pc_offset"],
                 "code_bytes": r["code_bytes"], "signal": r["signal"]}
                for r in shallow[:3]
            ],
            "fix_stats": payload,
        }
        log("%s: %d/%d accepted, %d reach trailer, picked %s (depth %d/%d, sig %d)"
            % (tidy, payload["accepted"], len(pool), len(deep),
               pick["candidate_sha256"][:12], pick["pc_offset"], pick["code_bytes"],
               pick["signal"]))
    (work / "fix.json").write_text(json.dumps(results, indent=2) + "\n")


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
    templates = json.loads((work / "templates.json").read_text())["templates"]
    selected = json.loads((work / "selected.json").read_text())["selected"]
    fixm = json.loads((work / "fix.json").read_text())
    table = Table.load(work / "table_lse.json")
    vdir = work / "verify"
    vdir.mkdir(parents=True, exist_ok=True)
    all_snaps = work / "snapshots_all"
    if all_snaps.exists():
        shutil.rmtree(all_snaps)
    all_snaps.mkdir()

    out = {}
    for tidy, t in templates.items():
        snap = work / fixm[tidy]["snapshot_path"]
        s = sfsnapshot.load(str(snap))
        code_maps = [m for m in s.mappings if m.start == CODE_BASE]
        if len(code_maps) != 1:
            raise SystemExit("%s: expected one code mapping, got %d" % (tidy, len(code_maps)))
        code = code_maps[0].data
        cand = (work / "alt" / tidy / (fixm[tidy]["candidate_sha256"] + ".bin")).read_bytes()
        # sf_fix appends the BRK exit word; everything before it must be the candidate
        if code[: len(cand)] != cand:
            raise SystemExit("%s: snapshot code is not the selected candidate" % tidy)
        trailer = code[len(cand):]
        words = words_from_bytes(code[: len(cand)])
        cls = [table.classify(w) for w in words]
        unknown = [hex(w) for w, c in zip(words, cls) if c is None]
        cover = set(cls) & set(t["classes"])
        audit = {
            "snapshot": snap.name,
            "snapshot_sha256": sha256_file(snap),
            "snapshot_bytes": snap.stat().st_size,
            "code_sha256": sha256_bytes(code[: len(cand)]),
            "matches_selected_candidate": True,
            "trailer_hex": trailer.hex(),
            "insns": len(words),
            "classes": sorted(set(cls)),
            "class_counts": dict(sorted(Counter(cls).items())),
            "unknown": unknown,
            "coverage": len(cover) / len(t["classes"]),
            "missing_classes": sorted(set(t["classes"]) - set(cls)),
            "end_states": len(s.end_states),
            "signal": s.end_states[0].signal if s.end_states else None,
        }
        if audit["coverage"] != 1.0 or unknown:
            raise SystemExit("%s: final artifact does not cover the template: %s" % (tidy, audit))

        # replay on four reference cores
        replays = []
        for core in (0, 32, 64, 96):
            proc = run([SF_PLAYER, "--snapshot", snap, "--core", str(core), "--repeat", "3"])
            runs = parse_json_lines(proc.stdout)
            if len(runs) != 3 or not all(r.get("ok") and r.get("match") for r in runs):
                raise SystemExit("%s: replay failed on core %d: %s" % (tidy, core, proc.stdout))
            replays.append({"core": core, "runs": runs})
        audit["replay"] = replays

        shutil.copy2(snap, all_snaps / (tidy + ".sfs"))
        out[tidy] = audit
        log("%s: audit ok, replay ok (4 cores x3), coverage=1.0" % tidy)

    # corpus-wide checker: full sweep and the paper's 50/1000 sampling
    checks = {}
    for mode, extra in (("sweep", []), ("sampled", ["--batch-size", "50", "--execs-per-batch", "1000"])):
        out_dir = vdir / ("check-" + mode)
        cmd = [SF_CHECKER, "--corpus", all_snaps, "--cores", args.cores,
               "--seconds", str(args.sweep_seconds), "--mode", mode, "--out", out_dir] + extra
        proc = run(cmd, timeout=args.sweep_seconds + 600)
        summary = parse_json_lines(proc.stdout)[-1]
        checks[mode] = summary
        log("%s: executions=%s mismatches=%s errors=%s"
            % (mode, summary["executions"], summary["mismatches"], summary["errors"]))
        if summary["mismatches"] or summary["errors"] or summary["executions"] == 0:
            raise SystemExit("%s checker reported a problem: %s" % (mode, summary))

    # 4-core fleet windows rotating over the whole machine
    fleet_dir = vdir / "fleet"
    proc = run([sys.executable, FLEET, "--corpus", all_snaps,
                "--db", vdir / "fleet.db", "--out-root", fleet_dir,
                "--cores", args.cores, "--window-cores", "4",
                "--window-seconds", str(args.fleet_seconds),
                "--windows", str(args.fleet_windows), "--mode", "sweep"],
               timeout=args.fleet_seconds * args.fleet_windows + 900)
    checks["fleet"] = {"stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
    log("fleet: %s" % proc.stdout.strip().splitlines()[-1:])

    (vdir / "verify.json").write_text(json.dumps(
        {"checks": checks, "pairs": out}, indent=2) + "\n")


# --------------------------------------------------------------------------
# stage: report
# --------------------------------------------------------------------------
def report(args):
    work = Path(args.work)
    templates = json.loads((work / "templates.json").read_text())["templates"]
    selected = json.loads((work / "selected.json").read_text())["selected"]
    fixm = json.loads((work / "fix.json").read_text())
    ver = json.loads((work / "verify" / "verify.json").read_text())

    pairs = []
    for tidy, t in templates.items():
        a = ver["pairs"][tidy]
        pairs.append({
            "template": {
                "id": tidy, "module": t["module"], "source": t["source"],
                "source_sha256": t["source_sha256"], "insns": t["total_insns"],
                "classes": t["classes"], "class_counts": t["class_counts"],
                "allowed_encodings": t["allowed_encodings"],
            },
            "stream": {
                "candidate_sha256": fixm[tidy]["candidate_sha256"],
                "snapshot": a["snapshot"], "snapshot_sha256": a["snapshot_sha256"],
                "insns": a["insns"], "classes": a["classes"],
                "class_counts": a["class_counts"], "coverage": a["coverage"],
                "js_divergence": fixm[tidy]["js_divergence"],
                "length_ratio": fixm[tidy]["length_ratio"],
                "pc_offset": fixm[tidy]["pc_offset"],
                "code_bytes": fixm[tidy]["code_bytes"],
                "generator": "ifuzz (arm64 user mode, -lse -branch-ext)",
                "pool_size": fixm[tidy]["pool_size"],
                "deep_candidates": fixm[tidy]["deep"],
                "shallow_candidates": fixm[tidy]["shallow"],
            },
            "fix": fixm[tidy]["fix_stats"],
            "replay": {"cores": [r["core"] for r in a["replay"]],
                       "runs_per_core": 3},
            "end_state": {"signal": a["signal"], "records": a["end_states"]},
            "execution": {
                "pc_offset": fixm[tidy]["pc_offset"],
                "code_bytes": fixm[tidy]["code_bytes"],
                "reached_trailer": fixm[tidy]["pc_offset"] >= fixm[tidy]["code_bytes"] - 4,
                "candidates_fixed": fixm[tidy]["accepted"],
                "candidates_reaching_trailer": fixm[tidy]["deep"],
                "candidates_ending_early": fixm[tidy]["shallow"],
            },
        })

    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": os.uname().nodename,
        "machine": os.uname().machine,
        "ifuzzgen_sha256": sha256_file(IFUZZ),
        "sf_fix_sha256": sha256_file(SF_FIX),
        "sf_player_sha256": sha256_file(SF_PLAYER),
        "sf_checker_sha256": sha256_file(SF_CHECKER),
        "pair_count": len(pairs),
        "policy": {
            "isa": "AArch64 (arm64 user mode)",
            "generator": "syzkaller ifuzz table + opt-in ARMv8.1 LSE and forward-branch forms",
            "registers": "Rn draws from x18-x25 which no instruction writes; other register "
                         "fields randomized (6 clones per encoding); every variant must still "
                         "decode to the same class",
            "correspondence": "identical instruction encoding classes (ifuzz ParseInsn); "
                              "every word validated as allocated and re-classified as labelled",
            "selection": "class coverage 1.0, minimum Jensen-Shannon divergence, "
                         "then end-state PC landing on the trailer BRK",
            "fix": "--centered-data --data-pages 16 --ref-cores 0,32,64,96 --repeat 3; "
                   "candidates ending before their trailer are discarded",
            "check": {"cores": "0-127", "sweep_seconds": args.sweep_seconds},
        },
        "corpus_checks": ver["checks"],
        "pairs": pairs,
    }
    (work / "final").mkdir(exist_ok=True)
    (work / "final" / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# sdcfuzz 模板 ↔ SiliFuzz 指令流配对（ARM64，全流水线）",
        "",
        "生成时间：%s　主机：%s（%s）" % (manifest["generated"], manifest["host"], manifest["machine"]),
        "",
        "## 方法",
        "",
        "1. **模板侧定契约**：每个 sdcfuzz 模板汇编为 `.o`，用 ifuzz 自己的解码器",
        "   （`arm64.ParseInsn`）把每条指令映射到编码类。不用 objdump 助记符做匹配，",
        "   因为它会把 `movz` 显示成 `mov`、`subs` 显示成 `cmp`，造成伪对应。",
        "2. **构造已验证词表**：对契约内每个表项生成寄存器变体（`Rn` 只取 x18–x25，",
        "   其余寄存器字段取 x0–x17/x26–x28），每个词必须同时满足（a）仍分类为同一类，",
        "   （b）被系统汇编器/反汇编器判为合法编码。上游表里有未分配编码和错位字段表，",
        "   这一层把它们全部挡掉，剔除数量逐模板记入 manifest。",
        "3. **生成**：`ifuzzgen -words` 以该词表为指令集、按编码类等概率抽样（`-balance-classes`），",
        "   每轮 400 个候选；只保留“全部指令合法 + 类覆盖 100%”的候选。",
        "4. **端态修复与执行深度**：候选经 `sf_fix`（4 参考核 × 3 次、`--centered-data`、16 数据页）",
        "   批量修复；只接受端态 PC **正好落在末尾 BRK** 的快照，即整个流被真正执行完。",
        "   在流中间异常终止的候选虽然也是合法快照，但会丢弃并换下一个候选。",
        "5. **校验**：审计最终 `.sfs` 的代码段（必须逐字节等于被选候选），再用同一解码器重算",
        "   类覆盖；`sf_player` 4 核 × 3 次回放；`sf_checker` 128 核 sweep + 50/1000 采样；",
        "   `fleet.py` 4 核窗口轮转。",
        "",
        "## 配对结果",
        "",
        "| 模板 | 单元 | 模板指令数 | 流指令数 | 长度比 | 编码类覆盖 | JS 散度 | 执行到末尾 | 快照 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for p in pairs:
        lines.append("| {id} | {mod} | {ti} | {si} | {lr} | {cov} | {js} | {dep}/{code}B | `{snap}` |".format(
            id=p["template"]["id"], mod=p["template"]["module"],
            ti=p["template"]["insns"], si=p["stream"]["insns"],
            lr=p["stream"]["length_ratio"], cov=p["stream"]["coverage"],
            js=p["stream"]["js_divergence"], dep=p["stream"]["pc_offset"],
            code=p["stream"]["code_bytes"], snap=p["stream"]["snapshot_sha256"][:12]))
    ck = ver["checks"]
    lines += [
        "",
        "## 机群校验",
        "",
        "| 模式 | 核 | 执行次数 | 不匹配 | 错误 |",
        "| --- | --- | --- | --- | --- |",
        "| sweep | %s | %s | %s | %s |" % (
            ck["sweep"]["cores"], ck["sweep"]["executions"],
            ck["sweep"]["mismatches"], ck["sweep"]["errors"]),
        "| sampled 50/1000 | %s | %s | %s | %s |" % (
            ck["sampled"]["cores"], ck["sampled"]["executions"],
            ck["sampled"]["mismatches"], ck["sampled"]["errors"]),
        "",
        "4 核窗口（%d 个窗口 × %ds）日志见 `verify/fleet/`。" % (
            args.fleet_windows, args.fleet_seconds),
        "",
        "## 逐模板候选统计",
        "",
        "| 模板 | 修复候选 | 跑到末尾 | 中途终止 | 被选候选 JS |",
        "| --- | --- | --- | --- | --- |",
    ]
    for p in pairs:
        e = p["execution"]
        lines.append("| %s | %d | %d | %d | %s |" % (
            p["template"]["id"], e["candidates_fixed"], e["candidates_reaching_trailer"],
            e["candidates_ending_early"], p["stream"]["js_divergence"]))
    lines += [
        "",
        "## 边界与已知差异",
        "",
        "- 对应关系建立在**编码类**层面：同类内寄存器/立即数取值不同，这是 ifuzz 的固定",
        "  操作数模板决定的，也是 SiliFuzz“覆盖无关生成”与 sdcfuzz“定向模板”的本质差异。",
        "  因此本文报告类覆盖率与类分布散度，不声称操作数级等价。",
        "- 生成器用三个**可选**表扩展：`-lse`（syzkaller 表无 CAS/SWP/LDADD）、",
        "  `-branch-ext`（上游分支编码位移为 0，是自跳转死循环）、`-vec-ext`（DUP/UMOV 的",
        "  imm5=0 是未分配编码）。三者默认关闭，未过滤生成器输出与上游字节一致。",
        "- 分支类流可能跳过尾部若干指令（前向跳转直接落到 BRK），执行到末尾由端态 PC 判定。",
        "- 流为单线程快照回放；跨核一致性压力由机轮窗口的多核并行提供。",
        "- 上游 ifuzz 表存在未分配编码与错位字段表；本次逐模板剔除，数量见 manifest 的",
        "  `variant_stats`。这不是本项目的产物缺陷，而是上游表的已知状态。",
        "",
    ]
    (work / "final" / "pairs.md").write_text("\n".join(lines))

    if args.copy_to:
        dest = Path(args.copy_to)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / "final" / "manifest.json", dest / "manifest.json")
        shutil.copy2(work / "final" / "pairs.md", dest / "pairs.md")
        shutil.copytree(work / "snapshots_all", dest / "snapshots", dirs_exist_ok=True)
        log("copied deliverable to %s" % dest)
    log("report: %d pairs" % len(pairs))


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--work", required=True)
        p.add_argument("--seeds", default=str(DEFAULT_SEEDS))

    p = sub.add_parser("analyze"); common(p)
    p.add_argument("--variants", type=int, default=8)
    p.add_argument("--seed", type=int, default=1)

    p = sub.add_parser("generate"); common(p)
    p.add_argument("--n", type=int, default=400)
    p.add_argument("--keep", type=int, default=200)
    p.add_argument("--vary-regs", type=int, default=6)
    p.add_argument("--seed", type=int, default=1)

    p = sub.add_parser("fix"); common(p)
    p.add_argument("--ref-cores", default="0,32,64,96")
    p.add_argument("--repeat", default="3")

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
    p.add_argument("--variants", type=int, default=8)
    p.add_argument("--n", type=int, default=400)
    p.add_argument("--keep", type=int, default=200)
    p.add_argument("--vary-regs", type=int, default=6)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--ref-cores", default="0,32,64,96")
    p.add_argument("--repeat", default="3")
    p.add_argument("--cores", default="0-127")
    p.add_argument("--sweep-seconds", type=int, default=30)
    p.add_argument("--fleet-seconds", type=int, default=60)
    p.add_argument("--fleet-windows", type=int, default=2)
    p.add_argument("--copy-to", default="")

    args = ap.parse_args()
    Path(args.work).mkdir(parents=True, exist_ok=True)
    if args.cmd in ("analyze", "all"):
        analyze(args)
    if args.cmd in ("generate", "all"):
        generate(args)
    if args.cmd in ("fix", "all"):
        fix(args)
    if args.cmd in ("verify", "all"):
        verify(args)
    if args.cmd in ("report", "all"):
        report(args)


if __name__ == "__main__":
    main()
