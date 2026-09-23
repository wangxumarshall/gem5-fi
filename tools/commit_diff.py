#!/usr/bin/env python3
"""commit_diff.py -- W2.2 TC'23 L2 commit-trace five-class offline differ.

Compares two commit traces -- a fault-free reference run vs a fault-injected
run -- instruction by instruction and classifies the pair into the TC'23 L2
five classes (docs/gem5-fi/ooo/01-observation-points.md, L2):

    ①执行时间错    Execution Time Error
    ②指令流改变    Instruction Flow Change
    ③指令替换      Instruction Replacement
    ④操作数强制切换 Operand Forced Switch
    ⑤数据损坏      Data Corruption

Pinned trace line format (docs/superpowers/plans/2026-09-24-ooo-w2-observation.md
Global Constraints; producer = W2.1 CHAOSCommitTrace, this tool = consumer):

    seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*

CSV, one committed instruction per line. gem5 simout writes it gzip-compressed;
this tool auto-detects gzip by magic bytes (a plain-text file also reads fine).
Fields:
    seq    self-contained GLOBAL commit sequence number, starts at 0,
           strictly increasing within one trace -- this is the alignment key
    tid    thread id (uint; informational only, never part of the五分类)
    tick   commit tick (uint; compared only against --tick-tol)
    pc     program counter, hex WITHOUT 0x prefix (case-insensitive)
    op     staticInst->getName() (exact string match)
    ndest  number of destination-register 4-tuples that follow
    per destination register (ndest tuples):
      class  RegClass value (uint)
      arch   architectural register index (uint)
      phys   physical register index (uint; microarch detail, NOT classified)
      val    64-bit value as EXACTLY 16 hex digits (scalar zero-padded, or
             FNV-1a-64 of the vector blob), case-insensitive

Strict parsing: every line must have exactly 6 + 4*ndest columns and every
field must match its type; anything else is a loud exit 1 naming file + line
number + reason. seq must start at 0 and strictly increase (alignment
requirement of the pinned format).

Alignment & classification (plan Task 2, pinned):
  The two traces are merged on seq (union; a seq present on only one side is
  itself a divergence). At each seq, fields are checked in priority order and
  the first failing check names the class of that divergence point:

    seq one-sided, or pc differs                 -> ②指令流改变
    same pc, op differs                          -> ③指令替换
    same op, dest count or dest arch id differs  -> ④操作数强制切换
    same dest arch ids, any val differs          -> ⑤数据损坏

  "dest arch id" is compared as the (class, arch) PAIR: a register's identity
  is both its class and its index (comparing index-only would equate x5 with
  d5). In practice same pc+op implies same dest classes (they are static
  properties of the instruction), so this never widens ④ on real traces.

  ①执行时间错 is assigned only when the instruction streams are field-
  identical over the WHOLE trace ("全程字段全同") and some aligned seq's
  tick drifts by more than --tick-tol; its latency is the first such seq.
  Rationale: the five classes classify the architectural OUTCOME. If the
  committed stream ever diverges in pc/op/dest/val, the outcome is that field
  divergence class, and a pure-timing classification does not apply. Tick
  drift that occurs before a field divergence is still reported (aux
  first_tick_over_tol_seq / max_tick_drift), it just never steals the primary
  class nor the ① count.

  Every diverging seq is one divergence point. The PRIMARY class is the class
  of the first (lowest-seq) divergence point; the latency (潜伏期) is its seq
  (01-observation-points.md: 潜伏期用提交指令数口径); ALL divergence points
  are counted per class. A pair with no field divergence and every tick drift
  <= tol is 无分歧 (no divergence).

Microarch diagnostics reported but never classified: phys-index mismatches
and tid mismatches on otherwise field-identical instructions, and tick-drift
stats computed only over field-identical instruction pairs (ticks are only
comparable between identical instructions).

Usage:
  python3 tools/commit_diff.py --ref A.csv.gz --run B.csv.gz \
      [--json OUT.json] [--tick-tol T]        (default T = 0)

Exit codes:
  0  comparison completed (diverged or not -- read the report/JSON verdict)
  1  unreadable file / malformed trace line (message names file + line)
  2  command-line misuse (argparse)
"""

import argparse
import gzip
import json
import re
import sys

UINT_RE = re.compile(r"^[0-9]+$")
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
VAL_RE = re.compile(r"^[0-9a-fA-F]{16}$")

GZIP_MAGIC = b"\x1f\x8b"

# ---- five classes, numbered as in 01-observation-points.md L2 ----
# (json key, 中文标签, English label)
CLASSES = [
    ("timing_error", "①执行时间错", "Execution Time Error"),
    ("instruction_flow_change", "②指令流改变", "Instruction Flow Change"),
    ("instruction_substitution", "③指令替换", "Instruction Replacement"),
    ("operand_forced_switch", "④操作数强制切换", "Operand Forced Switch"),
    ("data_corruption", "⑤数据损坏", "Data Corruption"),
]
CLASS_KEYS = [c[0] for c in CLASSES]
ZH = {k: z for k, z, _ in CLASSES}

NO_DIVERGENCE_ZH = "无分歧"
TRACE_FORMAT = "seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*"


class TraceError(Exception):
    """Loud, user-facing trace/IO error (exit 1)."""


class Rec(object):
    """One parsed committed-instruction line."""

    __slots__ = ("seq", "tid", "tick", "pc", "op", "ndest", "dests", "raw",
                 "lineno")

    def __init__(self, seq, tid, tick, pc, op, ndest, dests, raw, lineno):
        self.seq = seq
        self.tid = tid
        self.tick = tick
        self.pc = pc
        self.op = op
        self.ndest = ndest
        self.dests = dests  # list of (class, arch, phys, val) tuples
        self.raw = raw      # original line text (no trailing newline)
        self.lineno = lineno


# ---------------------------------------------------------------- parsing

def open_text(path):
    """Open `path` as text; gzip auto-detected by magic bytes, not extension."""
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
    except OSError as e:
        raise TraceError("cannot open '%s': %s" % (path, e.strerror or e))
    if magic == GZIP_MAGIC:
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "rt", encoding="utf-8")


def _uint(tok, what, path, lineno):
    if not UINT_RE.match(tok):
        raise TraceError("%s: line %d: %s 字段 '%s' 不是无符号整数"
                         % (path, lineno, what, tok))
    return int(tok)


def _pc(tok, path, lineno):
    if tok[:2] in ("0x", "0X"):
        raise TraceError("%s: line %d: pc 字段 '%s' 带 0x 前缀"
                         "（钉死格式要求无前缀十六进制）" % (path, lineno, tok))
    if not HEX_RE.match(tok):
        raise TraceError("%s: line %d: pc 字段 '%s' 不是合法十六进制"
                         % (path, lineno, tok))
    return tok.lower()


def _val(tok, what, path, lineno):
    if not VAL_RE.match(tok):
        raise TraceError("%s: line %d: %s 字段 '%s' 不是 16 位十六进制"
                         "（钉死格式: val=16位十六进制）" % (path, lineno, what, tok))
    return tok.lower()


def parse_line(path, lineno, line):
    cols = line.split(",")
    if len(cols) < 6:
        raise TraceError("%s: line %d: 列数 %d < 6（钉死格式基列 "
                         "'seq,tid,tick,pc,op,ndest' 至少 6 列）"
                         % (path, lineno, len(cols)))
    seq = _uint(cols[0], "seq", path, lineno)
    tid = _uint(cols[1], "tid", path, lineno)
    tick = _uint(cols[2], "tick", path, lineno)
    pc = _pc(cols[3], path, lineno)
    op = cols[4]
    if not op:
        raise TraceError("%s: line %d: op 字段为空" % (path, lineno))
    ndest = _uint(cols[5], "ndest", path, lineno)
    expected = 6 + 4 * ndest
    if len(cols) != expected:
        raise TraceError("%s: line %d: 列数不匹配: ndest=%d 要求 %d 列 "
                         "(6+4*ndest)，实际 %d 列"
                         % (path, lineno, ndest, expected, len(cols)))
    dests = []
    for i in range(ndest):
        b = 6 + 4 * i
        dcls = _uint(cols[b], "dest[%d].class" % i, path, lineno)
        darch = _uint(cols[b + 1], "dest[%d].arch" % i, path, lineno)
        dphys = _uint(cols[b + 2], "dest[%d].phys" % i, path, lineno)
        dval = _val(cols[b + 3], "dest[%d].val" % i, path, lineno)
        dests.append((dcls, darch, dphys, dval))
    return Rec(seq, tid, tick, pc, op, ndest, dests, line, lineno)


def iter_records(path):
    """Yield Rec objects from `path` in file order (seq strictly increasing)."""
    fh = open_text(path)
    lineno = 0
    prev_seq = None
    try:
        for raw in fh:
            lineno += 1
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue  # blank line: not a record, but still counted in numbering
            rec = parse_line(path, lineno, line)
            if prev_seq is None:
                if rec.seq != 0:
                    raise TraceError("%s: line %d: 首条记录 seq=%d，"
                                     "钉死格式要求 seq 从 0 起" % (path, lineno, rec.seq))
            elif rec.seq <= prev_seq:
                raise TraceError("%s: line %d: seq=%d 未严格递增"
                                 "（前一条 seq=%d）" % (path, lineno, rec.seq, prev_seq))
            prev_seq = rec.seq
            yield rec
    except UnicodeDecodeError as e:
        raise TraceError("%s: line %d 附近存在非 UTF-8 字节: %s"
                         % (path, lineno + 1, e))
    except (OSError, EOFError) as e:  # includes BadGzipFile / truncated gzip
        raise TraceError("%s: line %d 附近读取失败: %s" % (path, lineno + 1, e))
    finally:
        fh.close()


# ------------------------------------------------------------- comparison

def _pair_divergence(r, u):
    """Field-priority chain for one aligned (same-seq) pair.

    Returns None if every instruction field matches, else
    (class_key, level, detail_message).
    """
    if r.pc != u.pc:
        return ("instruction_flow_change", "pc",
                "pc: ref=%s run=%s" % (r.pc, u.pc))
    if r.op != u.op:
        return ("instruction_substitution", "op",
                "op: ref=%s run=%s" % (r.op, u.op))
    if r.ndest != u.ndest:
        return ("operand_forced_switch", "dest_count",
                "目的寄存器数量 ndest: ref=%d run=%d" % (r.ndest, u.ndest))
    for i in range(r.ndest):
        rd, ud = r.dests[i], u.dests[i]
        if (rd[0], rd[1]) != (ud[0], ud[1]):
            return ("operand_forced_switch", "dest[%d].arch" % i,
                    "dest[%d] arch id: ref=(class %d, arch %d) "
                    "run=(class %d, arch %d)" % (i, rd[0], rd[1], ud[0], ud[1]))
    for i in range(r.ndest):
        if r.dests[i][3] != u.dests[i][3]:
            return ("data_corruption", "dest[%d].val" % i,
                    "dest[%d] val: ref=%s run=%s"
                    % (i, r.dests[i][3], u.dests[i][3]))
    return None


def compare(ref_path, run_path, tick_tol):
    """Merge-join both traces on seq (streaming, O(1) memory) and classify."""
    it_ref = iter_records(ref_path)
    it_run = iter_records(run_path)
    r = next(it_ref, None)
    u = next(it_run, None)

    counts = dict.fromkeys(CLASS_KEYS, 0)
    first_seq = dict.fromkeys(CLASS_KEYS, None)
    first_point = None
    total_points = 0

    n_ref = n_run = aligned = 0
    phys_mis = tid_mis = 0
    tick_pairs = 0
    max_drift = None
    max_drift_seq = None
    first_over_tol = None
    # Tick divergence points are only kept while no field divergence has been
    # seen; a later field divergence discards them (① requires 全程字段全同).
    field_seen = False
    pending_tick_n = 0
    pending_tick_first = None  # (seq, ref_rec, run_rec)

    def add_point(seq, key, level, detail, rr, uu):
        nonlocal first_point, total_points
        total_points += 1
        counts[key] += 1
        if first_seq[key] is None:
            first_seq[key] = seq
        if first_point is None:
            first_point = {
                "seq": seq,
                "class": key,
                "class_zh": ZH[key],
                "level": level,
                "detail": detail,
                "ref_line": rr.raw if rr is not None else None,
                "run_line": uu.raw if uu is not None else None,
            }

    while (r is not None) or (u is not None):
        if u is None or (r is not None and r.seq < u.seq):
            # seq present only in ref
            add_point(r.seq, "instruction_flow_change", "presence",
                      "seq %d 仅存在于 ref（run 侧缺失）" % r.seq, r, None)
            field_seen = True
            n_ref += 1
            r = next(it_ref, None)
        elif r is None or r.seq > u.seq:
            # seq present only in run
            add_point(u.seq, "instruction_flow_change", "presence",
                      "seq %d 仅存在于 run（ref 侧缺失）" % u.seq, None, u)
            field_seen = True
            n_run += 1
            u = next(it_run, None)
        else:
            # aligned pair (same seq)
            n_ref += 1
            n_run += 1
            aligned += 1
            pt = _pair_divergence(r, u)
            if pt is not None:
                key, level, detail = pt
                add_point(r.seq, key, level, detail, r, u)
                if not field_seen:
                    field_seen = True
                    pending_tick_n = 0
                    pending_tick_first = None
            else:
                # field-identical pair: aux diagnostics + tick comparison
                if r.tid != u.tid:
                    tid_mis += 1
                if [d[2] for d in r.dests] != [d[2] for d in u.dests]:
                    phys_mis += 1
                tick_pairs += 1
                drift = abs(r.tick - u.tick)
                if max_drift is None or drift > max_drift:
                    max_drift, max_drift_seq = drift, r.seq
                if drift > tick_tol and first_over_tol is None:
                    first_over_tol = r.seq
                if (not field_seen) and drift > tick_tol:
                    pending_tick_n += 1
                    if pending_tick_first is None:
                        pending_tick_first = (r.seq, r, u)
            r = next(it_ref, None)
            u = next(it_run, None)

    # ①执行时间错 only when the whole trace pair is field-identical
    if (not field_seen) and pending_tick_first is not None:
        seq, rr, uu = pending_tick_first
        counts["timing_error"] = pending_tick_n
        first_seq["timing_error"] = seq
        total_points += pending_tick_n
        first_point = {
            "seq": seq,
            "class": "timing_error",
            "class_zh": ZH["timing_error"],
            "level": "tick",
            "detail": "tick: ref=%d run=%d（漂移 %d > 容差 %d）"
                      % (rr.tick, uu.tick, abs(rr.tick - uu.tick), tick_tol),
            "ref_line": rr.raw,
            "run_line": uu.raw,
        }

    verdict = "diverged" if first_point is not None else "no_divergence"
    return {
        "tool": "commit_diff",
        "trace_format": TRACE_FORMAT,
        "ref": ref_path,
        "ref_instructions": n_ref,
        "run": run_path,
        "run_instructions": n_run,
        "aligned_pairs": aligned,
        "tick_tol": tick_tol,
        "verdict": verdict,
        "primary_class": first_point["class"] if first_point else None,
        "primary_class_zh": (first_point["class_zh"] if first_point
                             else NO_DIVERGENCE_ZH),
        "latency_seq": first_point["seq"] if first_point else None,
        "first_divergence": first_point,
        "divergence_counts": {k: counts[k] for k in CLASS_KEYS},
        "first_seq_per_class": {k: first_seq[k] for k in CLASS_KEYS},
        "total_divergence_points": total_points,
        "aux": {
            "phys_mismatch": phys_mis,
            "tid_mismatch": tid_mis,
            "tick_compared_pairs": tick_pairs,
            "max_tick_drift": max_drift,
            "max_tick_drift_seq": max_drift_seq,
            "first_tick_over_tol_seq": first_over_tol,
        },
    }


# ----------------------------------------------------------------- report

def _fmt_seq(x):
    return "n/a" if x is None else str(x)


def format_report(res):
    lines = []
    lines.append("== commit_diff (W2.2): TC'23 L2 五分类离线比对 ==")
    lines.append("ref: %s  (%d 条提交指令)"
                 % (res["ref"], res["ref_instructions"]))
    lines.append("run: %s  (%d 条提交指令)"
                 % (res["run"], res["run_instructions"]))
    lines.append("对齐指令对: %d    tick 容差: %d"
                 % (res["aligned_pairs"], res["tick_tol"]))
    lines.append("")
    if res["verdict"] == "no_divergence":
        lines.append("[结论] 主分类: %s (no_divergence) —— 全程指令字段一致"
                     "且 tick 漂移 ≤ 容差" % NO_DIVERGENCE_ZH)
        lines.append("[潜伏期] n/a（无分歧）")
    else:
        fd = res["first_divergence"]
        lines.append("[结论] 主分类: %s (%s)" % (fd["class_zh"], fd["class"]))
        lines.append("[潜伏期] 首分歧 seq = %d" % res["latency_seq"])
        lines.append("[首分歧明细]")
        lines.append("  seq %d  分歧层级: %s" % (fd["seq"], fd["level"]))
        lines.append("  detail: %s" % fd["detail"])
        lines.append("  ref: %s" % (fd["ref_line"] if fd["ref_line"] is not None
                                    else "<该侧无此 seq 记录>"))
        lines.append("  run: %s" % (fd["run_line"] if fd["run_line"] is not None
                                    else "<该侧无此 seq 记录>"))
    lines.append("")
    lines.append("[全程分歧点计数]  (主类 = 首个分歧点; 其余分歧点计入各类)")
    for k in CLASS_KEYS:
        extra = ""
        if res["divergence_counts"][k] > 0:
            extra = "  (首见 seq %s)" % res["first_seq_per_class"][k]
        lines.append("  %s (%s): %d%s"
                     % (ZH[k], k, res["divergence_counts"][k], extra))
    lines.append("  合计分歧点: %d" % res["total_divergence_points"])
    lines.append("")
    a = res["aux"]
    lines.append("[辅助诊断]  (不计入五分类)")
    lines.append("  字段一致对上: phys 不匹配 %d 条, tid 不匹配 %d 条"
                 % (a["phys_mismatch"], a["tid_mismatch"]))
    if a["max_tick_drift"] is not None:
        lines.append("  tick 漂移 (仅字段一致对, 共 %d 对): max %d @ seq %s; "
                     "首超容差(>%d): seq %s"
                     % (a["tick_compared_pairs"], a["max_tick_drift"],
                        _fmt_seq(a["max_tick_drift_seq"]), res["tick_tol"],
                        _fmt_seq(a["first_tick_over_tol_seq"])))
    else:
        lines.append("  tick 漂移: 无可比对的字段一致指令对")
    return "\n".join(lines)


# -------------------------------------------------------------------- cli

def _nonneg_int(s):
    try:
        v = int(s, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid int value: %r" % s)
    if v < 0:
        raise argparse.ArgumentTypeError("must be >= 0, got %d" % v)
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="commit_diff.py",
        description="TC'23 L2 commit-trace 五分类离线比对器 (W2.2)。"
                    "trace 行格式钉死: " + TRACE_FORMAT)
    ap.add_argument("--ref", required=True, metavar="A.csv.gz",
                    help="无故障参照 trace（gzip 或纯文本，按 magic 自动识别）")
    ap.add_argument("--run", required=True, metavar="B.csv.gz",
                    help="注入运行 trace（gzip 或纯文本，按 magic 自动识别）")
    ap.add_argument("--json", metavar="OUT", default=None,
                    help="把同一结论写成机器可读 JSON 到该文件"
                         "（人读报告仍打印到 stdout）")
    ap.add_argument("--tick-tol", type=_nonneg_int, default=0, metavar="T",
                    help="tick 漂移容差，默认 0（tick 必须完全一致）")
    args = ap.parse_args(argv)

    try:
        res = compare(args.ref, args.run, args.tick_tol)
    except TraceError as e:
        sys.stderr.write("commit_diff: ERROR: %s\n" % e)
        return 1

    sys.stdout.write(format_report(res) + "\n")

    if args.json is not None:
        try:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as e:
            sys.stderr.write("commit_diff: ERROR: cannot write --json '%s': %s\n"
                             % (args.json, e.strerror or e))
            return 1
        sys.stderr.write("commit_diff: json written to %s\n" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
