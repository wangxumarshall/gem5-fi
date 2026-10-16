# tools/o3_atlas/tests/test_lsp_query.py
from tools.o3_atlas.lsp_query import ClangdClient, to_lsp_pos


class FakeClangd(ClangdClient):
    """不启动真进程：拦截 JSON-RPC 帧收发，只测协议层逻辑。"""

    def __init__(self, replies):
        self.replies, self.sent, self._id = list(replies), [], 0

    def _send(self, obj):
        self.sent.append(obj)

    def _read(self):
        return self.replies.pop(0)


def _reply(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def test_definition_skips_notifications_and_matches_id():
    c = FakeClangd([
        {"jsonrpc": "2.0", "method": "window/logMessage", "params": {"message": "hi"}},
        _reply(1, [{"uri": "file:///x/fetch.cc",
                    "range": {"start": {"line": 1058, "character": 11}}}]),
    ])
    assert c.definition("/x/fetch.cc", 1059, 12) == [
        {"uri": "file:///x/fetch.cc",
         "range": {"start": {"line": 1058, "character": 11}}}]
    assert c.sent[0]["method"] == "textDocument/definition"


def test_position_conversion_1based_to_lsp():
    assert to_lsp_pos(1059, 12) == {"line": 1058, "character": 11}


# ---- fixup_compile_db：仓库迁移后 compile_commands 绝对路径失效的重写器 ----

def test_fixup_rewrites_stale_directory_and_command_prefix(tmp_path):
    import json
    from pathlib import Path

    from tools.o3_atlas.lsp_query import fixup_compile_db

    repo = tmp_path / "repo"
    (repo / "gem5").mkdir(parents=True)
    stale_root = tmp_path / "oldroot"            # 不存在：仓库被移动走的旧根
    old_dir = stale_root / "gem5"
    db = tmp_path / "cc.json"
    db.write_text(json.dumps([
        {"directory": str(old_dir), "file": "src/x.cc",
         "command": f"g++ -I{old_dir}/src -c src/x.cc"}]))
    fixed = fixup_compile_db(db, repo)
    entries = json.loads(Path(fixed).read_text())
    assert entries[0]["directory"] == str(repo / "gem5")
    assert f"-I{repo}/gem5/src" in entries[0]["command"]
    assert str(stale_root) not in entries[0]["command"]


def test_fixup_prefix_guard_no_partial_match(tmp_path):
    import json
    from pathlib import Path

    from tools.o3_atlas.lsp_query import fixup_compile_db

    repo = tmp_path / "repo"
    (repo / "gem5").mkdir(parents=True)
    stale_root = tmp_path / "oldroot"
    db = tmp_path / "cc.json"
    db.write_text(json.dumps([
        {"directory": str(stale_root / "gem5"), "file": "src/x.cc",
         "command": f"g++ -I{stale_root}-ding/keep -c src/x.cc"}]))
    fixed = fixup_compile_db(db, repo)
    entries = json.loads(Path(fixed).read_text())
    # 前缀守卫：oldroot-ding 不被误改写（"oldroot" 后跟 '-'，非边界）
    assert f"-I{stale_root}-ding/keep" in entries[0]["command"]


def test_fixup_noop_when_directory_exists(tmp_path):
    import json
    from pathlib import Path

    from tools.o3_atlas.lsp_query import fixup_compile_db

    live = tmp_path / "live"
    live.mkdir()
    db = tmp_path / "cc.json"
    db.write_text(json.dumps([{"directory": str(live), "file": "src/x.cc",
                               "command": "g++ -c src/x.cc"}]))
    fixed = fixup_compile_db(db, tmp_path / "repo")
    assert Path(fixed) == db  # 无需重写：原样返回原 DB 路径
