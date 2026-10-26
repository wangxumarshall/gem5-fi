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

    print("[6] [R6-FIXA2] 显式 lineage bridge（request_fork）：跨 request 边"
          "仅在完整、可核验的 bridge 上放行")
    # 上一版把后续请求做成**无父生根的兄弟子链**，被用户裁决否决（把真实跨
    # request 污染传播排除在因果图之外）。本版：同一污染对象首次传播到新的
    # request_id 时发射显式 bridge，把新请求首事件接到**真实污染来源事件**上；
    # 无来源/无共享对象时**不造桥**；门禁只对完整可核验 bridge 放行。
    import lsu_chain_check as CC  # noqa: E402（tools/ 已在 sys.path）
    import lsu_prop_fields as PF  # noqa: E402
    RUN = "T04-F0-W4"          # T 族 → cache_access 观察层 L3

    def _L(kind, **kw):
        parts = [f"kind={kind}", f"run_id={RUN}"]
        parts += [f"{k}={v}" for k, v in kw.items()]
        return PF.parse_line("PROP-EVT: " + " ".join(parts))

    def _adm(events, oracle="SDC"):
        return CC.check_admission({"run_id": RUN, "activated": 1,
                                   "events": events,
                                   "oracle_outcome": oracle})

    def _anc_of(events, last):
        by_id = {e["event_id"]: e for e in events}
        return [e["event_id"] for e in CC._ancestry(by_id[last], by_id)]

    # 共享污染对象 = 已登记的坏物理页 [0x0, 0x1000)（T04 pfn→异帧 实测）。
    # owner 请求 301 的 L0→L3 前缀 + 未盖戳生命周期。
    owner = [
        _L("inj", fault_id=1, event_id=0, tick=10, request_id=301,
           va="ffffffc009483fa8", corr="origin"),
        _L("tlb_lookup", fault_id=1, event_id=1, parent_event_id=0, tick=11,
           request_id=301, corr="seq_primary", dyn_inst_seq=301,
           field="post_lookup", state_before="valid", state_after="valid"),
        _L("tlb_pfn", fault_id=1, event_id=2, parent_event_id=1, tick=12,
           request_id=301, corr="seq_primary", va="ffffffc009483fa8",
           before="81d75", after="0", pa="fa8"),
        _L("tlb_translate_result", fault_id=1, event_id=3, parent_event_id=2,
           tick=13, request_id=301, corr="seq_primary", outcome="NoFault",
           contained="0"),
        _L("lsq_push", fault_id=1, event_id=4, parent_event_id=3, tick=14,
           corr="seq_primary"),
        _L("cache_access", fault_id=1, event_id=5, parent_event_id=4, tick=15,
           request_id=301, corr="addr_fallback", pa="fa8",
           va="ffffffc009483fa8"),
        _L("mshr_alloc", fault_id=1, event_id=6, parent_event_id=5, tick=16,
           request_id=301, corr="addr_fallback", cache_line="fa8"),
    ]

    def _bridge(event_id, parent, old, new, src_ev, dst_ev, tick,
                layer="L3", reason="addr_fallback_broadcast", addr="0",
                size="1000", corr="addr_fallback"):
        return _L("request_fork", fault_id=1, event_id=event_id,
                  parent_event_id=parent, tick=tick, request_id=old,
                  corr=corr, old_request_id=old, new_request_id=new,
                  source_event_id=src_ev, dest_event_id=dst_ev,
                  bridge_layer=layer, bridge_reason=reason,
                  shared_addr=addr, shared_size=size)

    # 请求 B(303) 的首事件经 bridge(7) 挂在来源事件 6（owner 请求 301）之下，
    # 且 B 自己的链走到 L4/L5 —— 用户要求：L5 发生在新请求时，所选完整路径
    # 必须真实包含 L0…源请求…bridge…目标请求…L5。
    def _branch_b(base_tick, req=303, first_id=8, pa="fe0",
                  va="ffffffc009483fe0"):
        return [
            _L("cache_access", fault_id=1, event_id=first_id,
               parent_event_id=7, tick=base_tick, request_id=req,
               corr="addr_fallback", pa=pa, va=va),
            _L("resp", fault_id=1, event_id=first_id + 1,
               parent_event_id=first_id, tick=base_tick + 1, request_id=req,
               corr="addr_fallback", pa=pa, va=va),
            _L("taint_reg", fault_id=1, event_id=first_id + 2,
               parent_event_id=first_id + 1, tick=base_tick + 2,
               request_id=req, corr="addr_fallback"),
            _L("errant_commit", fault_id=1, event_id=first_id + 3,
               parent_event_id=first_id + 2, tick=base_tick + 3,
               request_id=req, corr="addr_fallback",
               detection_layer="L5", contained="0", outcome="errant_commit"),
            _L("chain_end", fault_id=1, event_id=first_id + 4,
               parent_event_id=first_id + 3, tick=base_tick + 4, corr="none",
               detection_layer="L5", contained="0",
               outcome="errant_commit_seen"),
        ]

    tail_owner = [
        _L("resp", fault_id=1, event_id=20, parent_event_id=6, tick=19,
           request_id=301, corr="seq_primary"),
        _L("taint_reg", fault_id=1, event_id=21, parent_event_id=20, tick=20,
           request_id=301, corr="seq_primary"),
        _L("errant_commit", fault_id=1, event_id=22, parent_event_id=21,
           tick=21, corr="taint_prop", detection_layer="L5", contained="0",
           outcome="errant_commit"),
        _L("chain_end", fault_id=1, event_id=23, parent_event_id=22, tick=22,
           corr="none", detection_layer="L5", contained="0",
           outcome="errant_commit_seen"),
    ]
    # 完整合法形状：owner L0–L3 + bridge(7) → B(303) L3–L5。
    bridged = owner + [_bridge(7, 6, 301, 303, 6, 8, 17)] + _branch_b(18)

    # (1) 同一请求的合法父边通过（无 bridge 参与）。
    r1 = _adm(owner + tail_owner)
    check("(1) 同请求链 admitted + full_chain",
          r1["admitted"] is True and r1["path"] == "full_chain",
          f'{r1["admitted"]} / {r1["path"]}')
    check("(1) 同请求链无 cross_request_edge",
          not any("cross_request_edge" in v for v in r1["violations"]),
          str(r1["violations"]))

    # (2) 没有 bridge 的跨 request 边**仍然拒绝**（门禁未放宽）：请求 303 的
    #     事件直接挂在 301 的事件 6 之下（实测 59 处断裂的单游标形状）。
    unbridged = ([e for e in owner]
                 + [_L("cache_access", fault_id=1, event_id=8,
                       parent_event_id=6, tick=17, request_id=303,
                       corr="addr_fallback", pa="fe0",
                       va="ffffffc009483fe0"),
                    _L("resp", fault_id=1, event_id=9, parent_event_id=8,
                       tick=18, request_id=303, corr="addr_fallback",
                       pa="fe0", va="ffffffc009483fe0"),
                    _L("taint_reg", fault_id=1, event_id=10,
                       parent_event_id=9, tick=19, request_id=303,
                       corr="addr_fallback"),
                    _L("errant_commit", fault_id=1, event_id=11,
                       parent_event_id=10, tick=20, request_id=303,
                       corr="addr_fallback", detection_layer="L5",
                       contained="0", outcome="errant_commit"),
                    _L("chain_end", fault_id=1, event_id=12,
                       parent_event_id=11, tick=21, corr="none",
                       detection_layer="L5", contained="0",
                       outcome="errant_commit_seen")])
    r2 = _adm(unbridged)
    check("(2) 无 bridge 的跨请求父边仍被拒绝",
          r2["admitted"] is False
          and any("cross_request_edge" in v for v in r2["violations"]),
          str(r2["violations"][:1]))

    # (3) 假 bridge 三种一律拒绝：字段缺失 / 来源事件不存在 / 地址不一致。
    fake_missing = _bridge(7, 6, 301, 303, 6, 8, 17)
    fake_missing["shared_size"] = ""
    fake_missing["bridge_layer"] = ""
    r3a = _adm(owner + [fake_missing] + _branch_b(18))
    check("(3a) 字段缺失的假 bridge 被拒绝",
          r3a["admitted"] is False
          and any("invalid_lineage_bridge" in v for v in r3a["violations"]),
          str(r3a["violations"][:1]))
    r3b = _adm(owner + [_bridge(7, 6, 301, 303, 9999, 8, 17)]
               + _branch_b(18))
    check("(3b) 来源事件不存在的假 bridge 被拒绝",
          r3b["admitted"] is False
          and any("invalid_lineage_bridge" in v for v in r3b["violations"]),
          str(r3b["violations"][:1]))
    r3c = _adm(owner + [_bridge(7, 6, 301, 303, 6, 8, 17,
                                addr="ff000000", size="1000")]
               + _branch_b(18))
    check("(3c) 地址/line 不一致的假 bridge 被拒绝",
          r3c["admitted"] is False
          and any("invalid_lineage_bridge" in v for v in r3c["violations"]),
          str(r3c["violations"][:1]))

    # (4) 合法 A→bridge→B 进入**所选 ancestry**（不是被忽略的兄弟根）。
    r4 = _adm(bridged)
    anc4 = _anc_of(bridged, "12")
    check("(4) 合法 bridge 链 admitted + L0..L5 全层",
          r4["admitted"] is True
          and r4["path_layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"],
          f'{r4["admitted"]} / {r4["path_layers"]}')
    check("(4) bridge 与目标请求在所选祖先上（非兄弟根）",
          "7" in anc4 and "8" in anc4, str(anc4))
    check("(4) 无 cross_request_edge",
          not any("cross_request_edge" in v for v in r4["violations"]),
          str(r4["violations"]))
    by_id4 = {e["event_id"]: e for e in bridged}
    check("(4) bridge 的父边指向真实来源事件 6",
          by_id4["7"]["parent_event_id"] == "6"
          and by_id4["7"]["source_event_id"] == "6", str(by_id4["7"]))
    check("(4) 新请求首事件的父边指向 bridge",
          by_id4["8"]["parent_event_id"] == "7", str(by_id4["8"]))

    # (5) 多请求广播 = 一个来源向多个 request 分支显式 fork。
    fan = ([e for e in owner]
           + [_bridge(7, 6, 301, 303, 6, 8, 17),
              _bridge(24, 6, 301, 307, 6, 25, 17),
              _L("cache_access", fault_id=1, event_id=25, parent_event_id=24,
                 tick=17, request_id=307, corr="addr_fallback", pa="fb0",
                 va="ffffffc009483fb0"),
              _L("cache_return", fault_id=1, event_id=26,
                 parent_event_id=25, tick=18, request_id=307,
                 corr="addr_fallback", pa="fb0")]
           + _branch_b(18) + tail_owner)
    r5 = _adm(fan)
    br5 = sorted(e["event_id"] for e in fan
                 if e["kind"] == "request_fork")
    srcs5 = {e["source_event_id"] for e in fan if e["kind"] == "request_fork"}
    dsts5 = {e["new_request_id"] for e in fan if e["kind"] == "request_fork"}
    check("(5) 两个 request 分支各自显式 fork（同一来源事件）",
          br5 == ["24", "7"] and srcs5 == {"6"}
          and dsts5 == {"303", "307"}, f"{br5} {srcs5} {dsts5}")
    check("(5) 广播链仍 admitted（bridge 全合法）",
          r5["admitted"] is True
          and not any("invalid_lineage_bridge" in v for v in r5["violations"]),
          str(r5["violations"][:1]))

    # (6) L5 发生在新请求 B：所选完整路径真实含 L0…源请求…bridge…目标请求…L5。
    check("(6) L5 在新请求时完整路径含 bridge（L0→L5）",
          r4["path_layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"]
          and "7" in anc4 and "11" in anc4 and "12" in anc4,
          f'{r4["path_layers"]} anc={anc4}')
    check("(6) L5 见证（errant_commit 11）属于目标请求 303",
          by_id4["11"]["request_id"] == "303"
          and by_id4["11"]["detection_layer"] == "L5", str(by_id4["11"]))

    # (7) 单请求链行为保持不变：无 bridge 事件、admitted、祖先 request 一致。
    single = owner + tail_owner
    r7 = _adm(single)
    anc7 = _anc_of(single, "23")
    by_id7 = {e["event_id"]: e for e in single}
    check("(7) 单请求链无任何 bridge 事件",
          not any(e["kind"] == "request_fork" for e in single), "存在 bridge")
    check("(7) 单请求链 admitted + full_chain + 祖先 request 一致",
          r7["admitted"] is True and r7["path"] == "full_chain"
          and all(str(by_id7.get(i, {}).get("request_id", "")).strip()
                  in ("", "0", "301")
                  for i in anc7),
          f'{r7["admitted"]} {anc7}')

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
