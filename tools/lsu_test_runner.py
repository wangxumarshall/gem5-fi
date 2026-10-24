#!/usr/bin/env python3
"""lsu_test_runner.py — 真实运行 tests/ 下的**全部**套件（含 pytest 不收集的独立脚本）。

动机（R5-U2，缺陷实测）：`tests/test_lsu_*.py` 中大多数是 `main()` 独立脚本，
`python3 -m pytest tests/ -q` **只收集 21 个**（实测 `--collect-only`），其余约 50 个
hook/契约套件从不被执行 —— 这本身就足以让它们的红完全不进入门禁，
曾掩护 R4-4 `corr` 契约收紧后两个 hook 套件长达数周的静默红（R5-U1）。

判定口径（[R5-U7] 独立复核 F3 纠正）：**以解析输出为准，rc 仅作辅助**。
实测 `tests/test_lsu_hook_{tlb,cpf}.py` 失败时确实 exit 1，但**不得假定所有
套件都如此** —— 本仓库各代脚本的判定风格不一，只依赖 rc 会在"打印失败却
exit 0"的套件上静默放行。反之，**输出不可识别时按 FAIL 处理**（诚实缺省），
绝不按 PASS。

本运行器逐个套件以真实子进程执行、解析真实输出，分类如下：

  PASS   rc==0 且末行含 `ALL PASS` 或 `FAILURES: 无`
  SKIP   rc==0 且末行含 `SKIPPED`（诚实跳过，理由同行输出）
  ENV    输出含 FileNotFoundError / No such file or directory（环境阻塞：缺二进制或
         资产）——必须披露，绝不并入 PASS
  FAIL   `FAILURES: [...]` 非空，或 rc!=0，或出现 Traceback

追踪（[LSU][MDSPEC][R6-DIAGRUNNER] 2026-10-24，**仅诊断用，绝不改判定**）：
默认只把每个套件的末 3 行摘要打到 stdout，**完整** stdout/stderr/traceback 被丢弃，
导致一条被截断的 traceback（`File ".../tools/lsu_o…`）无法归因。`--log-dir DIR`
为每个套件落盘完整证据（stdout/stderr/meta.json：rc、signal、timeout、起止时间、
耗时），判定逻辑与本文件 `classify()` 完全一致（逐字节未动）。`--only SPEC` 只跑
指定套件（按相对路径/文件名匹配；不含 pytest 收集阶段），供逐套件复现用。

用法：
  python3 tools/lsu_test_runner.py [--json OUT] [--timeout SEC] [--quiet]
                                   [--log-dir DIR] [--only SPEC ...]
退出码：0 当且仅当无 FAIL；ENV 存在时打印醒目披露但不单独判负（由调用方决定）。
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TESTS = REPO / "tests"

FAILPAT = re.compile(r"FAILURES:\s*\[(?P<body>[^\]]*)\]")
ENVPAT = re.compile(r"FileNotFoundError|No such file or directory")


def pytest_owned() -> set:
    """pytest 收集到的套件文件（相对 REPO 的路径），避免重复执行。"""
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/",
                        "--collect-only", "-q"],
                       capture_output=True, text=True, cwd=str(REPO))
    owned = set()
    for ln in (r.stdout or "").splitlines():
        ln = ln.strip()
        if "::" in ln:
            owned.add(ln.split("::")[0])
    return owned


def classify(rc, out):
    """由真实输出判定（脚本 exit 0 不可信，故必须解析文本）。"""
    text = out or ""
    tail = "\n".join(text.strip().splitlines()[-3:])
    if ENVPAT.search(text) and "FAILURES" not in text and "Traceback" in text:
        return "ENV", tail
    if "Traceback (most recent call last)" in text:
        if ENVPAT.search(text):
            return "ENV", tail
        return "FAIL", tail
    m = FAILPAT.search(text)
    if m:
        body = m.group("body").strip()
        if body and body not in ("无",):
            return "FAIL", f"FAILURES: [{body[:120]}]"
        return "PASS", "FAILURES: [无]"
    # 无括号的 "FAILURES: 无" 是另一族的通过标记（FAILPAT 要求方括号，故单列）
    if re.search(r"FAILURES:\s*无", text):
        return "PASS", "FAILURES: 无"
    if "ALL PASS" in text:
        return "PASS", "ALL PASS"
    if "SKIPPED" in text:
        return "SKIP", tail
    if rc != 0:
        return "FAIL", tail
    # [R5-U7] F3：输出不可识别时**不得**默认 PASS。rc==0 只说明进程正常退出，
    # 不说明断言通过（历史上存在"打印失败仍 exit 0"的判定风格）。
    return "FAIL", "rc=0 但输出无可识别的判定标记（未见 ALL PASS / FAILURES）"


def _run_and_capture(argv, cwd, timeout, env=None):
    """真实子进程执行并**完整**保留 stdout/stderr/rc/signal/timeout/时序。

    signal 约定：subprocess 返回值 rc<0 表示被信号 -rc 终止（POSIX）。
    绝不吞异常：TimeoutExpired 如实记录为 timeout=True 并保留已捕获输出。
    """
    t0 = time.time()
    t0_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0))
    timed_out = False
    try:
        r = subprocess.run(argv, capture_output=True, text=True, cwd=cwd,
                           timeout=timeout, env=env)
        rc, so, se = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        rc = None

        def _txt(x):
            if x is None:
                return ""
            return x.decode(errors="replace") if isinstance(x, bytes) else x
        so, se = _txt(e.stdout), _txt(e.stderr)
    t1 = time.time()
    meta = {
        "argv": [str(x) for x in argv], "cwd": str(cwd),
        "start": t0_iso, "end": time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(t1)),
        "seconds": round(t1 - t0, 3), "rc": rc,
        "signal": (-rc if (rc is not None and rc < 0) else None),
        "timeout": timed_out, "timeout_budget_s": timeout,
    }
    return so, se, rc, meta


def run_one(path, timeout, log_dir=None):
    """执行单个套件；判定口径与本文件 classify() 一致（未改）。

    log_dir 给定时额外落盘 <suite>.stdout / <suite>.stderr / <suite>.meta.json
    （完整证据，含非零 rc / 信号终止 / timeout 标记），**不改变** PASS/FAIL 判定。
    """
    so, se, rc, meta = _run_and_capture([sys.executable, str(path)],
                                        str(REPO), timeout)
    combined = (so or "") + (se or "")
    status, detail = classify(rc if rc is not None else 1, combined)
    meta["suite"] = f"tests/{Path(path).name}"
    meta["runner_status"] = status
    meta["runner_detail"] = detail
    if log_dir is not None:
        stem = Path(path).name
        d = Path(log_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{stem}.stdout").write_text(so or "")
        (d / f"{stem}.stderr").write_text(se or "")
        (d / f"{stem}.meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1))
    return status, detail


def _select_only(specs):
    """--only：按相对路径 / 文件名匹配 tests/ 下的套件（不改判定，仅选择范围）。"""
    chosen = []
    for f in sorted(TESTS.glob("test_*.py")):
        rel = f"tests/{f.name}"
        if any(sp in (rel, f.name) for sp in specs):
            chosen.append(f)
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="结果 JSON 输出路径")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--log-dir", default=None,
                    help="逐套件完整证据落盘目录（stdout/stderr/meta.json）；"
                         "仅诊断，不改判定")
    ap.add_argument("--only", nargs="+", default=None,
                    help="只跑指定套件（相对路径或文件名；跳过 pytest 收集），"
                         "供逐套件复现")
    a = ap.parse_args()

    results = []

    if a.only:
        owned = set()
        targets = _select_only(a.only)
    else:
        owned = pytest_owned()
        targets = None

        # 1) pytest 自身（覆盖其收集到的套件）
        so, se, rc, meta = _run_and_capture(
            [sys.executable, "-m", "pytest", "tests/", "-q"], str(REPO), None)
        pt = ((so or "") + (se or "")).strip().splitlines()[-1:] or [""]
        if a.log_dir:
            d = Path(a.log_dir)
            d.mkdir(parents=True, exist_ok=True)
            (d / "pytest_collect.stdout").write_text(so or "")
            (d / "pytest_collect.stderr").write_text(se or "")
            (d / "pytest_collect.meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=1))
        results.append({"suite": "pytest::collect", "status":
                        "PASS" if rc == 0 else "FAIL",
                        "detail": pt[0][:160], "collects": len(owned)})

    # 2) 全部独立脚本（pytest 未收集者）；--only 时只跑选定套件
    files = targets if targets is not None else sorted(TESTS.glob("test_*.py"))
    for f in files:
        rel = f"tests/{f.name}"
        if not a.only and rel in owned:
            continue
        try:
            st, detail = run_one(f, a.timeout, log_dir=a.log_dir)
        except subprocess.TimeoutExpired:
            st, detail = "FAIL", f"timeout >{a.timeout}s"
        results.append({"suite": rel, "status": st, "detail": detail})

    counts = {}
    for x in results:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    if not a.quiet:
        for x in results:
            print(f"  [{x['status']:4}] {x['suite']:<44} {x['detail'][:80]}")
        print(f"[lsu_test_runner] suites={len(results)} "
              + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        if counts.get("ENV"):
            print(f"[lsu_test_runner] DISCLOSURE: {counts['ENV']} 个套件因环境"
                  f"（缺二进制/资产）无法判定 —— 不计入 PASS。")
        if a.log_dir:
            print(f"[lsu_test_runner] 逐套件完整证据（stdout/stderr/meta.json）→ "
                  f"{a.log_dir}（仅诊断，判定口径未改）")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"suites": results, "counts": counts}, ensure_ascii=False, indent=1))
    return 1 if counts.get("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
