# tools/o3_atlas/lsp_query.py
"""clangd JSON-RPC client for precise anchor discovery (def/ref/hover).

Scope note: compile_commands.json covers C++ TU under CHAOS/gem5/src; the
.isa DSL and generated .inc files are NOT compilation units — read those
directly and verify anchors with validate.py instead.

Usage:
    python3 -m tools.o3_atlas.lsp_query def CHAOS/gem5/src/cpu/o3/fetch.cc:1059:16
    python3 -m tools.o3_atlas.lsp_query ref CHAOS/gem5/src/cpu/o3/rob.cc:194:26
First run builds clangd's background index for ~31k TU — slow is normal.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .corpus import REPO


def fixup_compile_db(db_path, repo_root):
    """Rewrite stale absolute roots in a compile_commands.json (repo moved).

    Every entry's 'directory' may point at the pre-move location (e.g.
    /home/sdc/gem5-fi/... vs the current /home/sdc/gem5-fi-ding/...), which
    makes clangd fall back to flag-less parsing and answer nonsense. For each
    stale directory, re-root its tail (the part below the first non-existent
    ancestor) at repo_root; guard-replace the same stale-root prefix inside
    command/arguments strings. Returns the path to a usable DB: the original
    if untouched, else <db_dir>/.clangd-fixed/compile_commands.json.
    """
    db_path = Path(db_path)
    entries = json.loads(db_path.read_text())
    fixed_dir = db_path.parent / ".clangd-fixed"
    fixed = fixed_dir / "compile_commands.json"
    if fixed.is_file() and fixed.stat().st_mtime >= db_path.stat().st_mtime:
        return fixed  # 缓存命中：原始 DB 未变
    changed = False
    for e in entries:
        d = Path(e.get("directory", ""))
        if d.is_dir():
            continue
        parts = d.parts
        stale_root = None
        for i in range(len(parts), 0, -1):  # 最长存在前缀 → 其下一级即失效根
            if Path(*parts[:i]).is_dir():
                stale_root = Path(*parts[:i + 1])
                tail = Path(*parts[i + 1:])
                break
        if stale_root is None:
            continue
        new_dir = Path(repo_root) / tail
        if not new_dir.is_dir():
            raise RuntimeError(
                f"compile DB directory {d} is stale and re-rooting to "
                f"{new_dir} does not exist; rebuild compile_commands.json")
        e["directory"] = str(new_dir)
        # 尾部 "/" 即边界守卫：oldroot-ding 不会匹配 oldroot/，无需额外前瞻
        old_prefix, new_prefix = str(stale_root) + "/", str(repo_root) + "/"
        pat = re.compile(re.escape(old_prefix))
        if isinstance(e.get("command"), str):
            e["command"] = pat.sub(new_prefix, e["command"])
        if isinstance(e.get("arguments"), list):
            e["arguments"] = [pat.sub(new_prefix, a) if isinstance(a, str) else a
                              for a in e["arguments"]]
        changed = True
    if not changed:
        return db_path
    fixed_dir.mkdir(exist_ok=True)
    fixed.write_text(json.dumps(entries))
    return fixed


class ClangdClient:
    def __init__(self, ccd, clangd_bin=os.path.expanduser("~/.local/bin/clangd")):
        self.proc = subprocess.Popen(
            [clangd_bin, f"--compile-commands-dir={ccd}", "--background-index",
             "--pch-storage=memory", "--limit-references=100"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)

    def _send(self, obj):
        data = json.dumps(obj).encode()
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
        self.proc.stdin.flush()

    def _read(self):
        headers = {}
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise EOFError("clangd closed")
            if line in (b"\r\n", b"\n"):
                break
            k, _, v = line.decode().partition(":")
            headers[k.strip().lower()] = v.strip()
        return json.loads(self.proc.stdout.read(int(headers["content-length"])))

    def request(self, method, params):
        self._id = getattr(self, "_id", 0) + 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while True:
            msg = self._read()  # 跳过 server 通知，只认同 id 应答
            if msg.get("id") == rid:
                return msg.get("result")

    def notify(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def initialize(self, root):
        self.request("initialize", {"processId": os.getpid(),
                                    "rootUri": "file://" + str(root),
                                    "capabilities": {}})
        self.notify("initialized", {})

    def open(self, path):
        text = open(path, encoding="utf-8", errors="replace").read()
        self.notify("textDocument/didOpen", {"textDocument": {
            "uri": "file://" + str(path), "languageId": "cpp", "version": 1,
            "text": text}})

    def definition(self, path, line, col):
        return self.request("textDocument/definition", {
            "textDocument": {"uri": "file://" + str(path)},
            "position": to_lsp_pos(line, col)})


def to_lsp_pos(line_1b, col_1b):
    return {"line": line_1b - 1, "character": col_1b - 1}


def _fmt(locs):
    """Location 与 LocationLink 两种形态都归一化为 {file,line,col}。"""
    out = []
    for l in (locs if isinstance(locs, list) else [locs]):
        if not l:
            continue
        uri = l.get("uri") or l.get("targetUri")
        rng = l.get("range") or l.get("targetSelectionRange")
        if uri and rng:
            out.append({"file": uri.removeprefix("file://"),
                        "line": rng["start"]["line"] + 1,
                        "col": rng["start"]["character"] + 1})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["def", "ref", "hover"])
    ap.add_argument("loc", help="FILE:LINE:COL (1-based)")
    ap.add_argument("--ccd", default=str(REPO / "build/ARM"))
    args = ap.parse_args()
    path, line, col = args.loc.rsplit(":", 2)
    path = os.path.abspath(path)
    usable_db = fixup_compile_db(Path(args.ccd) / "compile_commands.json", REPO)
    c = ClangdClient(str(Path(usable_db).parent))
    c.initialize(REPO)
    c.open(path)
    method = {"def": "textDocument/definition",
              "ref": "textDocument/references",
              "hover": "textDocument/hover"}[args.cmd]
    res = c.request(method, {"textDocument": {"uri": "file://" + path},
                             "position": to_lsp_pos(int(line), int(col)),
                             "context": {"includeDeclaration": True}})
    json.dump({"query": args.loc, "results": res if args.cmd == "hover"
               else _fmt(res)}, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
