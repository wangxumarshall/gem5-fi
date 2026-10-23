#!/usr/bin/env python3
"""test_lsu_campaign_propagation.py — [MDSPEC][H0] campaign 全量传播接入契约。

用户指令（2026-10-20 第二轮）：CHAOSPropagation 必须由**正式 campaign 入口**
对每个样本自动挂载并传递 run_id/sample_run_id（此前只有手工直驱 lsu_proxy
才有 PROP-EVT 流，正式入口产不出传播证据）。

钉死三件事：
  1. 每样本命令行含 --chaos_propagation / --prop_run_id <RunID> /
     --prop_sample_run_id s<seed>（SE 与 FS 两支）；
  2. 二进制解析遵 LSU_GEM5_BIN → repo-root build/ARM/gem5.opt，二者皆缺
     **响亮 SystemExit**（不得静默跑错/跑空二进制）；
  3. 端到端：run_single_cell 实际组装的命令里带齐上述三项（不是"函数存在
     但没被调用"）。

用法：python3 tests/test_lsu_campaign_propagation.py   （退出码 0=全 PASS）
"""
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _cell(runid, model, unit, freq, workload):
    row = [""] * 12
    row[LC.COL_RUNID] = runid
    row[LC.COL_MODEL] = model
    row[LC.COL_UNIT] = unit
    row[LC.COL_FREQ] = freq
    row[LC.COL_WORKLOAD] = workload
    return row


def main():
    print("[1] propagation_flags 形状")
    f = LC.propagation_flags("A01-F0-W3", 3)
    check("flags 完整", f == ["--chaos_propagation", "--prop_run_id",
                              "A01-F0-W3", "--prop_sample_run_id", "s3"],
          str(f))

    print("[2] 二进制解析（LSU_GEM5_BIN 优先 + 缺则响亮失败）")
    real = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
    if real.exists():
        got = LC.resolve_g5({"LSU_GEM5_BIN": str(real)})
        check("env 覆盖生效", got == real, str(got))
    try:
        LC.resolve_g5({"LSU_GEM5_BIN": "/nonexistent/gem5.opt"})
        check("缺二进制必须 SystemExit", False, "没抛异常")
    except SystemExit:
        check("缺二进制必须 SystemExit", True)
    # worktree 里 repo-root build/ 不存在 → 默认路径也必须响亮失败
    if not (ROOT / "build/ARM/gem5.opt").exists():
        try:
            LC.resolve_g5({})
            check("默认路径缺失也 SystemExit", False, "没抛异常")
        except SystemExit:
            check("默认路径缺失也 SystemExit", True)

    print("[3] 端到端：run_single_cell 组装的命令带齐传播标志")
    if not real.exists():
        check("端到端（需已构建二进制）", False, "未找到 " + str(real))
    else:
        import os
        os.environ["LSU_GEM5_BIN"] = str(real)
        captured = {}

        # [LSU][R6-CAMPAIGN] run_single_cell now drives gem5 through
        # LC.run_gem5 (Popen-based, so a timeout can be killed + reaped); fake
        # Popen captures the assembled command and returns cleanly.
        class FakePopen:
            def __init__(self, cmd, **kw):
                captured["cmd"] = cmd
                self.pid = 4242
                self.returncode = None

            def communicate(self, timeout=None):
                self.returncode = 0
                return ("FINAL 728e604ffcec539d\n", "")

            def wait(self):
                self.returncode = 0
                return 0

        orig = LC.subprocess.Popen
        LC.subprocess.Popen = FakePopen
        orig_classify = LC.classify_run
        LC.classify_run = lambda *a, **k: {"outcome": "Masked",
                                          "activated": 1, "classes": {}}
        try:
            args = types.SimpleNamespace(
                phase="trial", timeout=60, fs_checkpoint=None,
                fs_timeout=60)
            cell = _cell("A01-F0-W3", "A01", "AGU", "F0",
                         "AGU-AddrModes AArch64 寻址模式探针")
            out = ROOT / "runs/lsu/_test_prop_assembly/seed1"
            LC.run_single_cell(cell, args, 7, out)
        finally:
            LC.subprocess.Popen = orig
            LC.classify_run = orig_classify
            os.environ.pop("LSU_GEM5_BIN", None)

        cmd = captured.get("cmd")
        check("命令已组装", cmd is not None, "subprocess.run 未被调用")
        if cmd:
            check("含 --chaos_propagation", "--chaos_propagation" in cmd,
                  str(cmd))
            i = cmd.index("--prop_run_id") if "--prop_run_id" in cmd else -1
            check("--prop_run_id = RunID",
                  i >= 0 and cmd[i + 1] == "A01-F0-W3", str(cmd))
            j = (cmd.index("--prop_sample_run_id")
                 if "--prop_sample_run_id" in cmd else -1)
            check("--prop_sample_run_id = s<seed>",
                  j >= 0 and cmd[j + 1] == "s7", str(cmd))
            check("二进制取自 LSU_GEM5_BIN", str(real) in cmd, str(cmd[:2]))

    print("[4] FS 路径：armtlb 单元的命令构造同样带传播标志")
    if not real.exists():
        check("FS 命令构造（需已构建二进制）", False, "未找到 " + str(real))
    else:
        import os
        os.environ["LSU_GEM5_BIN"] = str(real)
        captured = {}

        class FakePopenFS:
            def __init__(self, cmd, **kw):
                captured["cmd"] = cmd
                self.pid = 4343
                self.returncode = None

            def communicate(self, timeout=None):
                self.returncode = 0
                return ("", "")

            def wait(self):
                self.returncode = 0
                return 0

        orig = LC.subprocess.Popen
        LC.subprocess.Popen = FakePopenFS
        # asset guard is exercised by the real FS smoke; here we only assert
        # the command shape (the worktree has no gem5-fs submodule).
        orig_assets = LC.require_fs_assets
        LC.require_fs_assets = lambda: None
        orig_fs = LC.classify_fs_run
        LC.classify_fs_run = lambda *a, **k: {"outcome": "Timeout",
                                             "injected": 0, "activated": 0}
        try:
            args = types.SimpleNamespace(
                phase="trial", timeout=60, fs_checkpoint="/tmp/fake_cpt",
                fs_timeout=60)
            cell = _cell("T01-F0-W4", "T01", "L1d-TLB", "F0",
                         "TLB-AliasPerm 地址翻译探针")
            out = ROOT / "runs/lsu/_test_prop_assembly_fs/seed1"
            LC.run_single_cell(cell, args, 5, out)
        finally:
            LC.subprocess.Popen = orig
            LC.classify_fs_run = orig_fs
            LC.require_fs_assets = orig_assets
            os.environ.pop("LSU_GEM5_BIN", None)
        cmd = captured.get("cmd") or []
        check("FS 命令已组装", bool(cmd), "subprocess.run 未被调用")
        check("FS 命令用 fs 配置", any("fs" in str(c) for c in cmd[:4]), str(cmd[:3]))
        check("FS 含 --chaos_propagation", "--chaos_propagation" in cmd, str(cmd))
        i = cmd.index("--prop_run_id") if "--prop_run_id" in cmd else -1
        check("FS --prop_run_id = RunID",
              i >= 0 and cmd[i + 1] == "T01-F0-W4", str(cmd))
        j = (cmd.index("--prop_sample_run_id")
             if "--prop_sample_run_id" in cmd else -1)
        check("FS --prop_sample_run_id = s<seed>",
              j >= 0 and cmd[j + 1] == "s5", str(cmd))

    print("[5] chain_report：oracle join + truncated 保留（含无 chain_end）")
    import gzip
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # 一条真实形状的流：tlb_fault(contained 空) + 无 chain_end（中止样本）
        body = (
            "# prop-evt v1: header\n"
            "PROP-EVT: kind=inj run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=0 tick=10\n"
            "PROP-EVT: kind=addr_form run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=1 tick=10\n"
            "PROP-EVT: kind=tlb_fault run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=2 tick=13 detection_layer=Hardware contained= "
            "outcome=GenericPageTableFault\n"
        )
        # A well-formed gz is NOT truncated; the abort shape is a stream
        # that was Z_SYNC_FLUSH-ed but never finished (no trailer). Build
        # exactly that, or the assertion tests nothing.
        import zlib
        co = zlib.compressobj(9, zlib.DEFLATED, 16 + 15)   # gzip wrapper
        (d / "prop_evt.txt.gz").write_bytes(
            co.compress(body.encode()) + co.flush(zlib.Z_SYNC_FLUSH))
        rep = LC.write_chain_report(d, "A01-F0-W3", 1,
                                    {"outcome": "Crash"}, exit_code=134)
        check("stream_present", rep["stream_present"] is True, str(rep))
        check("事件前缀被保留（无 chain_end 也计入）", rep["event_count"] == 3,
              str(rep["event_count"]))
        check("truncated 标记（gz 无 trailer）", rep["truncated"] is True,
              str(rep["truncated"]))
        check("oracle join → crash_translation_blocked",
              rep["terminal"] == "crash_translation_blocked", str(rep["terminal"]))
        check("provable_to / beyond 一致",
              rep["provable_to"] == "L2" and rep["beyond"] == "",
              f'{rep["provable_to"]} / {rep["beyond"]!r}')
        check("chain_report.json 落盘",
              (d / "chain_report.json").exists(), "文件不存在")
        # 无流：诚实记录 absent，不伪造判定
        rep2 = LC.write_chain_report(d / "non", "X-F0-W1", 2,
                                     {"outcome": "Masked"})
        check("无流 → stream_present=False 且无 terminal",
              rep2["stream_present"] is False and rep2["terminal"] is None,
              str(rep2))

    print("[6] [R6-FIXA] 请求域父边：同请求通过 / 跨请求拒绝 / T02-T04 真实形状")
    # 发射器（CHAOSPropagation::emitPropEvt）此前用单一 ptag 游标作
    # parent_event_id，使 addr_fallback 广播（一条被污染 line/PA 被多请求读到）
    # 直接挂成跨请求父子边——T04-F0-W4 实测 59 处断裂（首例 event 12
    # mshr_alloc req=31 → event 13 cache_access req=32）。修复把链变成
    # per-(fault, request)：非本请求的事件是**兄弟子链**（各自在自身请求首现处
    # 生根），不再成为跨请求父边。检查器门禁一字未改——这里用真实流形状钉死。
    import lsu_chain_check as CC  # noqa: E402（tools/ 已在 sys.path）
    import lsu_prop_fields as PF  # noqa: E402
    RUN = "T04-F0-W4"

    def _L(kind, **kw):
        parts = [f"kind={kind}", f"run_id={RUN}"]
        parts += [f"{k}={v}" for k, v in kw.items()]
        return PF.parse_line("PROP-EVT: " + " ".join(parts))

    # 真实 T04/T02 流形状：owner 请求 31 的 L0→L2（inj/tlb_lookup/tlb_pfn/
    # tlb_translate_result）+ 未盖戳生命周期（lsq_push）+ L3（cache_access/
    # mshr_alloc）+ 一个**兄弟**请求 32 的 cache_access/cache_return（自身生根，
    # 无跨请求父边）+ owner 的 resp/taint_reg + errant_commit（未盖戳，随 owner）。
    owner = [
        _L("inj", fault_id=1, event_id=0, tick=10, request_id=31,
           corr="origin"),
        _L("tlb_lookup", fault_id=1, event_id=1, parent_event_id=0, tick=11,
           request_id=31, corr="seq_primary", dyn_inst_seq=31,
           field="post_lookup", state_before="valid", state_after="valid"),
        _L("tlb_pfn", fault_id=1, event_id=2, parent_event_id=1, tick=12,
           request_id=31, corr="seq_primary", va="7f000", before="1000",
           after="2000"),
        _L("tlb_translate_result", fault_id=1, event_id=3, parent_event_id=2,
           tick=13, request_id=31, corr="seq_primary", outcome="NoFault",
           contained="0"),
        _L("lsq_push", fault_id=1, event_id=4, parent_event_id=3, tick=14,
           corr="seq_primary"),
        _L("cache_access", fault_id=1, event_id=5, parent_event_id=4, tick=15,
           request_id=31, corr="addr_fallback"),
        _L("mshr_alloc", fault_id=1, event_id=6, parent_event_id=5, tick=16,
           request_id=31, corr="addr_fallback"),
    ]
    # 兄弟子链（请求 32）：NO parent_event_id —— 自身生根，**不得**指向
    # 请求 31 的任何事件。
    sibling = [
        _L("cache_access", fault_id=1, event_id=7, tick=17, request_id=32,
           corr="addr_fallback"),
        _L("cache_return", fault_id=1, event_id=8, parent_event_id=7, tick=18,
           request_id=32, corr="addr_fallback"),
    ]
    owner_tail = [
        _L("resp", fault_id=1, event_id=9, parent_event_id=6, tick=19,
           request_id=31, corr="seq_primary"),
        _L("taint_reg", fault_id=1, event_id=10, parent_event_id=9, tick=20,
           request_id=31, corr="seq_primary"),
        _L("errant_commit", fault_id=1, event_id=11, parent_event_id=10,
           tick=21, corr="taint_prop", detection_layer="L5", contained="0",
           outcome="errant_commit"),
        _L("chain_end", fault_id=1, event_id=12, parent_event_id=11, tick=22,
           corr="none", detection_layer="L5", contained="0",
           outcome="errant_commit_seen"),
    ]

    # (1) 同一请求的合法边通过：纯 owner 链（无兄弟）→ 门禁 PASS。
    r1 = CC.check_admission({"run_id": RUN, "activated": 1,
                             "events": owner + owner_tail,
                             "oracle_outcome": "SDC"})
    check("同请求链 admitted + full_chain",
          r1["admitted"] is True and r1["path"] == "full_chain",
          f'{r1["admitted"]} / {r1["path"]}')
    check("同请求链无 cross_request_edge",
          not any("cross_request_edge" in v for v in r1["violations"]),
          str(r1["violations"]))

    # (2) 跨请求边仍被拒绝（门禁未被放宽）：修复前的**单游标**形状——请求 32
    #     的事件直接挂在请求 31 的事件 6 之下，owner tail 再续在 32 之后，
    #     使跨请求边落在所选祖先上（复现实测的 59 处断裂形状）。
    linear = ([L2 for L2 in owner]
              + [_L("cache_access", fault_id=1, event_id=7, parent_event_id=6,
                    tick=17, request_id=32, corr="addr_fallback"),
                 _L("cache_return", fault_id=1, event_id=8, parent_event_id=7,
                    tick=18, request_id=32, corr="addr_fallback"),
                 _L("resp", fault_id=1, event_id=9, parent_event_id=8, tick=19,
                    request_id=31, corr="seq_primary"),
                 _L("taint_reg", fault_id=1, event_id=10, parent_event_id=9,
                    tick=20, request_id=31, corr="seq_primary"),
                 _L("errant_commit", fault_id=1, event_id=11,
                    parent_event_id=10, tick=21, corr="taint_prop",
                    detection_layer="L5", contained="0",
                    outcome="errant_commit"),
                 _L("chain_end", fault_id=1, event_id=12, parent_event_id=11,
                    tick=22, corr="none", detection_layer="L5", contained="0",
                    outcome="errant_commit_seen")])
    r2 = CC.check_admission({"run_id": RUN, "activated": 1, "events": linear,
                             "oracle_outcome": "SDC"})
    check("跨请求父边仍被拒绝",
          r2["admitted"] is False
          and any("cross_request_edge" in v for v in r2["violations"]),
          str(r2["violations"][:1]))

    # (3) T02/T04 真实 L0–L5 链保持 request 一致：加兄弟子链后仍 admitted，
    #     且兄弟事件**不在**所选祖先上（未被拼接进 owner 链）。
    r3 = CC.check_admission({"run_id": RUN, "activated": 1,
                             "events": owner + sibling + owner_tail,
                             "oracle_outcome": "SDC"})
    check("真实形状仍 admitted + L0..L5 全层",
          r3["admitted"] is True
          and r3["path_layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"],
          f'{r3["admitted"]} / {r3["path_layers"]}')
    check("真实形状无 cross_request_edge",
          not any("cross_request_edge" in v for v in r3["violations"]),
          str(r3["violations"]))
    by_id = {e["event_id"]: e for e in owner + sibling + owner_tail}
    anc = CC._ancestry(by_id["12"], by_id)
    anc_ids = [e["event_id"] for e in anc]
    check("兄弟请求 32 的事件不在所选祖先上",
          "7" not in anc_ids and "8" not in anc_ids, str(anc_ids))
    check("所选祖先全部为 owner(31) 或未盖戳（request 一致）",
          all(str(e.get("request_id", "")).strip() in ("", "0", "31")
              for e in anc), str([e.get("request_id") for e in anc]))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
