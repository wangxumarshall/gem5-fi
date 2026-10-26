#!/usr/bin/env python3
"""test_lsu_evidence_durability.py — [0202-T02F2-DURABILITY] 异常中止下的证据耐久性。

规格（用户 2026-10-27 阶段4）：
  1. 每个 activated fault 的 L0 `inj` 在可能引发下游失败的操作前持久化；
  2. 正常退出生成完整兼容流；
  3. SIGINT 优雅退出生成完整流（走退出回调）；
  4. SIGABRT / 异常退出**至少保留最后一个已完整提交的数据块**；
  5. 异常流必须：truncated=True、**无伪造 chain_end**、无伪造 terminal、
     缺失字段保持空/未知（绝不填 0 冒充成功）；
  6. checker 能读取最后一个完整块并**指出截断位置**；
  7. 不在崩溃 signal handler 中调用非 async-signal-safe 操作；
  8. 设计评估（分块/独立 member/原子轮换/进程外写入器 …）须有测试证明；
  9. 记录性能开销，且不得扰动注入时序。

实测背景：发射器（CHAOSPropagation）用原生 zlib `gzFile`，**每条事件行后
`gzflush(Z_SYNC_FLUSH)`**，gzip trailer 由退出回调里的 `gzclose` 写出。
SIGABRT 时进程直接死亡 ⇒ 无 trailer、无 chain_end、无 funnel 摘要，但**每个
已 flush 的完整块都在盘上**。真实证据：T02-F2-W4 explicit seed 1 首轮
（runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814/）。

用法：python3 tests/test_lsu_evidence_durability.py   （退出码 0=全 PASS）
"""
import gzip
import os
import sys
import tempfile
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_prop_fields as P  # noqa: E402

FAILED = []
REAL_ABORT_STREAM = (ROOT / "runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814"
                     "/runs/engineering/ITEM-049_engineering_x1/prop_evt.txt.gz")


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name
          + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


def write_gz(path, lines, finish):
    """写 gzip 流：finish=True 写 trailer（完整）；False 只 Z_SYNC_FLUSH（模拟中止）。"""
    co = zlib.compressobj(6, zlib.DEFLATED, 16 + 15)
    buf = b""
    for ln in lines:
        buf += co.compress(ln.encode() + b"\n")
    buf += co.flush(zlib.Z_FINISH if finish else zlib.Z_SYNC_FLUSH)
    Path(path).write_bytes(buf)


EVT = ("PROP-EVT: kind=inj run_id=T02-F2-W4 sample_run_id=s1 fault_id=1 "
       "event_id={i} parent_event_id={p} tick={t} corr=origin")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="durab_"))

    print("[1] 完整流（有 trailer）⇒ truncated=False 且无截断原因")
    full = tmp / "full.txt.gz"
    write_gz(full, [EVT.format(i=i, p=(i - 1 if i else ""), t=i + 1) for i in range(5)],
             finish=True)
    d = {}
    ev, tr, _s, _i = P.read_stream(full, detail=d)
    check("完整流读到全部事件", len(ev) == 5, len(ev))
    check("truncated=False", tr is False, tr)
    check("detail.reason 为空", d.get("reason") is None, d.get("reason"))
    check("detail.last_event_id == 4", d.get("last_event_id") == "4", d.get("last_event_id"))

    print("[2] SIGABRT 型截断流（Z_SYNC_FLUSH、无 trailer）⇒ 保留最后完整块并指出位置")
    tr_path = tmp / "abort.txt.gz"
    write_gz(tr_path, [EVT.format(i=i, p=(i - 1 if i else ""), t=i + 1) for i in range(7)],
             finish=False)
    d = {}
    ev, tr, _s, _i = P.read_stream(tr_path, detail=d)
    check("截断流仍读到全部已 flush 事件（≥1）", len(ev) >= 1, len(ev))
    check("读到的正是前 7 条完整事件", [e["event_id"] for e in ev] ==
          [str(i) for i in range(7)], [e["event_id"] for e in ev])
    check("truncated=True", tr is True, tr)
    check("指出截断原因（异常类型）", bool(d.get("reason")), d.get("reason"))
    check("指出截断位置：last_event_id == 6", d.get("last_event_id") == "6", d.get("last_event_id"))
    check("指出截断位置：last_complete_boundary 非空",
          bool(d.get("last_complete_boundary")), d.get("last_complete_boundary"))
    check("last_tick 与最后事件一致", d.get("last_tick") == "7", d.get("last_tick"))

    print("[3] 异常流不得伪造 chain_end / terminal，缺失字段不得填 0")
    kinds = {e.get("kind") for e in ev}
    check("截断流里没有 chain_end（生命周期标记由退出回调发射，中止时不存在）",
          "chain_end" not in kinds, kinds)
    check("截断流里没有伪造的检测终局（detection_layer 全空）",
          all(not e.get("detection_layer") for e in ev), [e.get("detection_layer") for e in ev])
    ev0 = ev[0]
    check("缺失字段为空字符串而非 0（pfn/pa 等未填）",
          ev0.get("pa", "") == "" and ev0.get("cache_line", "") == "", ev0)

    print("[4] chain_check CLI 输出截断详情（需求 6）")
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
                        str(tr_path)], capture_output=True, text=True)
    import json
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {}
    check("CLI rc=0 且输出 JSON", r.returncode == 0 and bool(j), r.stderr[-200:])
    check("truncated_stream=True", j.get("truncated_stream") is True, j.get("truncated_stream"))
    check("truncation 详情含 last_event_id",
          (j.get("truncation") or {}).get("last_event_id") == "6", j.get("truncation"))

    print("[5] 真实 SIGABRT 产物（若在本机）")
    if REAL_ABORT_STREAM.exists():
        d = {}
        ev, tr, _s, _i = P.read_stream(REAL_ABORT_STREAM, detail=d)
        check("真实中止流读到非零事件", len(ev) > 0, len(ev))
        check("真实中止流 truncated=True", tr is True, tr)
        check("真实中止流指出截断位置", bool(d.get("last_complete_boundary")),
              d.get("last_complete_boundary"))
        check("真实中止流确实无 chain_end",
              not any(e.get("kind") == "chain_end" for e in ev))
        check("真实中止流的 inj 事件已落盘（每个 activated fault 的 L0 可查）",
              sum(1 for e in ev if e.get("kind") == "inj") >= 1,
              sum(1 for e in ev if e.get("kind") == "inj"))
    else:
        print("  SKIPPED [durability] 本机无真实中止产物（runs/ 未随 Git 分发）")

    print("[6] 性能开销（需求 9）：每行同步 flush 的 wall-time 成本")
    N = 4000
    lines = [EVT.format(i=i, p=i, t=i) for i in range(N)]
    # (a) 每行 Z_SYNC_FLUSH（发射器现状）
    t0 = time.perf_counter()
    co = zlib.compressobj(6, zlib.DEFLATED, 16 + 15)
    n = 0
    for ln in lines:
        n += len(co.compress(ln.encode() + b"\n"))
        co.flush(zlib.Z_SYNC_FLUSH)
    t_sync = time.perf_counter() - t0
    # (b) 仅末尾 flush（对照）
    t0 = time.perf_counter()
    co = zlib.compressobj(6, zlib.DEFLATED, 16 + 15)
    for ln in lines:
        co.compress(ln.encode() + b"\n")
    co.flush(zlib.Z_FINISH)
    t_batch = time.perf_counter() - t0
    per_line_us = (t_sync - t_batch) / N * 1e6
    print(f"      每行同步 flush 额外成本 ≈ {per_line_us:.2f} µs/行"
          f"（{N} 行实测 {t_sync*1e3:.1f} ms vs 批量 {t_batch*1e3:.1f} ms）")
    check("同步 flush 成本可接受（< 200 µs/行，不至于显著扰动）",
          per_line_us < 200.0, f"{per_line_us:.2f} µs/line")
    # 注入时序不受影响：gem5 的 tick 由事件队列决定，与 wall time 无关。
    # 用实测事件数估算整轮开销。
    check("整轮估算开销远小于 golden 的秒级预算（5178 行 × 实测 µs）",
          per_line_us * 5178 / 1e6 < 5.0, f"{per_line_us*5178/1e6:.3f} s")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
