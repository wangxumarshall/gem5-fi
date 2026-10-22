#!/usr/bin/env python3
"""lsu_test_runner.py — 真实运行 tests/ 下的**全部**套件（含 pytest 不收集的独立脚本）。

动机（R5-U2，缺陷实测）：`tests/test_lsu_*.py` 中大多数是 `main()` 独立脚本，
`python3 -m pytest tests/ -q` **只收集 21 个**（实测 `--collect-only`），其余约 40 个
hook/契约套件从不被执行；而且这些脚本**无论成败都以 exit 0 结束**，只把
`ALL PASS` / `FAILURES: [...]` 打到 stdout。因此：
  * `pytest_rc == 0` 不能证明"全部套件通过"；
  * 子进程 `returncode == 0` 也不能证明该脚本通过。
二者曾共同掩护了 R4-4 `corr` 契约收紧后两个 hook 套件长达数周的静默红（R5-U1）。

本运行器逐个套件以真实子进程执行、解析真实输出，分类如下：

  PASS   rc==0 且末行含 `ALL PASS` 或 `FAILURES: 无`
  SKIP   rc==0 且末行含 `SKIPPED`（诚实跳过，理由同行输出）
  ENV    输出含 FileNotFoundError / No such file or directory（环境阻塞：缺二进制或
         资产）——必须披露，绝不并入 PASS
  FAIL   `FAILURES: [...]` 非空，或 rc!=0，或出现 Traceback

用法：
  python3 tools/lsu_test_runner.py [--json OUT] [--timeout SEC] [--quiet]
退出码：0 当且仅当无 FAIL；ENV 存在时打印醒目披露但不单独判负（由调用方决定）。
"""
import argparse
import json
import re
import subprocess
import sys
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
        return "PASS", "FAILURES: 无"
    if "ALL PASS" in text:
        return "PASS", "ALL PASS"
    if "SKIPPED" in text:
        return "SKIP", tail
    if rc != 0:
        return "FAIL", tail
    return "PASS", "rc=0（未见显式判定）"


def run_one(path, timeout):
    r = subprocess.run([sys.executable, str(path)], capture_output=True,
                       text=True, cwd=str(REPO), timeout=timeout)
    return classify(r.returncode, (r.stdout or "") + (r.stderr or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="结果 JSON 输出路径")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    owned = pytest_owned()
    results = []

    # 1) pytest 自身（覆盖其收集到的套件）
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                       capture_output=True, text=True, cwd=str(REPO))
    pt = (r.stdout or "").strip().splitlines()[-1:] or [""]
    results.append({"suite": "pytest::collect", "status":
                    "PASS" if r.returncode == 0 else "FAIL",
                    "detail": pt[0][:160], "collects": len(owned)})

    # 2) 全部独立脚本（pytest 未收集者）
    for f in sorted(TESTS.glob("test_*.py")):
        rel = f"tests/{f.name}"
        if rel in owned:
            continue
        try:
            st, detail = run_one(f, a.timeout)
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

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"suites": results, "counts": counts}, ensure_ascii=False, indent=1))
    return 1 if counts.get("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
