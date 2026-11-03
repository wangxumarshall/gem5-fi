#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSU 30 模型 × 173 RunID 机器可读实施矩阵生成器.

数据来源（全部只读）:
  - 工作簿 docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx
    表 7（RunID/子模型/触发条件/传播监控）、表 9（必监控指标/现有覆盖/缺失钩子/
    实现状态）、表 10（模型级声明状态）。
  - 2026-11-02 真实代码审计（本文件 MODEL_AUDIT / WORKLOAD_AUDIT 内嵌，
    每条带 file:line 证据）。

输出:
  - docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json
  - docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.csv
  - docs/gem5-fi/fsu/IMPLEMENTATION_AUDIT.md

诚实约定:
  - “工作簿声明状态”与“代码审计状态”分列，后者覆盖前者。
  - 仅当注入器、真实 workload、golden/oracle、传播事件、链审计全部可用时
    status 才可为 IMPLEMENTED；当前审计无任何模型达到该标准。
"""
from __future__ import annotations

import csv
import functools
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx"
OUT = ROOT / "docs/gem5-fi/fsu"
DEFAULT_RUNS = ROOT / "runs/fsu"
SHEET7 = "7.展开执行矩阵"
SHEET9 = "9.逐RunID传播监控"
SHEET10 = "10.源码监控映射"
RUNID_SHEETS = (SHEET7, SHEET9)
EXPECTED_RUNIDS = 173

# ---------------------------------------------------------------------------
# 代码审计结论（2026-11-02，origin/fi-ding 46ce66cd）。
# status: IMPLEMENTED / PARTIAL / MISSING（对 FSU 语义而言）。
# ---------------------------------------------------------------------------
MODEL_AUDIT = {
    # ---- FP/SIMD Issue Queue ----
    "FQ01": dict(
        status="PARTIAL",
        injector="CHAOSIQ mode=tag_bitflip + targetClass=vec",
        hooks="CHAOSIQ.cc:587-663; inst_queue.cc:690-711; dyn_inst.hh:495-498",
        implemented="单个 Vec 源 tag 单 bit 翻转；insert 后 renameSrcReg 改 tag",
        missing="src0/src1 子模型选择；c 的 active-ready producer 判定；"
                "producer_sn/ready/activation 证据；operand hash；PROP 事件",
    ),
    "FQ02": dict(
        status="PARTIAL",
        injector="CHAOSIQ mode=tag_bitflip2 + targetClass=vec",
        hooks="CHAOSIQ.cc:593-663; inst_queue.cc:690-711",
        implemented="同一 Vec 源 tag 双 bit 翻转（faultMask 或随机两位）",
        missing="相邻/非相邻/跨子字段分层；候选域与越界计数；target writer/"
                "首个读者；PROP 事件",
    ),
    "FQ03": dict(
        status="MISSING",
        injector="无（tag_swap 是换成随机 producer，不是 src0↔src1 配对交换）",
        hooks="仅有 inst_queue.cc:690-711 单槽 hook",
        implemented="—",
        missing="src0↔src1 配对交换；FMA mul/add 源角色；lane 角色交换；"
                "双源配对日志；PROP 事件",
    ),
    "FQ04": dict(
        status="PARTIAL",
        injector="CHAOSIQ ready_early / ready_never / ready_never_event",
        hooks="CHAOSIQ.cc:665-777; inst_queue.cc:697-707,1234-1248",
        implemented="ready_early 可作用于 Vec；ready_never/_event 存在",
        missing="ready_never/_event 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；"
                "stale-ready 缺失；scoreboard 真值/旧值读取/ROB stall；PROP 事件",
    ),
    "FQ05": dict(
        status="MISSING",
        injector="无（无 valid/issued/squashed 注入 API）",
        hooks="inst_queue.cc insertNonSpec 无 hook",
        implemented="—",
        missing="valid lost/ghost、issued early、squash clear lost、nonSpec 伪造；"
                "IQ slot 生命期/occupancy 守恒；PROP 事件",
    ),
    "FQ06": dict(
        status="MISSING",
        injector="CHAOSIQ dispatch_misroute（仅 IntAlu↔IntMult）",
        hooks="CHAOSIQ.cc:815-856; inst_queue.cc:945-958",
        implemented="整数 FU class 误路由（对 FSU 不可用）",
        missing="FP/SIMD add-pipe↔mul-pipe、compatible FU index、scalar↔SIMD "
                "route；FU capability/grant/latency 证据；PROP 事件",
    ),
    "FQ07": dict(
        status="MISSING",
        injector="无（seqNum 仅用于日志/tag_stuck）",
        hooks="CHAOSIQ.cc:376,397",
        implemented="—",
        missing="ready-list rank/age swap、seqNum 合法替代、starvation bias；"
                "issue 顺序与性能差异；PROP 事件",
    ),
    "FQ08": dict(
        status="PARTIAL",
        injector="CHAOSIQ wake_omit / src_ready_bitflip / wake_phase",
        hooks="CHAOSIQ.cc:106-228; inst_queue.cc:1105-1144,1250-1281",
        implemented="wake 省略、错误 source、±phase 延迟",
        missing="duplicate wake；victim 非 Vec 限定且未写日志（inst_queue.cc:1272）；"
                "producer→consumer sn/tag 配对；b 在无 victim 时仍计注入；"
                "c 的延迟事件 squash 断言风险（inst_queue.cc:1160，UNVERIFIED）；"
                "PROP 事件",
    ),
    "FQ09": dict(
        status="MISSING",
        injector="无（noteIqDeparture 只读）",
        hooks="CHAOSIQ.cc:803-813; inst_queue.cc:1032-1036",
        implemented="—",
        missing="issue→execute early/late/drop/duplicate/stale slot；"
                "FUPool/FUCompletion 事件；PROP 事件",
    ),
    "FQ10": dict(
        status="MISSING",
        injector="无（dispatch_misroute 不改 FU index/busy/free）",
        hooks="无 FUPool/FUCompletion hook",
        implemented="—",
        missing="FU index 替代、busy→free/free→busy、release lost；"
                "FU 状态与 grant 证据；PROP 事件",
    ),
    # ---- FP/SIMD PRF ----
    "FR01": dict(
        status="PARTIAL",
        injector="CHAOSPhysReg phys/arch modes，VecRegClass，lane 8/16/32/64",
        hooks="CHAOSPhysReg.cc:328-392,459-501; regfile.hh:399-440",
        implemented="单个 Vec lane 内 1-bit/多位 XOR；FP64 字段未分层",
        missing="128-bit lane；FP32/FP64 字段分层；generation；ready/consumer "
                "谓词；old/new value hash；PROP 事件。工作簿“直接已有”高估",
    ),
    "FR02": dict(
        status="PARTIAL",
        injector="CHAOSPhysReg bitsToChange=2 / faultMask",
        hooks="CHAOSPhysReg.cc:328-392",
        implemented="同一 lane 内双 bit 翻转",
        missing="跨 lane、exp+mant 字段对、bit 距离/相邻性分类；"
                "越 lane 掩码丢失；PROP 事件",
    ),
    "FR03": dict(
        status="PARTIAL",
        injector="CHAOSPhysReg SA0/SA1 + setStuckTarget（仅标量）",
        hooks="CHAOSPhysReg.cc:364-447; regfile.hh:363-379",
        implemented="int/float 标量写路径永久 stuck",
        missing="Vec 写路径 stuck 未实现（不调用 setStuckTarget）；"
                "checkPermanent 按键号误伤 int PRF；clearStuckTarget 从未调用；"
                "exposure/applied 计数；PROP 事件",
    ),
    "FR04": dict(status="MISSING", injector="无", hooks="dyn_inst.hh:1213-1229 直接读 renamedSrcIdx",
                 implemented="—", missing="Vec 读地址/tag 替代到另一 active-ready Vec 物理寄存器；PROP 事件"),
    "FR05": dict(status="MISSING", injector="无", hooks="regfile.hh:238-323 只读计数",
                 implemented="—", missing="Vec 读端口输出 1-bit 翻转（不回写 PRF）；per-read 记录；PROP 事件"),
    "FR06": dict(status="MISSING", injector="无", hooks="regfile.hh:238-323",
                 implemented="—", missing="Vec 读端口多位/跨 lane 翻转；PROP 事件"),
    "FR07": dict(
        status="PARTIAL",
        injector="CHAOSFPU 执行后目标值 XOR（代理），非 PRF-WB hook",
        hooks="CHAOSFPU.cc:280-315",
        implemented="执行结果（含 Vec 低 64 位）单/多 bit XOR",
        missing="PRF 写回边界 hook；golden result、WB txn、dest tag、wakeup、"
                "consumer 链；PROP 事件",
    ),
    "FR08": dict(status="MISSING", injector="无", hooks="dyn_inst.hh:1240-1258 直接写 renamedDestIdx",
                 implemented="—", missing="Vec 写目标 tag 替代/交换；PROP 事件"),
    "FR09": dict(status="MISSING", injector="无", hooks="IEW scoreboard 写回未改",
                 implemented="—", missing="write-enable/ready/wakeup 原子性（lost/early/late/split）；PROP 事件"),
    "FR10": dict(status="MISSING", injector="无", hooks="gem5 O3 无 bypass mux hook",
                 implemented="—", missing="bypass/forwarding mux 与 partial-lane merge；PROP 事件"),
    # ---- FSU Pipe ----
    "FP01": dict(status="MISSING", injector="CHAOSFPU 仅结果侧 XOR，无操作数/A/B/C hook",
                 hooks="dyn_inst.cc:359-369; CHAOSFPU.cc:280-303",
                 implemented="—", missing="操作数/控制/流水线级故障；PROP 事件"),
    "FP02": dict(status="MISSING", injector="CHAOSFPU faultMask 仅结果低 64 位多位 XOR",
                 hooks="CHAOSFPU.cc:227-256",
                 implemented="结果侧粗粒度多位 XOR", missing="同 lane 相邻/跨 lane 双 bit 几何、FP32/全 128 位；PROP 事件"),
    "FP03": dict(status="MISSING", injector="CHAOSFPU 无；CHAOSDecode 仅有解码级 opcode swap（越界代理）",
                 hooks="CHAOSDecode.cc:77-125",
                 implemented="解码级 FP opcode 替换（非 FSU 内 op-select）", missing="FSU op-select 换值；PROP 事件"),
    "FP04": dict(
        status="PARTIAL",
        injector="CHAOSFPU 结果 XOR + bitseg(sign/exp_hi/exp_lo/mant_hi/mid/lo)",
        hooks="CHAOSFPU.cc:227-256,280-315; dyn_inst.cc:361-369",
        implemented="FP64 低 64 位结果字段单 bit 翻转；FP04-a/b/c 可试；"
                    "FSU PROP L0–L5 已落地（F0 三 seed 验证）",
        missing="FP32 字段映射；128-bit Vec 全 lane（FP04-d）；"
                "dest phys tag/old-correct/consumer/FPSR；F1/F2/F3 rate 语义"
                "（D2 实现中）。工作簿“直接已有”高估",
    ),
    "FP05": dict(status="PARTIAL", injector="CHAOSFPU faultMask / recurringStuck",
                 hooks="CHAOSFPU.cc:217-256",
                 implemented="结果多位 XOR、可重复同掩码", missing="2–4 事件 burst、burst_id/ordinal、lane mask/跨 lane；PROP 事件"),
    "FP06": dict(status="PARTIAL", injector="CHAOSFPU recurringStuck（结果侧 stuck 代理）",
                 hooks="CHAOSFPU.cc:217-227",
                 implemented="同一掩码重复应用于每次 eligible 结果", missing="SA0/SA1 极性、全向量宽度、exposure/applied 列表、部分积代理；PROP 事件"),
    "FP07": dict(status="PARTIAL", injector="CHAOSFPU fmaWeighted（E3 行为代理）",
                 hooks="CHAOSFPU.cc:229-241",
                 implemented="最终结果按 mant 85%/exp 10%/sign 5% 抽 bit", missing="真实 FMA 中间值不可达（gem5 功能级）；未限定 FMA opClass；partial row drop/dup/align shift；PROP 事件"),
    "FP08": dict(status="PARTIAL", injector="CHAOSFPU roundingSub / fpsrSuppress",
                 hooks="CHAOSFPU.cc:172-213",
                 implemented="结果 1-ULP 反向舍入代理；fpsrSuppress 仅计数", missing="FP32、FTZ/DN、异常/FPCR/FPSR 可观测状态；suppressed_count 未输出；PROP 事件"),
    "FP09": dict(status="MISSING", injector="无", hooks="CHAOSFPU 仅值 XOR",
                 implemented="—", missing="lane swap/rotate、元素宽度替代、mask 移位、新旧拼接；PROP 事件"),
    "FP10": dict(status="MISSING", injector="无", hooks="CHAOSFPU 仅执行后值 XOR",
                 implemented="—", missing="completion early/late/drop/duplicate、result/dest swap、stale completion、延迟配对；PROP 事件"),
}

# ---------------------------------------------------------------------------
# Workload 审计：W-ID → 真实载体 / golden / oracle。
# identity: REAL / PARTIAL / NO_TRUE_ARTIFACT / NO_FP_ARTIFACT / UNUSED
# ---------------------------------------------------------------------------
WORKLOAD_AUDIT = {
    "W0": dict(name="FSU-MiniCheck", identity="UNUSED",
               real="仅存在 LSU 整数版 workloads/directed/mini_check（无 FP/NEON）",
               path="workloads/directed/mini_check", golden="minicheck-golden-v1=07568da9f3ad5665（LSU）",
               oracle="exact 16-hex（但域不符）",
               gap="它不是 FSU 探针；173 个 RunID 未使用 W0"),
    "W1": dict(name="FP-ScalarProbe", identity="NO_TRUE_ARTIFACT",
               real="无专用产物；可用 method1_controls pure_fma 作部分标量 FMA 代理",
               path="workloads/directed/method1_controls", golden="purefma-golden-v1=98433fcf09968e6a",
               oracle="16-hex checksum（无 FPSR/FPCR/NaN/4 舍入）",
               gap="工作簿要求的 NaN/Inf/±0/subnormal、4 种舍入、FPSR/FPCR 均无载体"),
    "W2": dict(name="FP-IQ-Dependency", identity="NO_TRUE_ARTIFACT",
               real="无专用产物；dep_chain_vec 仅 NEON FMLA 依赖链",
               path="workloads/ooo/dep_chain/dep_chain_vec", golden="depchainvec-golden-v1=b1e661a247b95774",
               oracle="16-hex checksum（非逐边 oracle）",
               gap="缺 FP/NEON fan-out/fan-in、双源非交换、多 ready 竞争、mispredict 消费者"),
    "W3": dict(name="NEON-LaneProbe", identity="PARTIAL",
               real="neon_lane（仅 32-bit lane；XOR/shift/add）",
               path="workloads/directed/neon_lane", golden="neon-golden-v1=00000000526925fe",
               oracle="精确 16-hex + 64-hex per-lane 行",
               gap="缺 8/16/64-bit lane、extract/insert、widen/narrow、permute、reduce"),
    "W4": dict(name="FMA-DotProduct", identity="REAL",
               real="elemwise_fma_kernel（FP64 c[i]=a[i]*b[i]+d[i]）；"
                    "D2 另有 W4-rate-v1 扩展版（N=262144，实测 eligible 2,097,155）",
               path="workloads/directed/elemwise_fma_kernel",
               golden="elemwisefma-golden-v1=ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7；"
                      "elemwisefma-rate-v1-golden=e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba",
               oracle="ARRAYHASH 64-hex + ULP",
               gap="不是点积归约；FMA 中间值在 gem5 为功能级不可达（工作簿已注明代理）；"
                   "W4-rate-v1 尚无正式三 seed"),
    "W5": dict(name="PolyBench-FP", identity="PARTIAL",
               real="gemm/lu/cholesky/jacobi-2d（2mm 未 vendored）",
               path="workloads/ooo/polybench/",
               golden="gemm=116849d3adf3227b; lu=74ffe5eb77ea9257; cholesky=ea7e0d0e7c86582d; jacobi-2d=dc867b5f02998c1e",
               oracle="精确 FINAL 16-hex",
               gap="工作簿点名的 2mm 缺失；单 RunID 需绑定到具体程序而非“PolyBench-FP”标签"),
    "W6": dict(name="SVD-FFT-Sparse", identity="PARTIAL",
               real="svd_iterative_kernel；FFT/稀疏线性系统无固定产物",
               path="workloads/directed/svd_iterative_kernel",
               golden="svditerative-golden-v1=4afb95b5b32f3820",
               oracle="16-hex checksum",
               gap="FFT/IFFT 组合与稀疏线性系统组件缺失"),
    "W7": dict(name="FP-ExceptionRecovery", identity="NO_FP_ARTIFACT",
               real="仅整数除零/NULL 解引用崩溃探针（divzero_loop_kernel/exc_trigger）",
               path="workloads/directed/divzero_loop_kernel",
               golden="无 golden",
               oracle="无",
               gap="无 FP invalid/div0/overflow/underflow/inexact、FPCR/FPSR、精确恢复载体"),
    "W8": dict(name="Embench-FP-Selected", identity="UNUSED",
               real="nbody/minver 为 FP 项", path="workloads/ooo/embench/",
               golden="nbody=f39b4e8804f279c3; minver=9792f3ee24af3023",
               oracle="FINAL 16-hex", gap="无单一 W8 身份；173 RunID 未使用"),
    "W9": dict(name="libjpeg-turbo-NEON", identity="REAL",
               real="libjpeg-turbo 3.2.1 AArch64 NEON jpeg_wl",
               path="workloads/ooo/libjpeg/jpeg_wl",
               golden="libjpeg-golden-v1=c712f8f6fb9e21ec",
               oracle="FINAL 16-hex（解码 RGB FNV-1a）",
               gap="尚未被任何 FSU 173 RunID campaign 绑定"),
    "W10": dict(name="SPEC CPU2017 FP SimPoint", identity="UNUSED",
                real="无（需许可证）", path="—", golden="无", oracle="无",
                gap="仓库无源码/二进制/checkpoint；173 RunID 未使用"),
}

BASELINE_COMMIT = "46ce66cdb9c22f5e591b43b97b68c7d526704211"

# 2026-11-02 最初代码审计的全局缺口。原文保留，不得删除。
# 每项额外记录后来的裁决证据；status 由 probe_current_status() 实时覆盖。
BASELINE_GAPS = [
    {
        "id": "gem5_binary_missing",
        "text": "无 gem5 二进制：/home/sdc/gem5-fi-fsu/build/ARM/gem5.opt 不存在，任何 RunID 都无法运行",
        "resolved_by_commit": ["f8eb4a22", "2f65a647"],
        "resolution_evidence": "权威基线改为 CHAOS/gem5/build/ARM/gem5.opt；"
                               "Python 3.11.9 构建成功并由 F0 三 seed 使用",
    },
    {
        "id": "fsu_prop_evt_missing",
        "text": "无 FSU PROP-EVT 发射：CHAOSFPU/CHAOSIQ/CHAOSPhysReg 均未调用 CHAOSPropagation::notePropEvt",
        "resolved_by_commit": ["e541beb9"],
        "resolution_evidence": "CHAOSFPU emitFsu() 调用 CHAOSPropagation::notePropEvt；"
                               "F0 三 seed 的 prop_evt 已由链审计器解析",
    },
    {
        "id": "fsu_chain_auditor_missing",
        "text": "无 FSU 链审计器：无 fsu_prop_fields.py/fsu_chain_check.py；LSU 审计器为硬编码",
        "resolved_by_commit": ["15f6cd1b", "ccf4c96e", "26c96efe"],
        "resolution_evidence": "tools/fsu_prop_fields.py + tools/fsu_chain_check.py + "
                               "tools/fsu_seed_audit.py；逐 seed audit.json 已持久化",
    },
    {
        "id": "fsu_three_seed_runner_missing",
        "text": "无 FSU 三 seed 流水线：runner.py/campaign.py 无 FSU RunID/seed1..3/chain_report 支持",
        "resolved_by_commit": ["ef6b4036", "8e86d1ba"],
        "resolution_evidence": "tools/fsu_seed_runner.py（census→inject→oracle→chain）"
                               "与 F0 三 seed AUTHORITATIVE 证据",
    },
    {
        "id": "config_mismatch_b0",
        "text": "配置不匹配：ooo_proxy.py 默认 ROB=128、IQ=64、4-wide，工作簿 B0 为 ROB=40、IQ=32、3/3/3、8/8/8",
        "resolved_by_commit": [],
        "resolution_evidence": "未解决：C3 仍使用默认 ROB/IQ/width，B0 参数化未实现",
    },
    {
        "id": "model_level_tests_missing",
        "text": "所有模型均无模型级自动化测试；仅有转换器 24 项 + 实施矩阵 5 项",
        "resolved_by_commit": ["e541beb9", "15f6cd1b", "ccf4c96e", "26c96efe"],
        "resolution_evidence": "已新增 FSU rate/chain/runner/audit/index/矩阵测试；"
                               "但 30 个模型的逐模型行为测试仍未齐全（见 remaining_gaps）",
    },
]

GOLDEN_F0_W4 = "ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@functools.lru_cache(maxsize=1)
def _binary_probe():
    """权威二进制按 D0 证据顺序探测；不假设仓库根路径存在。"""
    candidates = [ROOT / "CHAOS/gem5/build/ARM/gem5.opt",
                  ROOT / "build/ARM/gem5.opt"]
    for p in candidates:
        if p.exists():
            st = p.stat()
            return {"path": str(p), "exists": True,
                    "sha256": _sha256_file(p), "size": st.st_size,
                    "mtime": st.st_mtime}
    return {"path": str(candidates[0]), "exists": False, "sha256": "",
            "size": 0, "mtime": 0}


@functools.lru_cache(maxsize=1)
def _head():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def probe_current_status():
    """当前 fsu HEAD 的可验证状态（与 baseline 审计分开记录）。"""
    fpu_cc = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
    fpu_txt = fpu_cc.read_text(encoding="utf-8", errors="replace") \
        if fpu_cc.exists() else ""
    prop_hh = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
    runner = ROOT / "tools/fsu_seed_runner.py"
    chain = ROOT / "tools/fsu_chain_check.py"
    rate = ROOT / "tools/fsu_rate_ordinals.py"
    tests = sorted((ROOT / "tests").glob("test_fsu_*.py"))
    binary = _binary_probe()
    rate_impl = rate.exists()
    return {
        "head": _head(),
        "head_note": "probe-time HEAD；本文件由其后继提交写入，故最终 HEAD 通常是该值的子提交",
        "branch": subprocess.run(
            ["git", "-C", str(ROOT), "branch", "--show-current"],
            capture_output=True, text=True).stdout.strip(),
        "gem5_binary": binary,
        "fsu_prop_emitter": {
            "implemented": ("emitFsu" in fpu_txt
                            and "notePropEvt" in fpu_txt
                            and prop_hh.exists()),
            "evidence": "CHAOSFPU.cc emitFsu -> CHAOSPropagation::notePropEvt",
        },
        "chain_auditor": {"implemented": chain.exists(),
                          "path": str(chain.relative_to(ROOT))},
        "three_seed_runner": {
            "implemented": runner.exists()
            and "AUTHORITATIVE" in runner.read_text(encoding="utf-8",
                                                    errors="replace"),
            "path": str(runner.relative_to(ROOT)),
        },
        "rate_ordinals": {
            "implemented": rate_impl,
            "path": str(rate.relative_to(ROOT)),
            "generator": "build_rate_ordinals" if rate_impl else "",
        },
        "model_level_tests": [str(p.relative_to(ROOT)) for p in tests],
        "config_b0_match": False,
        "config_b0_note": "ooo_proxy.py 仍为 C3 默认 ROB=128/IQ=64/4-wide；"
                          "工作簿 B0 的 ROB=40/IQ=32/3/3/3 未实现",
    }


def remaining_gaps(status):
    """只列当前仍成立、尚未解决的缺口。"""
    gaps = []
    for g in BASELINE_GAPS:
        if g["id"] == "gem5_binary_missing" and status["gem5_binary"]["exists"]:
            continue
        if g["id"] == "fsu_prop_evt_missing" and status["fsu_prop_emitter"]["implemented"]:
            continue
        if g["id"] == "fsu_chain_auditor_missing" and status["chain_auditor"]["implemented"]:
            continue
        if g["id"] == "fsu_three_seed_runner_missing" and status["three_seed_runner"]["implemented"]:
            continue
        if g["id"] == "model_level_tests_missing":
            # 已有 FSU 编排/链/审计测试，但 30 模型仍未逐个覆盖。
            gaps.append({
                "id": "per_model_behavior_tests_missing",
                "text": "30 个模型尚未逐个具备模型级行为测试（现有测试覆盖 "
                        "rate/链条/runner/audit/矩阵，不等于 30 模型全覆盖）",
            })
            continue
        gaps.append({"id": g["id"], "text": g["text"]})
    if not status["rate_ordinals"]["implemented"]:
        gaps.append({
            "id": "rate_ordinals_missing",
            "text": "F1/F2/F3 的真实 rate ordinal 语义尚未实现；不得只改 freq 标签",
        })
    return gaps


def resolved_gaps(status):
    out = []
    for g in BASELINE_GAPS:
        if not g["resolved_by_commit"]:
            continue
        # 只有当前探测确实成立时，才把历史缺口标为已解决。
        if g["id"] == "gem5_binary_missing" and not status["gem5_binary"]["exists"]:
            continue
        if g["id"] == "fsu_prop_evt_missing" and not status["fsu_prop_emitter"]["implemented"]:
            continue
        if g["id"] == "fsu_chain_auditor_missing" and not status["chain_auditor"]["implemented"]:
            continue
        if g["id"] == "fsu_three_seed_runner_missing" and not status["three_seed_runner"]["implemented"]:
            continue
        out.append({"id": g["id"], "text": g["text"],
                    "resolved_by_commit": list(g["resolved_by_commit"]),
                    "evidence": g["resolution_evidence"]})
    return out


def _sheet_rows(ws, header_row):
    header = [ws.cell(header_row, c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
        if all(v in (None, "") for v in vals):
            continue
        rows.append({str(k).strip(): v for k, v in zip(header, vals) if k is not None})
    return rows


def load_workbook_tables():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    # 表 7：首个 RunID 表头行 = 第 5 行（前有横幅/空行）
    ws7 = wb[SHEET7]
    hdr7 = next(r for r in range(1, ws7.max_row + 1)
                if any(str(ws7.cell(r, c).value).strip().lower() == "runid"
                       for c in range(1, ws7.max_column + 1)))
    rows7 = _sheet_rows(ws7, hdr7)
    rows9 = _sheet_rows(wb[SHEET9], 1)
    rows10 = _sheet_rows(wb[SHEET10], 1)
    return rows7, rows9, rows10


def _seed_completion(out_root, runid):
    n = 0
    for s in (1, 2, 3):
        if (Path(out_root) / runid / f"seed{s}" / "AUTHORITATIVE").exists():
            n += 1
    return n


def _coverage(runid, audited_status, workload_identity, seed_n):
    """Coverage semantics are independent of seed completion.

    PILOT_SUBMODEL_ONLY is only for a RunID whose workbook row requires more
    submodels than the validated pilot actually exercised.
    """
    if runid == "FSU-FP04-F0-W4":
        return ("PILOT_SUBMODEL_ONLY",
                "pilot covers FP04-c/mant_lo/W4/F0 only; workbook RunID "
                "requires FP04-a sign, FP04-b exp_hi/lo, FP04-c mant_hi/mid/lo, "
                "FP04-d NEON lane result, plus F1/F2/F3 semantics")
    if runid == "FSU-FP04-F0-W3":
        if seed_n:
            return ("PARTIAL",
                    f"official seeds {seed_n}/3 admitted with the real NEON "
                    "FP32 lane workload; evidence covers FP04-d lane2 sign "
                    "bit only (32-bit lane domain); FP04-a/b/c fields and "
                    "the other lanes are not covered")
        return ("PARTIAL",
                "real NEON FP32 lane workload and golden exist, but this "
                "RunID has 0/3 official seeds")
    if runid in ("FSU-FP04-F1-W4", "FSU-FP04-F2-W4", "FSU-FP04-F3-W4"):
        if seed_n:
            gate_note = (" The F3 multi-fault gate used the short W4 and is "
                         "not an official seed"
                         if runid == "FSU-FP04-F3-W4" else "")
            return ("PARTIAL",
                    f"W4-rate-v1 official seeds {seed_n}/3 admitted; "
                    f"{3 - seed_n} remaining.{gate_note}")
        return ("PARTIAL",
                "D2 implements real rate ordinals and W4-rate-v1 "
                "(N=2,097,155) is golden/census-ready, but this RunID still "
                "has 0/3 official seeds; the F3 multi-fault gate used the "
                "short W4 and is not an official seed")
    if audited_status == "MISSING":
        return ("BLOCKED_NOT_IMPLEMENTED",
                "injector/hook for this model is missing in the audited code")
    if workload_identity in ("NO_TRUE_ARTIFACT", "NO_FP_ARTIFACT"):
        return ("BLOCKED_NO_TRUE_ARTIFACT",
                "workload identity has no真实 artifact / oracle")
    if audited_status == "PARTIAL":
        return ("PARTIAL",
                "injector/model only partially covers the workbook submodels; "
                "no 3-seed evidence for this RunID")
    return ("COMPLETE", "")


def build(out_root=DEFAULT_RUNS):
    rows7, rows9, rows10 = load_workbook_tables()
    s9 = {r["RunID"]: r for r in rows9}
    s10 = {r["模型ID"]: r for r in rows10}
    rids = [r["RunID"] for r in rows7]
    if len(rids) != EXPECTED_RUNIDS:
        sys.exit(f"[ABORT] 表7 RunID 数 {len(rids)} != {EXPECTED_RUNIDS}")
    if len(set(rids)) != len(rids):
        sys.exit("[ABORT] 表7 RunID 重复")
    if set(rids) != set(s9):
        sys.exit("[ABORT] 表7/表9 RunID 集合不相等")

    matrix = []
    for r in rows7:
        rid = r["RunID"]
        model = r["模型ID"]
        freq = r["频率"]
        load = r["负载ID"]
        audit = MODEL_AUDIT[model]
        wl = WORKLOAD_AUDIT[load]
        r9 = s9[rid]
        claimed = s10[model]["实现状态"]
        status = probe_current_status()
        # baseline_blockers 保留最初审计事实；blockers 只列当前仍成立的缺口。
        baseline_blockers = [g["text"] for g in BASELINE_GAPS]
        blockers = [g["text"] for g in remaining_gaps(status)]
        if audit["status"] != "IMPLEMENTED":
            blockers.insert(0, f"注入器缺口（{audit['status']}）：{audit['missing']}")
        if wl["identity"] != "REAL":
            blockers.insert(0, f"workload 身份缺口（{wl['identity']}）：{wl['gap']}")
        if freq in ("F1", "F2", "F3") and not status["rate_ordinals"]["implemented"]:
            blockers.insert(0, "频率语义缺口：F1/F2/F3 需要真实 rate ordinal；"
                               "仅改 --fsu_freq 标签无效")
        if audit["status"] == "PARTIAL":
            activation = ("注入动作可施加，但 activated 需要额外消费/结果见证；"
                          "当前无 FSU PROP 事件，无法证明 activation")
        elif audit["status"] == "MISSING":
            activation = "该 RunID 的注入动作尚不存在，activated 不可定义"
        else:
            activation = "—"
        seed_n = _seed_completion(out_root, rid)
        coverage_status, coverage_reason = _coverage(
            rid, audit["status"], wl["identity"], seed_n)
        matrix.append({
            "runid": rid,
            "model_id": model,
            "unit": r["单元"],
            "freq": freq,
            "load_id": load,
            "load_name": r.get("负载名称"),
            "fault_location": r.get("注入位置"),
            "fault_type": r.get("故障类型"),
            "submodels": r.get("子模型"),
            "eligible_condition": r.get("触发条件"),
            "attempted_definition": "注入器在候选点到达注入门并选中目标（无论是否真正改写状态）",
            "eligible_definition": f"满足该模型 eligible 谓词：{r.get('触发条件')}；countOnly 统计 N_eligible",
            "activated_definition": activation,
            "workbook_status_sheet7": r.get("结果状态"),
            "workbook_status_sheet9": r9.get("实现状态"),
            "workbook_status_sheet10": claimed,
            "audited_status": audit["status"],
            "existing_injector": audit["injector"],
            "existing_hooks": audit["hooks"],
            "implemented": audit["implemented"],
            "missing_hooks": audit["missing"],
            "workload_definition": f"{wl['name']}：{r9.get('负载ID与说明')}",
            "real_workload_identity": wl["real"],
            "workload_path": wl["path"],
            "workload_identity_status": wl["identity"],
            "golden_oracle": f"{wl['golden']}；{wl['oracle']}",
            "required_l0_l5": r9.get("必监控单元/事件/指标"),
            "required_chain_path": r9.get("完整传播路径（按顺序）"),
            "fsu_fields_model_focus": s10[model].get("模型重点字段"),
            "cross_unit_keys": r9.get("跨单元关联键"),
            "test_status": "无模型级自动化测试（仅转换器 24 项 + 实施矩阵 5 项）",
            "three_seed_status": f"{seed_n}/3",
            "seed_completion": f"{seed_n}/3",
            "seed_completion_count": seed_n,
            "coverage_status": coverage_status,
            "coverage_reason": coverage_reason,
            "pilot": rid in ("FSU-FP04-F0-W4",),
            "baseline_blockers": baseline_blockers,
            "blockers": blockers,
            "remaining_gaps": [g["id"] for g in remaining_gaps(status)],
            "resolved_by_commit": {g["id"]: g["resolved_by_commit"]
                                   for g in resolved_gaps(status)},
        })

    # 汇总
    from collections import Counter
    status_counts = Counter(m["audited_status"] for m in matrix)
    model_status = {}
    for m in matrix:
        model_status.setdefault(m["model_id"], m["audited_status"])
    status = probe_current_status()
    summary = {
        "generated_from": str(XLSX),
        "baseline_commit": BASELINE_COMMIT,
        "current_head": status["head"],
        "current_binary_sha256": status["gem5_binary"]["sha256"],
        "baseline_gap": [{"id": g["id"], "text": g["text"],
                          "resolved_by_commit": g["resolved_by_commit"]}
                         for g in BASELINE_GAPS],
        "current_status": status,
        "resolved_by_commit": resolved_gaps(status),
        "remaining_gaps": remaining_gaps(status),
        "runid_count": len(matrix),
        "unique_runids": len(set(m["runid"] for m in matrix)),
        "sheet7_sheet9_sets_equal": True,
        "model_count": len(model_status),
        "model_status_counts": dict(Counter(model_status.values())),
        "runid_status_counts": dict(status_counts),
        "workload_identity_counts": dict(Counter(m["workload_identity_status"] for m in matrix)),
        "pilot_candidates": [m["runid"] for m in matrix if m["pilot"]],
        "seed_completion_counts": dict(Counter(m["seed_completion"] for m in matrix)),
        "coverage_status_counts": dict(Counter(m["coverage_status"] for m in matrix)),
        "coverage_dimensions": {
            "seed_completion": {
                "admitted_seeds": sum(m["seed_completion_count"] for m in matrix),
                "target_seeds": len(matrix) * 3,
                "complete_runids": sum(1 for m in matrix
                                       if m["seed_completion_count"] == 3),
            },
            "frequency_coverage": {
                f: f"{next((m['seed_completion_count'] for m in matrix if m['runid'] == f'FSU-FP04-{f}-W4'), 0)}/3"
                for f in ("F0", "F1", "F2", "F3")
            },
            "submodel_coverage": {
                "covered": ["FP04-c/mant_lo (formal W4 seeds)"],
                "partial": (
                    ["FP04-d lane result: 32-bit lane2 sign bit only "
                     f"(F0-W3 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W3'), 0)}/3)"]
                    if next((m["seed_completion_count"] for m in matrix
                             if m["runid"] == "FSU-FP04-F0-W3"), 0) else []
                ),
                "not_covered": ["FP04-a sign", "FP04-b exp_hi/exp_lo",
                                "FP04-c mant_hi/mant_mid",
                                "FP04-d other lanes/fields",
                                "FP32 formal RunID coverage",
                                "NEON 128-bit full field/lane matrix"],
            },
            "workload_coverage": {
                "W4": "REAL; short W4 F0 "
                      f"{next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W4'), 0)}/3; "
                      "W4-rate-v1 "
                      f"F1 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F1-W4'), 0)}/3, "
                      f"F2 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F2-W4'), 0)}/3, "
                      f"F3 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F3-W4'), 0)}/3",
                "W1": "NO_TRUE_ARTIFACT (gate-only FP32 scalar workload exists)",
                "W2": "NO_TRUE_ARTIFACT",
                "W3": "PARTIAL; real NEON FP32 lane workload "
                      f"F0-W3 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W3'), 0)}/3 "
                      "(lane2 sign only)",
                "W5": "PARTIAL", "W6": "PARTIAL",
                "W7": "NO_FP_ARTIFACT", "W9": "REAL but unbound",
                "W0/W8/W10": "UNUSED",
            },
            "overall": "NOT_COMPLETE",
        },
        "implemented_runids": [m["runid"] for m in matrix if m["audited_status"] == "IMPLEMENTED"],
        "models": model_status,
    }
    return matrix, summary


def write_outputs(matrix, summary):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "IMPLEMENTATION_MATRIX.json").write_text(
        json.dumps({"summary": summary, "runids": matrix},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    fields = ["runid", "model_id", "unit", "freq", "load_id", "load_name",
              "fault_type", "submodels", "eligible_condition",
              "attempted_definition", "eligible_definition", "activated_definition",
              "audited_status", "workbook_status_sheet10", "existing_injector",
              "implemented", "missing_hooks", "real_workload_identity",
              "workload_path", "workload_identity_status", "golden_oracle",
              "required_l0_l5", "fsu_fields_model_focus", "test_status",
              "three_seed_status", "seed_completion", "coverage_status",
              "coverage_reason", "pilot", "remaining_gaps",
              "baseline_blockers", "blockers"]
    with (OUT / "IMPLEMENTATION_MATRIX.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n",
                           extrasaction="ignore")
        w.writeheader()
        for m in matrix:
            w.writerow({**m,
                        "remaining_gaps": " || ".join(m["remaining_gaps"]),
                        "baseline_blockers": " || ".join(m["baseline_blockers"]),
                        "blockers": " || ".join(m["blockers"])})

    st = summary["current_status"]
    bin_ = st["gem5_binary"]
    lines = ["# FSU 30 模型 × 173 RunID 实施审计（阶段 B + D2 事实刷新）", "",
             f"> 设计时基线：`origin/fi-ding` `{summary['baseline_commit']}`；"
             f"当前 HEAD：`{summary['current_head']}`；"
             "生成工具：`tools/fsu_implementation_matrix.py`；"
             "数据源：工作簿表 7/9/10 + 初始代码审计 + 当前状态实时探测。", "",
             "## 1. 结论", "",
             f"- RunID 总数：**{summary['runid_count']}**（唯一 {summary['unique_runids']}；"
             "表 7/表 9 集合相等）",
             f"- 模型数：**{summary['model_count']}**；模型状态："
             + "、".join(f"{k} {v}" for k, v in sorted(summary["model_status_counts"].items())),
             f"- RunID 状态："
             + "、".join(f"{k} {v}" for k, v in sorted(summary["runid_status_counts"].items())),
             f"- workload 身份："
             + "、".join(f"{k} {v}" for k, v in sorted(summary["workload_identity_counts"].items())),
             f"- **可端到端运行（注入器+workload+oracle+传播链）的 RunID："
             f"{len(summary['implemented_runids'])}/{summary['runid_count']}**", "",
             "工作簿把 FR01/FP04 标为“直接已有”，但代码审计显示二者均只覆盖部分子模型："
             "FR01 无 128-bit lane/FP 字段分层/generation/consumer；FP04 仅 FP64 低 64 位结果字段，"
             "FP32 与 NEON 全 lane（FP04-d）缺失。FP04 的 FSU PROP 发射端与 F0 传播链已落地，"
             "但子模型覆盖仍不完整；FR01 仍无 FSU PROP 链，不能直接进入三 seed 执行。", "",
             "## 2. 30 模型审计表", "",
             "| 模型 | 单元 | 工作簿声明 | 代码审计 | 现有注入器 | 关键缺口 |",
             "|---|---|---|---|---|---|"]
    for model in sorted(summary["models"]):
        m0 = next(m for m in matrix if m["model_id"] == model)
        lines.append(f"| {model} | {m0['unit']} | {m0['workbook_status_sheet10']} | "
                     f"**{m0['audited_status']}** | {m0['existing_injector']} | "
                     f"{m0['missing_hooks']} |")
    lines += ["", "## 2.1 RunID 状态（seed_completion 与 coverage_status 独立）", "",
              "- seed_completion："
              + "、".join(f"{k} {v}" for k, v in sorted(summary["seed_completion_counts"].items())),
              "- coverage_status："
              + "、".join(f"{k} {v}" for k, v in sorted(summary["coverage_status_counts"].items())),
              "", "| RunID | seed_completion | coverage_status | coverage_reason |",
              "|---|---|---|---|"]
    for m in matrix:
        lines.append(f"| {m['runid']} | {m['seed_completion']} | "
                     f"{m['coverage_status']} | {m['coverage_reason']} |")
    lines += ["", "## 3. 基线缺口 vs 当前状态", "",
              "### 3.1 baseline_gap（2026-11-02 最初审计原文，保留不删）", ""]
    for g in summary["baseline_gap"]:
        lines.append(f"- `{g['id']}`：{g['text']}")
    lines += ["", "### 3.2 current_status（当前 fsu HEAD 实测）", "",
              f"- HEAD：`{st['head']}`（branch `{st['branch']}`）",
              f"- gem5 二进制：`{bin_['path']}`；存在={bin_['exists']}；"
              f"SHA-256=`{bin_['sha256'] or 'N/A'}`；size={bin_['size']}",
              f"- FSU PROP 发射端：{st['fsu_prop_emitter']['implemented']}"
              f"（{st['fsu_prop_emitter']['evidence']}）",
              f"- FSU 链审计器：{st['chain_auditor']['implemented']}"
              f"（`{st['chain_auditor']['path']}`）",
              f"- FSU 三 seed runner：{st['three_seed_runner']['implemented']}"
              f"（`{st['three_seed_runner']['path']}`）",
              f"- rate ordinal 工具：{st['rate_ordinals']['implemented']}"
              f"（`{st['rate_ordinals']['path']}`）",
              f"- 模型级测试文件：{len(st['model_level_tests'])} 个",
              f"- B0 配置匹配：{st['config_b0_match']}（{st['config_b0_note']}）", "",
              "### 3.3 resolved_by_commit", ""]
    for r in summary["resolved_by_commit"]:
        lines.append(f"- `{r['id']}`：已由 {', '.join(r['resolved_by_commit'])} 解决；"
                     f"{r['evidence']}")
    lines += ["", "### 3.4 remaining_gaps（当前仍成立，不含已解决事项）", ""]
    lines += [f"- `{g['id']}`：{g['text']}" for g in summary["remaining_gaps"]]
    lines += ["", "## 4. Workload 身份审计", "",
              "| W-ID | 名称 | 身份 | 真实载体 | golden/oracle | 缺口 |",
              "|---|---|---|---|---|---|"]
    for wid, w in WORKLOAD_AUDIT.items():
        lines.append(f"| {wid} | {w['name']} | **{w['identity']}** | "
                     f"`{w['path']}` {w['real']} | {w['golden']}；{w['oracle']} | {w['gap']} |")
    lines += ["", "## 5. 试点现状", "",
              "**FSU-FP04-F0-W4**（FP04-c/mant_lo + 短 `elemwise_fma_kernel` + "
              "ARRAYHASH/ULP）已完成三 seed：",
              "- seed_completion = 3/3，逐 seed admitted/certified=true、violations=[]；",
              "- coverage_status 仍为 PILOT_SUBMODEL_ONLY（只覆盖 FP04-c 的 mant_lo，"
              "不是 FP04 全子模型，也不是 F1/F2/F3）。",
              "- 已解决的全局能力见 3.3；仍缺的能力见 3.4。", "",
              "## 6. 诚实边界", "",
              "- 本表不把“不支持/未激活/缺观测字段”记为 Masked；三 seed 状态一律 0/3。",
              "- 工作簿声明状态与代码审计状态分列；未观测到的运行时行为标 UNVERIFIED。",
              "- 未运行 gem5（服务器上无二进制），本阶段结论仅来自静态代码/工作簿/产物审计。", ""]
    (OUT / "IMPLEMENTATION_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[matrix] {len(matrix)} RunID；模型状态 {summary['model_status_counts']}；"
          f"RunID 状态 {summary['runid_status_counts']}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_MATRIX.json'}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_MATRIX.csv'}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_AUDIT.md'}")


if __name__ == "__main__":
    write_outputs(*build())
