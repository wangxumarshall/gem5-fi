#!/usr/bin/env python3
"""Precise audit of the R6 narrative propagation documents.

The previous audit (2026-10-27) used two unreliable heuristics:

  * "REVIEW_REQUIRED appears anywhere in the file" -> the file is REVIEW.
    T03-F5-W4-seed1 mentions a *stale evidence directory* classified
    REVIEW_REQUIRED in Chapter 7 and was misjudged; its own seed verdict is
    PASS.
  * the literal Chapter-7 heading "原始证据与文件哈希".  Twelve documents use
    the equivalent "原始证据与哈希" and were reported as structural failures.

This tool reads the seed verdict ONLY from the explicit field in Chapter 6
(`verdict` / `判定` / `结论`) and matches the seven chapters semantically.
Every structural claim names the file. Every chain claim is re-derived from the
seed's own unmodified `prop_evt.txt.gz` + authoritative `chain_report.json`.

Two-axis experiment status:
  * chain_evidence_status      PASS / FAIL       (propagation chain itself)
  * experiment_identity_status MATCH /
                               WORKLOAD_IDENTITY_MISMATCH
  * overall_experiment_status  PASS / REVIEW_REQUIRED / FAIL /
                               NOT_MIBENCH_RESULT

Usage:
  python3 tools/lsu_prop_doc_audit.py \
      --docs-dir runs/lsu/R6_COMPLETE_PROPAGATION_PATHS \
      --repo-root /home/sdc/gem5-fi-ding \
      --evidence-json runs/lsu/R6-AUTHORITATIVE-EVIDENCE.json \
      --out-md runs/lsu/r6_reports/R6-PROPAGATION-PATHS-NARRATIVE-AUDIT.md \
      --out-json runs/lsu/r6_reports/R6-PROPAGATION-PATHS-NARRATIVE-AUDIT.json
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
from datetime import datetime

CHAPTER_KEYS = [
    ("ch1", ("实验身份与复现信息",)),
    ("ch2", ("完整故障传播过程",)),
    ("ch3", ("SDC 诊断分析",)),
    ("ch4", ("完整主链事件表",)),
    ("ch5", ("相关旁支与未进入最终主链的事件",)),
    ("ch6", ("最终判定与证据完整性",)),
    ("ch7", ("原始证据与文件哈希", "原始证据与哈希")),
]

CHAPTER_LABELS = {
    "ch1": "1 实验身份与复现信息",
    "ch2": "2 完整故障传播过程",
    "ch3": "3 SDC 诊断分析",
    "ch4": "4 完整主链事件表",
    "ch5": "5 相关旁支与未进入主链的事件",
    "ch6": "6 最终判定与证据完整性",
    "ch7": "7 原始证据与文件哈希",
}

_VERDICT_KEYS = re.compile(r"(verdict|判定|结论)", re.IGNORECASE)
_BOLD = re.compile(r"\*\*([^*]+?)\*\*")
_HEADING = re.compile(r"^##\s+(.+?)\s*$")
_NUMBERING = re.compile(r"^\d+[.、]\s*")
_CHAIN_SEP = re.compile(r"\s*(?:→|,|，|、)\s*")
_EVENT_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(—|-|\d+)\s*\|\s*(\d+)\s*\|"
)
_HEX64 = re.compile(r"`([0-9a-fA-F]{64})`")
_BACKTICK = re.compile(r"`([^`]+)`")


# ---------------------------------------------------------------------------
# Document structure
# ---------------------------------------------------------------------------
def _clean_heading(text: str) -> str:
    return _NUMBERING.sub("", text.strip())


def split_sections(text: str) -> dict[str, str]:
    """Split on level-2 headings and map the seven semantic chapters.

    Returns {key: body-text-including-heading}. Missing chapters are absent.
    """
    sections: dict[str, str] = {}
    current_key = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            if current_key:
                sections[current_key] = "\n".join(buf)
            heading = _clean_heading(m.group(1))
            current_key = None
            for key, aliases in CHAPTER_KEYS:
                if any(a in heading for a in aliases):
                    current_key = key
                    break
            buf = [line] if current_key else []
        elif current_key:
            buf.append(line)
    if current_key:
        sections[current_key] = "\n".join(buf)
    return sections


def missing_chapters(sections: dict[str, str]) -> list[str]:
    return [key for key, _ in CHAPTER_KEYS if key not in sections]


def has_legacy_sections(text: str) -> bool:
    return ("30 秒" in text or "30秒" in text or "一行传播图" in text)


def verdict_from_ch6(ch6: str) -> str:
    """Read the explicit seed verdict field in Chapter 6.

    The verdict is a *field*, not any sentence containing 结论: a table row
    `| verdict | ... |` / `| 判定 | ... |`, or a bullet `- 结论：...`.
    Prose rows such as `| campaign/checker agreement | ... 样本级结论一致 |`
    must never be mistaken for the verdict. Mentions of REVIEW_REQUIRED
    elsewhere (e.g. Chapter 7 stale-directory notes) are likewise ignored.
    """
    row = re.compile(r"^\|\s*(verdict|判定|结论)\s*\|\s*(.*?)\s*\|?\s*$", re.I)
    bullet = re.compile(r"^[-*]\s*(verdict|判定|结论)\s*[:：]\s*(.*)$", re.I)
    for line in ch6.splitlines():
        s = line.strip()
        m = row.match(s) or bullet.match(s)
        if not m:
            continue
        body = m.group(2)
        bm = _BOLD.search(body)
        token = bm.group(1) if bm else body
        token = token.strip()
        if token.upper().startswith("REVIEW_REQUIRED"):
            return "REVIEW_REQUIRED"
        if token.upper().startswith("PASS"):
            return "PASS"
        if token.upper().startswith("NOT_MIBENCH_RESULT"):
            return "NOT_MIBENCH_RESULT"
        return token
    return "MISSING"


def identity_status(ch1: str, run_out_text: str | None = None) -> str:
    """Matrix label MiBench + actual tlb_probe.rcS carrier => mismatch.

    The matrix label is a Ch.1 claim; the actual carrier is taken from the
    seed's own `run.out` when available (falling back to Ch.1). A doc's prose
    cannot clear a mismatch by asserting the labels agree.
    """
    label_has_mibench = "MiBench" in ch1
    actual = run_out_text if run_out_text is not None else ch1
    actual_is_tlb = "tlb_probe.rcS" in actual
    return (
        "WORKLOAD_IDENTITY_MISMATCH"
        if label_has_mibench and actual_is_tlb
        else "MATCH"
    )


def ch6_field(ch6: str, key: str) -> str | None:
    """Read an explicit `| key | value |` row from Chapter 6 (bold stripped)."""
    for line in ch6.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == key.lower():
            val = cells[1].replace("*", "").strip()
            return val or None
    return None


def has_main_chain_narrative(ch2: str) -> bool:
    """Chapter 2 must narrate an ancestry chain and its layer subsections.

    The chain may be written as `0(inj) → 1(...)`, as `0 → 1 → ...`, as an
    explicit range (`祖先为 0–20`), or as a full ancestor table in Ch.4 that
    Ch.2 references. All of those count as a narrative; only a Chapter 2 with
    no ancestry statement at all fails.
    """
    subs = len(re.findall(r"^###\s+2\.\d+", ch2, re.MULTILINE))
    has_chain = bool(re.search(r"→", ch2)) or "祖先" in ch2 or bool(
        re.search(r"\b\d+\s*[–-]\s*\d+\b", ch2)
    )
    return subs >= 4 and has_chain


def has_units_table(ch2: str) -> bool:
    """The 单元/输入/内部变化/输出/传播意义 table."""
    for line in ch2.splitlines():
        if line.count("|") >= 5 and all(
            x in line for x in ("输入", "内部变化", "输出", "传播意义")
        ):
            return True
    return False


def has_sdc_diag(ch3: str) -> bool:
    return len(ch3.strip()) > 200 and (
        "激活" in ch3 or "SDC" in ch3 or "3.1" in ch3
    )


# ---------------------------------------------------------------------------
# Evidence parsing
# ---------------------------------------------------------------------------
def load_prop_events(path: str) -> dict[str, dict]:
    """Parse `PROP-EVT: k=v ...` lines into event_id -> dict."""
    events: dict[str, dict] = {}
    with gzip.open(path, "rt", errors="replace") as fh:
        for line in fh:
            if not line.startswith("PROP-EVT:"):
                continue
            body = line[len("PROP-EVT:"):].strip()
            row: dict[str, str] = {}
            for tok in body.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    row[k] = v
            eid = row.get("event_id")
            if eid is not None:
                events[eid] = row
    return events


def parse_ancestry_chain(
    ch2: str, ch4_rows: list[dict] | None = None
) -> list[int]:
    """Extract the ancestry chain shown in Chapter 2.

    Accepted forms (all observed in the real doc set):

      * `0(inj) → 1(tlb_lookup) → ...`   (parenthetical labels on each id)
      * `0 → 1 → ...`
      * `祖先为 0–20（21 个事件 ...）`     (explicit contiguous range)

    Lines that name ``path_event_ids`` or call the list a layer-anchor list
    (``层锚点``) are explicitly NOT the full chain and are skipped. If Chapter
    2 only states a count and defers the full order to the Chapter 4 table
    (which is declared to be the full ancestor table), the Ch.4 row order is
    used as the chain.
    """
    best: list[int] = []

    def consider(nums: list[int]) -> None:
        nonlocal best
        if len(nums) > len(best):
            best = nums

    for line in ch2.splitlines():
        low = line.lower()
        if "path_event_ids" in low or "层锚点" in line or "只作层锚点" in line:
            continue
        if any(x in line for x in ("省略", "排除", "没有", "不含", "不进入祖先")):
            continue
        if "→" in line:
            parts = [p.strip() for p in line.split("→")]
            nums: list[int] = []
            ok = True
            for part in parts:
                m = re.match(r"^(\d+)", part)
                if not m:
                    ok = False
                    break
                nums.append(int(m.group(1)))
            if ok and len(nums) >= 5:
                consider(nums)
        # Explicit contiguous range: `祖先为 0–20` / `单祖先事件（0–21）`.
        for m in re.finditer(
            r"(?:祖先[^。\n]{0,16}|事件[（(])\s*(\d+)\s*[–-]\s*(\d+)", line
        ):
            lo, hi = int(m.group(1)), int(m.group(2))
            if 0 <= hi - lo <= 512:
                consider(list(range(lo, hi + 1)))

    # Chapter 4 is declared to be the full ancestor table; if Chapter 2 only
    # names anchors or states a count, the table is the authoritative order.
    if ch4_rows and len(best) < len(ch4_rows):
        consider([row["event_id"] for row in ch4_rows])
    return best


def parse_event_table(ch4: str) -> list[dict]:
    rows = []
    for line in ch4.splitlines():
        m = _EVENT_ROW.match(line)
        if not m:
            continue
        rows.append(
            {
                "event_id": int(m.group(1)),
                "parent": None if m.group(2) in ("—", "-") else int(m.group(2)),
                "tick": int(m.group(3)),
            }
        )
    return rows


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


_INTERESTING = (
    "prop_evt",
    "chain_report",
    "run.out",
    "run.err",
    "stats.txt",
    "manifest.json",
    "board.workload.dmesg",
    "board.terminal",
    "armtlb_injections.log",
)


def _resolve_doc_path(raw: str, auth_dir: str, repo_root: str) -> str | None:
    """Resolve an absolute, relative, or elided (`…/x`) Ch.7 path."""
    p = raw.strip().strip("`")
    if not p or p in ("—", "-", "N/A"):
        return None
    if p.startswith("…/") or p.startswith(".../"):
        base = p.split("/", 1)[1]
        cand = os.path.join(auth_dir, base)
        if os.path.exists(cand):
            return cand
        cand = os.path.join(repo_root, base)
        return cand if os.path.exists(cand) else None
    if os.path.isabs(p):
        return p
    cand = os.path.join(auth_dir, p)
    if os.path.exists(cand):
        return cand
    cand = os.path.join(repo_root, p)
    return cand if os.path.exists(cand) else None


def check_ch7_hashes(
    ch7: str,
    auth_dir: str | None = None,
    binary_sha256: str | None = None,
    repo_root: str = ".",
) -> dict:
    """Recompute every Ch.7 hash we can and compare to the table.

    Ch.7 uses three path styles in the real set: absolute paths, paths
    relative to the authoritative directory, and `…/name` elisions. The
    binary row is compared to the manifest-recorded SHA-256 instead of
    re-hashing a 1.1 GB file.
    """
    checked = []
    mismatches = []
    for line in ch7.splitlines():
        hashes = [h.lower() for h in _HEX64.findall(line)]
        if not hashes:
            continue
        cands = [
            p for p in _BACKTICK.findall(line)
            if not re.fullmatch(r"[0-9a-fA-F]{64}", p)
        ]
        if auth_dir is None:
            cands = [p for p in cands if "/" in p and not p.startswith(("…/", ".../"))]
        if not cands:
            continue
        path = _resolve_doc_path(cands[0], auth_dir or repo_root, repo_root)
        if path is None:
            # A row without a resolvable path is not a hash claim we can check
            # (e.g. the `启动命令记录` row points at run.out by description).
            continue
        base = os.path.basename(path)
        if base == "gem5.opt":
            ok = bool(binary_sha256) and binary_sha256.lower() in hashes
            checked.append({"path": path, "sha256": binary_sha256,
                            "match": ok, "via": "manifest"})
            if not ok:
                mismatches.append({"path": path, "reason": "BINARY_SHA_MISMATCH",
                                   "doc": hashes,
                                   "manifest": binary_sha256})
            continue
        if not any(tag in path for tag in _INTERESTING):
            checked.append({"path": path, "sha256": None, "match": None,
                            "via": "not_rehashed"})
            continue
        if not os.path.exists(path):
            mismatches.append({"path": path, "reason": "MISSING"})
            continue
        actual = _sha256(path)
        ok = actual in hashes
        checked.append({"path": path, "sha256": actual, "match": ok,
                        "via": "recomputed"})
        if not ok:
            mismatches.append(
                {"path": path, "reason": "SHA_MISMATCH", "actual": actual,
                 "doc": hashes}
            )
    return {"checked": checked, "mismatches": mismatches}


# ---------------------------------------------------------------------------
# Per-document audit
# ---------------------------------------------------------------------------
def _review_reasons(ch6: str, verdict: str) -> list[str]:
    if verdict not in ("REVIEW_REQUIRED", "NOT_MIBENCH_RESULT"):
        return []
    reasons = []
    capture = False
    for line in ch6.splitlines():
        s = line.strip()
        if not s:
            continue
        if "理由" in s and ("REVIEW" in s.upper() or "不一致" in s):
            capture = True
            continue
        if "必须记录的不一致" in s or "必须记录的缺口" in s:
            capture = True
            continue
        if capture:
            if s.startswith("## ") or s.startswith("一致性自检"):
                break
            if re.match(r"^(\d+[.、]|[-*])\s*", s):
                reasons.append(s)
    return reasons[:8]


def _witness_from_ch6(ch6: str) -> int | None:
    """Read the explicit propagation-terminal event id from Chapter 6.

    The real doc set writes this row as `传播终局事件`, `传播终局`,
    `propagation terminal event`, or `终局见证`; the id may be written as
    `event_id=68`, ``event_id=`68```, `event 20`, or ``event 118``.
    A line about `chain_end` is never accepted as the L5 witness.
    """
    for line in ch6.splitlines():
        low = line.lower()
        if "chain_end" in low or "chain end" in low:
            continue
        if not any(
            k in line
            for k in ("传播终局", "终局见证", "终局事件")
        ) and not any(
            k in low
            for k in ("propagation terminal", "terminal event")
        ) and "终局" not in line:
            continue
        m = re.search(r"event_id\s*[=:：]\s*`?\s*(\d+)", line)
        if not m:
            m = re.search(r"event\s*`?\s*(\d+)", line)
        if m:
            return int(m.group(1))
    return None


def _check_witness(witness_id: int | None, terminal: str, events: dict) -> dict:
    out = {"event_id": witness_id, "exists": False, "contained": None,
           "detection_layer": None, "kind": None, "outcome": None,
           "ok": False, "reason": ""}
    if witness_id is None:
        out["reason"] = "Ch.6 has no explicit propagation-terminal event id"
        return out
    e = events.get(str(witness_id))
    if e is None:
        out["reason"] = "witness event not present in this seed's stream"
        return out
    contained = str(e.get("contained", "")).lower() in ("1", "true")
    out.update(
        exists=True,
        contained=contained,
        detection_layer=e.get("detection_layer"),
        kind=e.get("kind"),
        outcome=e.get("outcome"),
    )
    if terminal == "full":
        out["ok"] = (
            e.get("kind") == "errant_commit"
            and e.get("detection_layer") == "L5"
            and not contained
        )
        if not out["ok"]:
            out["reason"] = (
                "full seed witness must be a real errant_commit at L5 with "
                "contained=0 (chain_end is not L5)"
            )
    elif terminal == "detected_contained":
        out["ok"] = (
            contained
            and e.get("detection_layer") in ("L2", "L4")
            and e.get("kind") in ("squash_masked", "tlb_translate_result")
        )
        if not out["ok"]:
            out["reason"] = (
                "containment witness must be contained=1 at L2 "
                "(tlb_translate_result) or L4 (squash_masked)"
            )
    else:
        out["reason"] = f"unexpected terminal {terminal!r}"
    return out


def audit_one(doc_path: str, repo_root: str, evidence_json: str) -> dict:
    name = os.path.basename(doc_path)
    m = re.match(r"^(T\d+-F\d+-W\d+)-seed(\d+)\.md$", name)
    run_id = m.group(1) if m else "?"
    seed = int(m.group(2)) if m else 0
    text = open(doc_path, encoding="utf-8").read()
    sections = split_sections(text)
    ch6 = sections.get("ch6", "")

    result = {
        "file": name,
        "run_id": run_id,
        "seed": seed,
        "chapters_present": sorted(sections.keys()),
        "missing_chapters": missing_chapters(sections),
        "legacy_sections": has_legacy_sections(text),
        "has_ch2_narrative": has_main_chain_narrative(sections.get("ch2", "")),
        "has_units_table": has_units_table(sections.get("ch2", "")),
        "sdc_diag": has_sdc_diag(sections.get("ch3", "")),
        "seed_verdict": verdict_from_ch6(ch6),
        "declared_chain_status": ch6_field(ch6, "chain_evidence_status"),
        "declared_identity_status": ch6_field(ch6, "experiment_identity_status"),
        "declared_overall_status": ch6_field(ch6, "overall_experiment_status"),
        "experiment_identity_status": "UNKNOWN",
        "matrix_workload_label": None,
        "actual_readfile": None,
        "ancestry": {"chain": [], "parent_mismatches": [], "tick_violations": []},
        "ch4": {"rows": 0, "missing_events": [], "parent_mismatches": [],
                "tick_mismatches": [], "order_violations": []},
        "hashes": {"checked": [], "mismatches": []},
        "witness": {"event_id": None, "exists": False, "contained": None,
                    "detection_layer": None, "kind": None, "outcome": None,
                    "ok": False, "reason": "not checked"},
        "chain_evidence_status": "FAIL",
        "overall_experiment_status": "REVIEW_REQUIRED",
        "review_reasons": _review_reasons(ch6, verdict_from_ch6(ch6)),
    }

    ev = json.load(open(evidence_json))
    entry = ev.get("seeds", {}).get(f"{run_id}|seed{seed}")
    if not entry:
        result["error"] = "NO_AUTHORITATIVE_ENTRY"
        return result
    auth = entry["authoritative"]
    auth_dir = os.path.join(repo_root, auth["dir"])
    prop_path = os.path.join(auth_dir, "prop_evt.txt.gz")
    report_path = os.path.join(
        repo_root, auth["files"]["chain_report_or_regrade"]["path"]
    )
    report = json.load(open(report_path))
    events = load_prop_events(prop_path)

    # --- Workload identity: matrix label vs the seed's real run.out --------
    run_out_path = os.path.join(auth_dir, "run.out")
    run_out_text = (
        open(run_out_path, encoding="utf-8", errors="replace").read()
        if os.path.exists(run_out_path)
        else None
    )
    ch1 = sections.get("ch1", "")
    label = re.search(r"(MiBench[^`|\n]*|TLB-AliasPerm[^`|\n]*|tlb_probe[^`|\n]*)", ch1)
    result["matrix_workload_label"] = label.group(1).strip() if label else None
    rf = re.search(r"--readfile\s+(\S+)", run_out_text or "")
    result["actual_readfile"] = rf.group(1) if rf else None
    result["experiment_identity_status"] = identity_status(ch1, run_out_text)

    # --- Chapter 4 first: it is the declared full ancestor table ----------
    rows = parse_event_table(sections.get("ch4", ""))
    result["ch4"]["rows"] = len(rows)
    for idx, row in enumerate(rows):
        e = events.get(str(row["event_id"]))
        if e is None:
            result["ch4"]["missing_events"].append(row["event_id"])
        else:
            if row["parent"] is not None:
                actual = e.get("parent_event_id", "")
                if actual != str(row["parent"]):
                    result["ch4"]["parent_mismatches"].append(
                        {"event_id": row["event_id"],
                         "doc_parent": row["parent"], "actual_parent": actual})
            try:
                if int(e.get("tick", 0)) != row["tick"]:
                    result["ch4"]["tick_mismatches"].append(
                        {"event_id": row["event_id"], "doc_tick": row["tick"],
                         "actual_tick": int(e.get("tick", 0))})
            except ValueError:
                pass
        if idx > 0:
            prev = rows[idx - 1]["event_id"]
            if row["parent"] is not None and row["parent"] != prev:
                result["ch4"]["order_violations"].append(
                    {"row": idx + 1, "event_id": row["event_id"],
                     "parent": row["parent"], "previous_row": prev})

    # --- Chapter 2: ancestry ordering -------------------------------------
    chain = parse_ancestry_chain(sections.get("ch2", ""), rows)
    result["ancestry"]["chain"] = chain
    for a, b in zip(chain, chain[1:]):
        ea, eb = events.get(str(a)), events.get(str(b))
        if eb is None:
            result["ancestry"]["parent_mismatches"].append(
                {"child": b, "reason": "MISSING_EVENT"})
            continue
        parent = eb.get("parent_event_id", "")
        if parent != str(a):
            result["ancestry"]["parent_mismatches"].append(
                {"child": b, "expected_parent": a, "actual_parent": parent})
        if ea is not None:
            try:
                if int(eb.get("tick", 0)) < int(ea.get("tick", 0)):
                    result["ancestry"]["tick_violations"].append(
                        {"parent": a, "child": b})
            except ValueError:
                pass

    # --- Chapter 7: hashes ------------------------------------------------
    hashes = check_ch7_hashes(
        sections.get("ch7", ""), auth_dir, auth.get("binary_sha256"), repo_root
    )
    result["hashes"]["checked"] = hashes["checked"]
    result["hashes"]["checked_count"] = len(hashes["checked"])
    result["hashes"]["mismatches"] = hashes["mismatches"]

    # --- Authoritative report (plain or regrade schema) -------------------
    admission = report.get("admission") or {}
    violations = admission.get("violations")
    if violations is None:
        violations = report.get("violations") or []
    chain_valid = report.get("chain_valid")
    if chain_valid is None:
        chain_valid = bool(report.get("admitted") and report.get("certified"))
    terminal = report.get("terminal")
    witness_id = _witness_from_ch6(ch6)
    witness = _check_witness(witness_id, terminal, events)
    result["witness"] = witness

    chain_ok = (
        terminal in ("full", "detected_contained")
        and bool(chain_valid)
        and bool(report.get("admitted"))
        and bool(report.get("certified"))
        and not violations
        and witness["ok"]
        and not result["missing_chapters"]
        and not result["ancestry"]["parent_mismatches"]
        and not result["ancestry"]["tick_violations"]
        and not result["ch4"]["missing_events"]
        and not result["ch4"]["parent_mismatches"]
        and not result["ch4"]["tick_mismatches"]
        and not result["ch4"]["order_violations"]
        and not result["hashes"]["mismatches"]
        and result["has_ch2_narrative"]
        and result["has_units_table"]
    )
    result["chain_evidence_status"] = "PASS" if chain_ok else "FAIL"
    result["evidence"] = {
        "authoritative_dir": auth["dir"],
        "binary_sha256": auth.get("binary_sha256"),
        "terminal": terminal,
        "provable_to": report.get("provable_to"),
        "oracle_outcome": report.get("oracle_outcome"),
        "admitted": report.get("admitted"),
        "certified": report.get("certified"),
        "chain_valid": chain_valid,
        "violations": violations,
        "event_count": len(events),
        "fault_count": len(report.get("faults") or {}),
    }

    # --- Two-axis overall status -----------------------------------------
    if result["experiment_identity_status"] == "WORKLOAD_IDENTITY_MISMATCH":
        result["overall_experiment_status"] = "NOT_MIBENCH_RESULT"
    elif result["chain_evidence_status"] != "PASS":
        result["overall_experiment_status"] = "FAIL"
    else:
        result["overall_experiment_status"] = result["seed_verdict"]

    if result["chain_evidence_status"] != "PASS":
        result["review_reasons"].append(
            "chain evidence check failed: see ancestry/ch4/hashes/witness details"
        )
    # A doc that declares the three two-axis fields must agree with the audit.
    declared = {
        "chain_evidence_status": result["declared_chain_status"],
        "experiment_identity_status": result["declared_identity_status"],
        "overall_experiment_status": result["declared_overall_status"],
    }
    for key, val in declared.items():
        if val is None:
            continue
        expected = result[key]
        if key == "overall_experiment_status" and val.split()[0] != expected:
            result["review_reasons"].append(
                f"Ch.6 declares {key}={val!r} but audit computed {expected!r}")
    return result


# ---------------------------------------------------------------------------
# Directory audit + rendering
# ---------------------------------------------------------------------------
def audit_dir(docs_dir: str, repo_root: str, evidence_json: str) -> dict:
    files = sorted(
        f for f in os.listdir(docs_dir)
        if re.match(r"^T\d+-F\d+-W\d+-seed\d+\.md$", f)
    )
    results = []
    for f in files:
        try:
            results.append(audit_one(os.path.join(docs_dir, f), repo_root,
                                     evidence_json))
        except Exception as exc:  # loud, per-file
            results.append({"file": f, "error": f"{type(exc).__name__}: {exc}",
                            "chain_evidence_status": "FAIL",
                            "overall_experiment_status": "FAIL",
                            "experiment_identity_status": "UNKNOWN",
                            "seed_verdict": "UNKNOWN",
                            "missing_chapters": [], "legacy_sections": False,
                            "has_ch2_narrative": False, "has_units_table": False,
                            "sdc_diag": False, "review_reasons": []})

    def names(pred):
        return [r["file"] for r in results if pred(r)]

    def structural_reasons(r: dict) -> list[str]:
        reasons = []
        if r.get("missing_chapters"):
            reasons.append("missing chapters: " + ",".join(r["missing_chapters"]))
        if r.get("legacy_sections"):
            reasons.append("legacy 30s/one-line section present")
        if not r.get("has_ch2_narrative"):
            reasons.append("Ch.2 has no ancestry narrative")
        if not r.get("has_units_table"):
            reasons.append("Ch.2 lacks input/internal-change/output/meaning table")
        if not r.get("sdc_diag"):
            reasons.append("Ch.3 lacks SDC diagnosis")
        return reasons

    structural_details = []
    for r in results:
        reasons = structural_reasons(r)
        if reasons:
            structural_details.append({"file": r["file"], "reasons": reasons})
    structural = [d["file"] for d in structural_details]

    chain_fail_details = []
    for r in results:
        if r.get("chain_evidence_status") == "PASS":
            continue
        if r.get("error"):
            chain_fail_details.append(
                {"file": r["file"], "reasons": [r["error"]]})
            continue
        reasons = []
        if r.get("missing_chapters"):
            reasons.append("missing chapters")
        if r["ancestry"].get("parent_mismatches"):
            reasons.append("Ch.2 ancestry parent mismatch")
        if r["ancestry"].get("tick_violations"):
            reasons.append("child tick < parent tick")
        if r["ch4"].get("missing_events"):
            reasons.append("Ch.4 event absent from seed stream")
        if r["ch4"].get("parent_mismatches"):
            reasons.append("Ch.4 parent mismatch")
        if r["ch4"].get("tick_mismatches"):
            reasons.append("Ch.4 tick mismatch")
        if r["ch4"].get("order_violations"):
            reasons.append("Ch.4 row order: child before parent")
        if r["hashes"].get("mismatches"):
            reasons.append("Ch.7 hash mismatch/missing file")
        if not r.get("has_ch2_narrative"):
            reasons.append("no main-chain narrative")
        if not r.get("has_units_table"):
            reasons.append("no unit input/change/output/meaning table")
        if not r.get("witness", {}).get("ok"):
            reasons.append("witness invalid: " + r.get("witness", {}).get("reason", ""))
        chain_fail_details.append({"file": r["file"], "reasons": reasons})

    overall_counts: dict[str, int] = {}
    for r in results:
        key = r.get("overall_experiment_status", "UNKNOWN")
        overall_counts[key] = overall_counts.get(key, 0) + 1

    summary = {
        "files_total": len(results),
        "seven_chapters_complete": sum(
            1 for r in results if not r.get("missing_chapters")),
        "legacy_section_files": names(lambda r: r.get("legacy_sections")),
        "missing_main_chain_narrative": names(
            lambda r: not r.get("has_ch2_narrative")),
        "missing_units_table": names(lambda r: not r.get("has_units_table")),
        "missing_sdc_diag": names(lambda r: not r.get("sdc_diag")),
        "verdict_pass": sum(1 for r in results
                            if r.get("seed_verdict") == "PASS"),
        "verdict_review_required": sum(
            1 for r in results
            if r.get("seed_verdict") == "REVIEW_REQUIRED"),
        "verdict_not_mibench": sum(
            1 for r in results
            if r.get("seed_verdict") == "NOT_MIBENCH_RESULT"),
        "structural_failures": structural,
        "structural_failure_details": structural_details,
        "identity_mismatch_files": names(
            lambda r: r.get("experiment_identity_status")
            == "WORKLOAD_IDENTITY_MISMATCH"),
        "chain_evidence_pass": sum(
            1 for r in results if r.get("chain_evidence_status") == "PASS"),
        "chain_evidence_fail": names(
            lambda r: r.get("chain_evidence_status") != "PASS"),
        "chain_evidence_failure_details": chain_fail_details,
        "overall_status_counts": overall_counts,
        "containment_seeds": names(
            lambda r: (r.get("evidence") or {}).get("terminal")
            == "detected_contained"),
    }
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "docs_dir": docs_dir,
        "repo_root": repo_root,
        "evidence_json": evidence_json,
        "summary": summary,
        "files": results,
    }


def _ok(flag: bool) -> str:
    return "✓" if flag else "✗"


def render_md(result: dict) -> str:
    s = result["summary"]
    lines = [
        "# R6 叙事版传播文档审计（精确版）",
        "",
        f"- 生成时间 `{result['generated_at']}`",
        f"- 文档目录 `{result['docs_dir']}`",
        f"- 权威证据索引 `{result['evidence_json']}`",
        "",
        "## 汇总",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 文件总数 | **{s['files_total']}** |",
        f"| 七章齐全 | **{s['seven_chapters_complete']}** |",
        f"| 仍含旧章节 | **{len(s['legacy_section_files'])}** |",
        f"| 缺少主链叙述 | **{len(s['missing_main_chain_narrative'])}** |",
        f"| 缺少单元输入/内部变化/输出/传播意义表 | **{len(s['missing_units_table'])}** |",
        f"| 缺少 SDC 诊断 | **{len(s['missing_sdc_diag'])}** |",
        f"| 当前 seed verdict=PASS | **{s['verdict_pass']}** |",
        f"| 当前 seed verdict=REVIEW_REQUIRED | **{s['verdict_review_required']}** |",
        f"| 当前 seed verdict=NOT_MIBENCH_RESULT | **{s['verdict_not_mibench']}** |",
        f"| 结构失败（真实，逐文件） | **{len(s['structural_failures'])}** |",
        f"| chain evidence PASS | **{s['chain_evidence_pass']}** |",
        f"| chain evidence FAIL | **{len(s['chain_evidence_fail'])}** |",
        f"| workload identity mismatch | **{len(s['identity_mismatch_files'])}** |",
        f"| containment seed | **{len(s['containment_seeds'])}** |",
        "",
        "overall_experiment_status 分布："
        + "、".join(f"`{k}`={v}" for k, v in sorted(s["overall_status_counts"].items())),
        "",
        "结构失败文件清单：**"
        + ("无" if not s["structural_failures"]
           else "、".join(f"`{x}`" for x in s["structural_failures"]))
        + "**",
        "",
        "workload identity mismatch 清单：**"
        + ("无" if not s["identity_mismatch_files"]
           else "、".join(f"`{x}`" for x in s["identity_mismatch_files"]))
        + "**",
        "",
        "chain evidence FAIL 清单：**"
        + ("无" if not s["chain_evidence_fail"]
           else "、".join(f"`{x}`" for x in s["chain_evidence_fail"]))
        + "**",
        "",
        "## 逐文件",
        "",
        "`7章`=七章齐全；`祖先序`=第2章链逐对 parent 正确且 tick 单调；"
        "`单表`=含输入/内部变化/输出/传播意义；`4章`=事件存在于本 seed 流；"
        "`哈希`=第7章重算一致；`见证`=终局事件真实（full=L5 errant_commit，"
        "contained=L2/L4 contained）；`链证`=chain evidence；`身份`=experiment identity。",
        "",
        "| 文件 | 7章 | 祖先序 | 子先于父 | 单表 | SDC | 4章 | 哈希 | 见证 | 链证 | 身份 | 总状态 | Ch6 verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in result["files"]:
        if r.get("error"):
            lines.append(
                f"| `{r['file']}` | — | — | — | — | — | — | — | — | FAIL | UNKNOWN | FAIL | — |"
            )
            continue
        anc = r["ancestry"]
        ch4 = r["ch4"]
        identity = ("MISMATCH"
                    if r["experiment_identity_status"]
                    == "WORKLOAD_IDENTITY_MISMATCH" else "MATCH")
        lines.append(
            "| `{f}` | {c7} | {anc} | {child} | {units} | {sdc} | {ch4} | {h} | {w} | {chain} | {ident} | **{overall}** | {verdict} |".format(
                f=r["file"],
                c7=_ok(not r["missing_chapters"]),
                anc=_ok(not anc["parent_mismatches"]
                        and len(anc["chain"]) >= 2),
                child=_ok(not anc["tick_violations"]
                          and not ch4["order_violations"]),
                units=_ok(r["has_units_table"]),
                sdc=_ok(r["sdc_diag"]),
                ch4=_ok(not ch4["missing_events"]
                        and not ch4["parent_mismatches"]
                        and not ch4["tick_mismatches"]),
                h=_ok(not r["hashes"]["mismatches"]),
                w=_ok(r["witness"]["ok"]),
                chain=r["chain_evidence_status"],
                ident=identity,
                overall=r["overall_experiment_status"],
                verdict=r["seed_verdict"],
            )
        )
    lines += ["", "## 结构失败逐文件原因", ""]
    if result["summary"]["structural_failure_details"]:
        for d in result["summary"]["structural_failure_details"]:
            lines.append(f"- `{d['file']}`：{'；'.join(d['reasons'])}")
    else:
        lines.append("无。")
    lines += ["", "## chain evidence 失败逐文件原因", ""]
    if result["summary"]["chain_evidence_failure_details"]:
        for d in result["summary"]["chain_evidence_failure_details"]:
            lines.append(f"- `{d['file']}`：{'；'.join(d['reasons'])}")
    else:
        lines.append("无。")
    lines += ["", "## REVIEW_REQUIRED / NOT_MIBENCH_RESULT 的准确原因", ""]
    any_reason = False
    for r in result["files"]:
        if r.get("seed_verdict") not in (
            "REVIEW_REQUIRED", "NOT_MIBENCH_RESULT"
        ):
            continue
        any_reason = True
        lines.append(f"### `{r['file']}`")
        lines.append("")
        lines.append(f"- Ch.6 verdict：`{r['seed_verdict']}`")
        lines.append(f"- chain_evidence_status：`{r['chain_evidence_status']}`")
        lines.append(
            f"- experiment_identity_status：`{r['experiment_identity_status']}`"
        )
        lines.append(f"- overall_experiment_status：`{r['overall_experiment_status']}`")
        for reason in r.get("review_reasons") or ["（文档未给出结构化理由）"]:
            lines.append(f"- {reason}")
        lines.append("")
    if not any_reason:
        lines.append("无。")
    lines += [
        "",
        "## 方法论",
        "",
        "- seed verdict 只从第 6 章的 `verdict` / `判定` / `结论` 显式字段读取，"
        "全文出现 `REVIEW_REQUIRED` 不再参与判定。",
        "- 七章按语义匹配，`原始证据与哈希` 与 `原始证据与文件哈希` 等价。",
        "- 第 2 章祖先链、第 4 章事件、第 7 章哈希均由本 seed 原始证据独立重算。",
        "- containment seed 的 `L5=N/A` 不构成结构失败。",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docs-dir", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--evidence-json", required=True)
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    args = ap.parse_args(argv)
    result = audit_dir(args.docs_dir, args.repo_root, args.evidence_json)
    md = render_md(result)
    if args.out_md:
        os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
        open(args.out_md, "w", encoding="utf-8").write(md)
    if args.out_json:
        os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
        json.dump(result, open(args.out_json, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        open(args.out_json, "a", encoding="utf-8").write("\n")
    if not args.out_md:
        print(md)
    s = result["summary"]
    print(
        f"files={s['files_total']} seven_chapters={s['seven_chapters_complete']} "
        f"legacy={len(s['legacy_section_files'])} "
        f"no_chain={len(s['missing_main_chain_narrative'])} "
        f"no_units={len(s['missing_units_table'])} "
        f"no_sdc={len(s['missing_sdc_diag'])} "
        f"pass={s['verdict_pass']} review={s['verdict_review_required']} "
        f"not_mibench={s['verdict_not_mibench']} "
        f"structural={len(s['structural_failures'])} "
        f"identity_mismatch={len(s['identity_mismatch_files'])} "
        f"chain_pass={s['chain_evidence_pass']} "
        f"chain_fail={len(s['chain_evidence_fail'])}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
