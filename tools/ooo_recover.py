#!/usr/bin/env python3
"""ooo_recover.py — OOO 轨样本 COMPLETE 标记与恢复对账扫描。

总方针（用户指令）§三.5/§三.6 的可审计实现：

  mark-complete  样本结果目录内原子落位 COMPLETE.json（tmp 写入 + os.replace），
                 含 run_key / exit / classification / evidence / created_utc /
                 自校验 sha256（对除 sha256 外字段的规范化 JSON 计算）。
                 标记不可变：目录内已存在 COMPLETE.json 即拒绝覆盖；
                 事后任何改动都会被 scan 的 sha256 校验检出。

  scan           遍历运行根目录，逐样本输出状态（只报告、不修改；恢复动作由
                 campaign 层决策）：
                   COMPLETE     有效 COMPLETE.json（sha256 自校验通过）
                   RUNNING      无 COMPLETE、manifest 在、心跳新鲜(< 阈值)
                   INTERRUPTED  无有效 COMPLETE、已启动(manifest 在)但心跳陈旧/
                                缺失，或标记/manifest 损坏、run_key 冲突
                   MISSING      预期清单(--expected)有而磁盘无；或 sample_* 空
                                目录（未真正启动，恢复动作与缺失相同）
                   ORPHAN       磁盘存在但不在预期清单（未给 --expected 时该
                                状态不可判定，输出中显式注明，不臆测）

  selftest       在 runs/ooo/selftest/ 下构造 9 项夹具（五种状态全覆盖 + 不可变
                 /run_key 不一致两个拒绝路径），断言 scan 结果一致。

run_key 约定（总方针 §三.5）：campaign/phase/RunID/sample_index/seed/config_sha。
恢复规则（§三.6）：已 COMPLETE 跳过；只恢复 MISSING / 明确 INTERRUPTED 的样本。

独立于 gem5 构建，python3.9（login01）可运行；P0 工程件（计划
docs/superpowers/plans/2026-09-30-ooo-p0-engineering-pass.md Unit 2）。
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

DEFAULT_RUN_ROOT = os.path.join("runs", "ooo")
SELFTEST_ROOT = os.path.join(DEFAULT_RUN_ROOT, "selftest")
DEFAULT_HEARTBEAT_STALE_SEC = 600          # 心跳超过 10 分钟视为陈旧
EXCLUDED_TOP_DIRS = {"guard", "selftest"}  # 守卫锁目录/自测夹具不参与对账
COMPLETE_NAME = "COMPLETE.json"
MANIFEST_NAME = "manifest.json"
HEARTBEAT_NAME = "heartbeat"


def die(msg, code=2):
    sys.stderr.write("FATAL: %s\n" % msg)
    sys.exit(code)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def marker_sha(fields):
    return hashlib.sha256(canonical(fields).encode("utf-8")).hexdigest()


def load_json(path):
    """返回 (obj, None) 或 (None, 错误说明)；错误说明 'absent' 表示文件不存在。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "absent"
    except (OSError, ValueError) as e:
        return None, str(e)


def read_expected(path):
    """预期 run_key 清单：txt（每行一个，# 注释）或 JSON 字符串数组。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if text.lstrip().startswith("["):
        data = json.loads(text)
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            die("--expected JSON 必须为字符串数组: %s" % path)
        return set(data)
    keys = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            keys.add(line)
    return keys

# ------------------------------------------------------------ mark-complete

def mark_complete(run_dir, run_key, exit_code, classification, evidence,
                  allow_no_manifest=False, note=None):
    """原子写入 COMPLETE.json；已存在即拒绝（不可变标记约定）。"""
    marker_path = os.path.join(run_dir, COMPLETE_NAME)
    if os.path.exists(marker_path):
        die("%s 已存在：COMPLETE 标记不可变，拒绝覆盖（重做须显式删除并留痕）"
            % marker_path)
    manifest, merr = load_json(os.path.join(run_dir, MANIFEST_NAME))
    notes = []
    if merr == "absent":
        if not allow_no_manifest:
            die("样本目录缺 %s（未启动却要标记完成？）；确需如此请加 --allow-no-manifest"
                % MANIFEST_NAME)
        notes.append("no_manifest(--allow-no-manifest)")
    elif merr:
        die("manifest.json 无法解析: %s" % merr)
    else:
        mk = manifest.get("run_key")
        if isinstance(mk, str) and mk != run_key:
            die("run_key 不一致：manifest=%r 而 --run-key=%r" % (mk, run_key))
    if note:
        notes.append(note)
    fields = {
        "run_key": run_key,
        "exit": exit_code,
        "classification": classification,
        "evidence": list(evidence or []),
        "created_utc": utc_now(),
        "marker_version": 1,
    }
    if notes:
        fields["note"] = "; ".join(notes)
    fields["sha256"] = marker_sha(fields)
    tmp = os.path.join(run_dir, "%s.tmp.%d.%d"
                       % (COMPLETE_NAME, os.getpid(), time.time_ns() // 1000))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(canonical(fields) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, marker_path)   # 同目录 rename，POSIX 原子
    return fields


# --------------------------------------------------------------------- scan

def discover_run_dirs(root):
    """递归发现样本目录：名为 sample_*，或含 manifest.json/COMPLETE.json。
    不下钻已识别的样本目录（其子目录是输出产物）。"""
    found = []
    root_abs = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        if os.path.abspath(dirpath) == root_abs:
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_TOP_DIRS]
        else:
            dirnames[:] = [d for d in dirnames if d != ".git"]
        here = os.path.basename(dirpath)
        if dirpath != root and (here.startswith("sample_")
                                or MANIFEST_NAME in filenames
                                or COMPLETE_NAME in filenames):
            found.append(dirpath)
            dirnames[:] = []   # 样本目录内部是产物，不再下钻
    return sorted(found)


def classify_run_dir(d, stale_sec):
    """返回 (state, run_key, note, detail)。state 为 None 表示发现规则外的目录。"""
    complete, cerr = load_json(os.path.join(d, COMPLETE_NAME))
    if cerr is None:
        sha = complete.pop("sha256", None)
        problems = []
        if not isinstance(complete.get("run_key"), str):
            problems.append("marker_invalid:no_run_key")
        elif not isinstance(sha, str) or sha != marker_sha(complete):
            problems.append("marker_invalid:sha256_mismatch")
        manifest, merr = load_json(os.path.join(d, MANIFEST_NAME))
        if merr is None:
            mk = manifest.get("run_key")
            if isinstance(mk, str) and mk != complete.get("run_key"):
                problems.append("run_key_mismatch(manifest=%r)" % mk)
        if problems:
            return ("INTERRUPTED", complete.get("run_key"),
                    "; ".join(problems), None)
        return ("COMPLETE", complete["run_key"], None, complete)
    if cerr != "absent":
        return ("INTERRUPTED", None, "marker_unreadable:%s" % cerr, None)
    # —— 无 COMPLETE.json ——
    manifest, merr = load_json(os.path.join(d, MANIFEST_NAME))
    if merr == "absent":
        if os.path.basename(d).startswith("sample_"):
            return ("MISSING", None, "empty_dir(无 manifest，未真正启动)", None)
        return (None, None, "not_a_run_dir", None)
    run_key = manifest.get("run_key") if isinstance(manifest, dict) else None
    if merr:
        return ("INTERRUPTED", run_key, "manifest_invalid:%s" % merr, None)
    try:
        age = max(0.0, time.time() - os.stat(os.path.join(d, HEARTBEAT_NAME)).st_mtime)
    except OSError:
        return ("INTERRUPTED", run_key, "heartbeat_absent", None)
    if age <= stale_sec:
        return ("RUNNING", run_key, "heartbeat_age=%.0fs" % age, None)
    return ("INTERRUPTED", run_key,
            "heartbeat_stale(%.0fs > %ds)" % (age, stale_sec), None)


def run_scan(run_root, expected=None, stale_sec=DEFAULT_HEARTBEAT_STALE_SEC):
    """扫描 + 对账。expected=None 表示无预期清单（ORPHAN 不可判定，显式注明）。"""
    runs = []
    seen = {}
    for d in discover_run_dirs(run_root):
        state, run_key, note, detail = classify_run_dir(d, stale_sec)
        if state is None:
            continue
        entry = {"run_dir": os.path.relpath(d, run_root),
                 "run_key": run_key, "state": state}
        if note:
            entry["note"] = note
        if state == "COMPLETE":
            entry["exit"] = detail.get("exit")
            entry["classification"] = detail.get("classification")
            if detail.get("note"):
                entry["note"] = (entry["note"] + "; " + detail["note"])                     if entry.get("note") else detail["note"]
        runs.append(entry)
        if run_key:
            seen.setdefault(run_key, []).append(d)
    for run_key, dirs in seen.items():
        if len(dirs) > 1:
            tag = "duplicate_run_key(x%d)" % len(dirs)
            for e in runs:
                if e["run_key"] == run_key:
                    e["note"] = (e["note"] + "; " + tag) if e.get("note") else tag
    if expected is not None:
        for run_key in sorted(expected - set(seen)):
            runs.append({"run_dir": None, "run_key": run_key,
                         "state": "MISSING", "note": "no_dir(清单有而磁盘无)"})
        for e in runs:
            if (e["run_key"] is not None and e["run_key"] not in expected
                    and e["run_dir"] is not None):
                e["disk_state"] = e["state"]
                e["state"] = "ORPHAN"
    counts = {}
    for e in runs:
        counts[e["state"]] = counts.get(e["state"], 0) + 1
    return {
        "generated_utc": utc_now(),
        "run_root": run_root,
        "expected": "provided" if expected is not None else None,
        "heartbeat_stale_sec": stale_sec,
        "orphan_undeterminable": expected is None,
        "counts": counts,
        "total": len(runs),
        "runs": runs,
    }

# --------------------------------------------------------------------- CLI

def cmd_mark_complete(args):
    marker = mark_complete(args.run_dir, args.run_key, args.exit,
                           args.classification, args.evidence,
                           allow_no_manifest=args.allow_no_manifest,
                           note=args.note)
    print("COMPLETE 标记已原子落位: %s"
          % os.path.join(args.run_dir, COMPLETE_NAME))
    print("  run_key=%s exit=%s classification=%s"
          % (marker["run_key"], marker["exit"], marker["classification"]))
    print("  sha256=%s" % marker["sha256"])
    return 0


def cmd_scan(args):
    expected = read_expected(args.expected) if args.expected else None
    result = run_scan(args.run_root, expected, args.heartbeat_stale_sec)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for e in result["runs"]:
            loc = e["run_dir"] if e["run_dir"] else "(磁盘无目录)"
            line = "[%s] %s  %s" % (e["state"], e["run_key"] or "(run_key 未知)", loc)
            if e.get("note"):
                line += "  — " + e["note"]
            print(line)
        print("—")
        print("共 %d 项: %s" % (result["total"], ", ".join(
            "%s=%d" % kv for kv in sorted(result["counts"].items())) or "(空)"))
        if result["orphan_undeterminable"]:
            print("注: 未提供 --expected，ORPHAN 不可判定（仅报告磁盘实况）")
    return 0


# ----------------------------------------------------------------- selftest

def _st_mkdirs(root, rel):
    d = os.path.join(root, rel)
    os.makedirs(d, exist_ok=True)
    return d


def _st_manifest(d, run_key):
    with open(os.path.join(d, MANIFEST_NAME), "w", encoding="utf-8") as f:
        json.dump({"run_key": run_key, "manifest_version": 1}, f)


def _st_heartbeat(d, stale_sec_ago=0):
    p = os.path.join(d, HEARTBEAT_NAME)
    with open(p, "w", encoding="utf-8") as f:
        f.write(utc_now() + "\n")
    if stale_sec_ago > 0:
        t = time.time() - stale_sec_ago
        os.utime(p, (t, t))


def cmd_selftest(args):
    import shutil
    fixture = os.path.join(SELFTEST_ROOT, "recover-st-%d" % os.getpid())
    if os.path.isdir(fixture):
        shutil.rmtree(fixture)
    os.makedirs(fixture)

    kA1 = "campA/p1/R001/sample_0001_deadbeef"
    kA2 = "campA/p1/R001/sample_0002_cafe0000"
    kA3 = "campA/p1/R001/sample_0003_1234abcd"
    kA5 = "campA/p1/R002/sample_0001_900dcafe"
    kA6 = "campA/p1/R003/sample_0001_11112222"
    kA7 = "campA/p1/R004/sample_0001_33334444"
    kB1 = "campB/p2/R009/sample_0001_feedface"
    kPH = "campC/p3/R777/sample_0099_c0ffee00"

    # A1: 陈旧心跳 → INTERRUPTED
    d = _st_mkdirs(fixture, "campA/p1/R001/sample_0001_deadbeef")
    _st_manifest(d, kA1); _st_heartbeat(d, stale_sec_ago=7200)
    # A2: 新鲜心跳 → RUNNING
    d = _st_mkdirs(fixture, "campA/p1/R001/sample_0002_cafe0000")
    _st_manifest(d, kA2); _st_heartbeat(d)
    # A3: mark-complete 正常路径 → COMPLETE
    d = _st_mkdirs(fixture, "campA/p1/R001/sample_0003_1234abcd")
    _st_manifest(d, kA3)
    mark_complete(d, kA3, 0, "Masked",
                  ["m5out/stats.txt", "m5out/simout.txt"])
    # A4: 空目录 → MISSING(empty_dir)
    _st_mkdirs(fixture, "campA/p1/R001/sample_0004_0badf00d")
    # A5: 标记被篡改 → INTERRUPTED(marker_invalid:sha256_mismatch)
    d = _st_mkdirs(fixture, "campA/p1/R002/sample_0001_900dcafe")
    _st_manifest(d, kA5)
    mark_complete(d, kA5, 0, "Masked", ["m5out/stats.txt"])
    mp = os.path.join(d, COMPLETE_NAME)
    tampered, _ = load_json(mp)
    tampered["exit"] = 5          # 事后篡改，未重算 sha256
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(tampered, f)
    # A6: run_key 不一致 → mark-complete 拒绝（目录保留为 INTERRUPTED）
    d = _st_mkdirs(fixture, "campA/p1/R003/sample_0001_11112222")
    _st_manifest(d, kA6)
    try:
        mark_complete(d, kA6.replace("11112222", "99999999"), 0, "Masked", [])
        print("FAIL A6-refuse: run_key 不一致未被拒绝")
        return 1
    except SystemExit:
        pass
    # A7: --allow-no-manifest → COMPLETE（带 note）
    d = _st_mkdirs(fixture, "campA/p1/R004/sample_0001_33334444")
    mark_complete(d, kA7, 0, "simfail", ["m5out/stats.txt"],
                  allow_no_manifest=True)
    # B1: 磁盘存在但不在清单 → ORPHAN
    d = _st_mkdirs(fixture, "campB/p2/R009/sample_0001_feedface")
    _st_manifest(d, kB1)
    mark_complete(d, kB1, 0, "SDC", ["m5out/stats.txt"])
    # A3 二次 mark-complete：不可变拒绝
    d3 = os.path.join(fixture, "campA/p1/R001/sample_0003_1234abcd")
    try:
        mark_complete(d3, kA3, 0, "Masked", [])
        print("FAIL immutable-refuse: 已存在标记未被拒绝")
        return 1
    except SystemExit:
        pass

    ledger = os.path.join(fixture, "expected.txt")
    with open(ledger, "w", encoding="utf-8") as f:
        for k in (kA1, kA2, kA3, kA5, kA6, kA7, kPH):
            f.write(k + "\n")
        f.write("# campB 不在清单 → ORPHAN\n")
    expected = read_expected(ledger)
    result = run_scan(fixture, expected)
    by_key = {}
    for e in result["runs"]:
        if e["run_key"]:
            by_key.setdefault(e["run_key"], []).append(e)

    checks = [
        ("A1 陈旧心跳", kA1, "INTERRUPTED", "heartbeat_stale"),
        ("A2 新鲜心跳", kA2, "RUNNING", "heartbeat_age"),
        ("A3 正常标记", kA3, "COMPLETE", None),
        ("A5 标记被篡改", kA5, "INTERRUPTED", "marker_invalid:sha256_mismatch"),
        ("A6 拒绝后残留", kA6, "INTERRUPTED", "heartbeat_absent"),
        ("A7 无manifest标记", kA7, "COMPLETE", "no_manifest"),
        ("B1 清单外", kB1, "ORPHAN", None),
        ("PHANTOM 清单幽灵", kPH, "MISSING", "no_dir"),
    ]
    failed = 0
    for label, key, want_state, want_note in checks:
        entries = by_key.get(key, [])
        e = entries[0] if entries else None
        ok = e is not None and e["state"] == want_state
        if ok and want_note:
            ok = want_note in (e.get("note") or "")
        if ok and label.startswith("A3"):
            ok = e.get("exit") == 0 and e.get("classification") == "Masked"
        if ok and label.startswith("B1"):
            ok = e.get("disk_state") == "COMPLETE"
        print("%s %s -> %s" % ("PASS" if ok else "FAIL", label, want_state))
        if not ok:
            failed += 1
            print("   期望 state=%s note~%s 实际=%r" % (want_state, want_note, e))
    empty = [e for e in result["runs"]
             if (e.get("note") or "").startswith("empty_dir")]
    ok = len(empty) == 1 and empty[0]["state"] == "MISSING"
    print("%s A4 空目录 -> MISSING(empty_dir)" % ("PASS" if ok else "FAIL"))
    if not ok:
        failed += 1
        print("   实际=%r" % empty)
    want_counts = {"COMPLETE": 2, "INTERRUPTED": 3, "MISSING": 2,
                   "ORPHAN": 1, "RUNNING": 1}
    ok = result["counts"] == want_counts and result["total"] == 9
    print("%s 汇总计数 %s (total=%d)"
          % ("PASS" if ok else "FAIL", result["counts"], result["total"]))
    if not ok:
        failed += 1
        print("   期望=%r total=9" % want_counts)
    if failed == 0 and not args.keep:
        shutil.rmtree(fixture)
        print("夹具已清理（--keep 可保留）")
    else:
        print("夹具保留于: %s" % fixture)
    print("SELFTEST %s" % ("PASS" if failed == 0 else "FAIL(%d 项)" % failed))
    return 0 if failed == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="OOO 轨 COMPLETE 标记与恢复对账（scan 只报告不修改）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mark-complete", help="原子落位 COMPLETE.json（不可变）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-key", required=True)
    p.add_argument("--exit", type=int, default=None, help="样本退出码")
    p.add_argument("--classification", default=None,
                   help="分类（tools/classify.py 口径）")
    p.add_argument("--evidence", action="append", default=[],
                   help="证据路径（可多次）")
    p.add_argument("--allow-no-manifest", action="store_true")
    p.add_argument("--note", default=None)
    p.set_defaults(func=cmd_mark_complete)
    p = sub.add_parser("scan", help="扫描对账（只报告，不修改）")
    p.add_argument("--run-root", default=DEFAULT_RUN_ROOT)
    p.add_argument("--expected", help="预期 run_key 清单（txt 或 JSON 数组）")
    p.add_argument("--heartbeat-stale-sec", type=int,
                   default=DEFAULT_HEARTBEAT_STALE_SEC)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_scan)
    p = sub.add_parser("selftest", help="构造夹具并断言 scan（runs/ooo/selftest/）")
    p.add_argument("--keep", action="store_true")
    p.set_defaults(func=cmd_selftest)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
