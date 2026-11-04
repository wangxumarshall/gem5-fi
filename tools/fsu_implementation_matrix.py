#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSU 30 模型 × 173 RunID 机器可读实施矩阵生成器.

数据来源（全部只读）:
  - 工作簿 docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx
    表 7（RunID/子模型/触发条件/传播监控）、表 9（必监控指标/现有覆盖/缺失钩子/
    实现状态）、表 10（模型级声明状态）。
  - 2026-11-02 真实代码审计（本文件 MODEL_AUDIT / WORKLOAD_AUDIT 内嵌，
    每条带 file:line 证据）。
  - 磁盘权威 seed 状态：复用 fsu_index.scan（AUTHORITATIVE + audit.ok；
    W5 suite seed 只计 1，component run 不计）。
  - 当前代码能力探测：probe_capability_evidence（静态 grep/文件证据，
    code_present 不等于正式认证）。

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

# 复用磁盘权威索引的 seed 语义：只有 AUTHORITATIVE + audit.ok 才计 seed，
# W5 suite seed 的 5 个 component run 只计 1 个 seed。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_index  # noqa: E402

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
        injector="CHAOSPhysReg SA0/SA1 + setStuckTarget；FR03 Vec 写路径按 generation 重施加",
        hooks="regfile.hh:212-296,363-486; CHAOSPhysReg.cc:111-150,428-451",
        implemented="标量 int/float 写路径 stuck；Vec 写路径每次写入后重施加 "
                    "SA0/SA1（非 XOR）；永久物理 cell 跨 generation 保留，"
                    "generation 只标识分配世代/暴露链；host 纯模型单测 "
                    "（tests/unit/chaos_vec_stuck_test.cc、"
                    "tests/unit/chaos_physreg_generation_test.cc）",
        missing="FR03-F5-W3 已完成 3/3（L5 commit/squash/first-impact、"
                "runner 显式 CHAOSPhysReg 路径、O3 生命周期 gate）；"
                "FSU_PROP L0-L5 已接入；FR03-F5-W5/W6 仍 BLOCKED"
                "（不得借用 W3 证据）；模型整体仍为 PARTIAL"),
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
    "FP06": dict(
        status="PARTIAL",
        injector="CHAOSFPU permanentStuck + f5Warmup（结果侧 stuck；安装一次、多次 exposure）",
        hooks="CHAOSFPU.cc:213-269,780-812,1438; chaos_trigger.hh:9,57; chaos_fsu_fields.hh applyStuck",
        implemented="F5 永久语义：warm-up 后唯一安装根；SA0/SA1 强制极性"
                    "（&~mask / |mask，非 XOR）；有界 exposure 采样；"
                    "FSU_PROP L0–L5 + chain_end。FP06-a/b/c 已由 "
                    "FSU-FP06-F5-W3 3/3 正式认证（结果侧代理）",
        missing="FP06-d partial-product proxy MISSING（不得用最终结果位冒充）；"
                "全向量宽度超过 128-bit；W4/W5/W6 尚未完成正式认证；"
                "FP06-a/b/c 的正式认证只覆盖 W3 的 32-bit lane2/结果侧代理",
    ),
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
    "W1": dict(name="FP-ScalarProbe", identity="REAL",
               real="w1_fp_scalar_probe（FP32/FP64 add/sub/mul/div/sqrt/FMA；"
                    "NaN/Inf/±0/subnormal；RN/RP/RM/RZ；FPSR/FPCR 快照）",
               path="workloads/directed/w1_fp_scalar_probe",
               golden="w1-fpscalarprobe-v1-golden=ffe18c8279bf419d9b0aad0f5e039018"
                      "74d3440506066d93ede75820f2eba183",
               oracle="ARRAYHASH 64-hex（结果32+结果64+FPSR+FPCR）+ ULP；in-run golden/check",
               gap="F0-W1 3/3 在 B0-core 下注入 FP32 scalar sign；FP64、特殊值、"
                   "4 舍入与 FPSR 由 workload 执行但未逐 seed 注入；FPCR trap/"
                   "异常恢复在 SE 中 N/A"),
    "W2": dict(name="FP-IQ-Dependency", identity="NO_TRUE_ARTIFACT",
               real="无专用产物；dep_chain_vec 仅 NEON FMLA 依赖链",
               path="workloads/ooo/dep_chain/dep_chain_vec", golden="depchainvec-golden-v1=b1e661a247b95774",
               oracle="16-hex checksum（非逐边 oracle）",
               gap="缺 FP/NEON fan-out/fan-in、双源非交换、多 ready 竞争、mispredict 消费者"),
    "W3": dict(name="NEON-LaneProbe", identity="PARTIAL",
               real="neon_fp32_lane_kernel（float32x4 FMA，4×32-bit lane；"
                    "真实 golden/census；旧 neon_lane 为整数 NEON，不在 FSU eligible 域）",
               path="workloads/directed/neon_fp32_lane_kernel",
               golden="neonfp32lane-v1-golden=cb66197d92c7656b9359b312e93180ea"
                      "af3c1e774d9264d7d0b595189bce8c2e",
               oracle="ARRAYHASH 64-hex + ULP + LANEHASH0..3（非单一 16-hex FINAL）",
               gap="F0-W3 3/3 仅覆盖 lane2 sign（bit95）；缺其他 lane/字段、"
                   "8/16/64-bit lane、extract/insert、widen/narrow、permute、reduce"),
    "W4": dict(name="FMA-DotProduct", identity="REAL",
               real="elemwise_fma_kernel（FP64 c[i]=a[i]*b[i]+d[i]）；"
                    "D2 另有 W4-rate-v1 扩展版（N=262144，实测 eligible 2,097,155）",
               path="workloads/directed/elemwise_fma_kernel",
               golden="elemwisefma-golden-v1=ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7；"
                      "elemwisefma-rate-v1-golden=e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba",
               oracle="ARRAYHASH 64-hex + ULP",
               gap="不是点积归约；FMA 中间值在 gem5 为功能级不可达（工作簿已注明代理）；"
                   "W4-rate-v1 的 F1/F2/F3-W4 已各 3/3 正式完成，"
                   "但 F0-W4 仍是短 W4 pilot"),
    "W5": dict(name="PolyBench-FP", identity="PARTIAL",
               real="gemm/2mm/lu/cholesky/jacobi-2d（suite polybench-fp-v1，五程序均已 vendored）",
               path="workloads/ooo/polybench/",
               golden="gemm=116849d3adf3227b; 2mm/lu/cholesky/jacobi-2d 见 "
                      "configs/fsu/suites/polybench-fp-v1.json（逐元素 oracle）",
               oracle="精确 FINAL 16-hex + canonical array 逐元素 abs/rel/ULP",
               gap="suite 五程序已完成 FSU-FP04-F0-W5 3/3（每 suite seed 只计 1）；"
                   "workbook 单 RunID 仍绑定 suite 而非单一程序，PolyBench "
                   "全集与其他规模未覆盖"),
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
        "config_b0_match": True,
        "config_b0_note": "B0-core 已实现并经 F0-W1 的 config.ini 逐项校验："
                          "ROB=40/IQ=32/fetch-decode-rename 3/3/3/dispatch6/"
                          "issue-wb-commit 8/8/8/PRF 128/192/48/LQ-SQ16。"
                          "完整 v7a_3 的 FP FUPool=2 尚未实现，属剩余缺口。",
        "config_b0_full_match": False,
    }


def _read_text(path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _occ(rel_path: str, needle: str) -> int:
    return _read_text(ROOT / rel_path).count(needle)


def _has(rel_path: str, needle: str) -> bool:
    return _occ(rel_path, needle) > 0


def _cap(code_present: bool, evidence, certified=False, certification="") -> dict:
    """一个能力探测条目。

    code_present 只表示静态代码/测试文件存在，绝不等于正式认证；
    certified 只来自磁盘 AUTHORITATIVE + audit.ok 的正式 seed。
    """
    return {
        "code_present": bool(code_present),
        "evidence": evidence if isinstance(evidence, list) else [evidence],
        "certified": bool(certified),
        "certification": certification,
        "note": "code/test presence is not formal certification",
    }


def probe_capability_evidence(seed_map=None) -> dict:
    """当前代码能力探测（静态证据 + 磁盘正式 seed 认证分开记录）。

    seed_map: fsu_index.scan 的 {runid: row}；用于把“代码存在”与
    “已有 certified 正式 seed”严格区分。未提供时按无认证处理。
    """
    seed_map = seed_map or {}

    def rows(rid):
        return seed_map.get(rid, {})

    def certified(rid):
        r = rows(rid)
        return (r.get("admitted_seeds") == 3
                and all(s.get("state") == "admitted"
                        for s in r.get("seeds", {}).values()))

    no_cert = "无正式认证 seed"
    fr03_ok = (certified("FSU-FR03-F5-W5") or certified("FSU-FR03-F5-W6"))
    fr03_cert = ("FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3"
                 if fr03_ok else no_cert)
    w3_ok = certified("FSU-FP06-F5-W3")
    w1_ok = certified("FSU-FP06-F5-W1")
    fp06_ok = w3_ok and w1_ok
    if fp06_ok:
        fp06_cert = ("FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，"
                     "逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理"
                     "（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），"
                     "FP06-d 仍 MISSING")
    elif w3_ok:
        fp06_cert = ("FSU-FP06-F5-W3 正式 seed 3/3，逐 seed audit.ok；"
                     "仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域）")
    else:
        fp06_cert = no_cert

    fpu_cc = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
    fpu_py = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py"
    fpu_fields = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/chaos_fsu_fields.hh"
    phys_cc = "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc"
    regfile = "CHAOS/gem5/src/cpu/o3/regfile.hh"
    vec_unit = "tests/unit/chaos_vec_stuck_test.cc"
    vec_pytest = "tests/test_chaos_vec_stuck_cpp.py"
    f5_pytest = "tests/test_chaos_fsu_f5_cpp.py"
    runner = "tools/fsu_seed_runner.py"

    f5_schedule = (_has(fpu_cc, "fault_installed")
                   and _has(fpu_cc, "f5_warmup")
                   and _has(fpu_py, "f5Warmup"))
    stuck_apply = (_has(fpu_fields, "applyStuck")
                   and _has(fpu_fields, "stuckPolarityValid")
                   and _has(fpu_cc, "applyStuck"))
    prop_free = (not _has(phys_cc, "notePropEvt")
                 and not _has(regfile, "notePropEvt"))
    vec_stuck_code = (_has(regfile, "setStuckTarget")
                      and _has(regfile, "reapplyVecStuck")
                      and _has(phys_cc, "maybeReapplyStuck"))
    gen_code = (_has(regfile, "generationOf")
                and _has(regfile, "armVecStuck")
                and _has(regfile, "flat_generation"))
    squash_test = _has(vec_unit, "squash") and _has(regfile, "squash")
    phys_runner = _has(runner, "CHAOSPhysReg") or _has(runner, "phys_reg")
    partial_product = (_has(fpu_cc, "partial_product")
                       or _has(fpu_cc, "partialProduct")
                       or _has(fpu_py, "injectPartialProduct"))

    return {
        "probe_basis": "static grep / file probes at generation time; "
                       "code_present != formal certification",
        "FP06": {
            "permanent_stuck": _cap(
                _has(fpu_cc, "permanentStuck") and _has(fpu_py, "permanentStuck"),
                [f"{fpu_cc}: permanentStuck x{_occ(fpu_cc, 'permanentStuck')}",
                 f"{fpu_py}: permanentStuck parameter"],
                fp06_ok, fp06_cert),
            "f5_schedule_install_once": _cap(
                f5_schedule,
                [f"{fpu_cc}: fault_installed/f5_warmup",
                 f"{fpu_py}: f5Warmup"],
                fp06_ok, fp06_cert),
            "sa0_sa1_non_xor": _cap(
                stuck_apply,
                [f"{fpu_fields}: applyStuck/stuckPolarityValid",
                 f"{fpu_cc}: applyStuck x{_occ(fpu_cc, 'applyStuck')}"],
                fp06_ok, fp06_cert),
            "apply_stuck": _cap(
                _has(fpu_cc, "applyStuck"),
                f"{fpu_cc}: applyStuck x{_occ(fpu_cc, 'applyStuck')}",
                fp06_ok, fp06_cert),
            "fsu_prop_l0_l5": _cap(
                _has(fpu_cc, "notePropEvt") and _has(fpu_cc, "emitFsu"),
                [f"{fpu_cc}: emitFsu -> notePropEvt",
                 "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"],
                fp06_ok, fp06_cert),
            "chain_end": _cap(
                _has(fpu_cc, "chain_end"),
                f"{fpu_cc}: chain_end x{_occ(fpu_cc, 'chain_end')}",
                fp06_ok, fp06_cert),
            "bounded_exposure_sampling": _cap(
                _has(fpu_cc, "f5_sample_limit")
                and _has(fpu_cc, "exposures_dropped"),
                [f"{fpu_cc}: f5_sample_limit/exposures_dropped",
                 f5_pytest],
                fp06_ok, fp06_cert),
            "partial_product_proxy_fp06d": _cap(
                partial_product,
                [f"{fpu_py}: gem5 ARM FP is a functional model; no "
                 "partial-product/alignment-shift injection point",
                 "grep partial_product/partialProduct: no injection code"],
                False, "FP06-d MISSING；不得用最终结果位冒充部分积"),
        },
        "FR03": {
            "vec_stuck_write_path": _cap(
                vec_stuck_code,
                [f"{regfile}: setStuckTarget/reapplyVecStuck",
                 f"{phys_cc}: maybeReapplyStuck",
                 vec_unit, vec_pytest],
                fr03_ok, fr03_cert),
            "permanent_cell_across_generations": _cap(
                gen_code,
                [f"{regfile}: flat_generation/generationOf/armVecStuck "
                 "generation is identity, not a match/clear key",
                 "tests/unit/chaos_physreg_generation_test.cc: "
                 "cross-generation persistence + chain restart"],
                fr03_ok, fr03_cert),
            "chaosphysreg_fsu_prop": _cap(
                not prop_free,
                [f"{phys_cc}: notePropEvt x{_occ(phys_cc, 'notePropEvt')}",
                 f"{regfile}: notePropEvt x{_occ(regfile, 'notePropEvt')}",
                 "O3 commit/ROB squash hooks + honest chain_end terminal"],
                fr03_ok, fr03_cert),
            "runner_chaosphysreg_path": _cap(
                phys_runner,
                f"{runner}: CHAOSPhysReg/phys_reg x"
                f"{_occ(runner, 'CHAOSPhysReg') + _occ(runner, 'phys_reg')}",
                fr03_ok, fr03_cert),
            "squash_realloc_container_test": _cap(
                squash_test,
                [f"{vec_unit}: squash x{_occ(vec_unit, 'squash')}, "
                 f"realloc x{_occ(vec_unit, 'realloc')}",
                 vec_pytest, "real O3 gate: F5-FR03-W3-GATE-v3"],
                fr03_ok, fr03_cert),
            "fr03_formal_seeds": _cap(
                fr03_ok is not False,
                "runs/fsu/FSU-FR03-F5-W3: 3/3 certified; "
                "W5/W6 remain BLOCKED",
                fr03_ok,
                "FR03-F5-W3 3/3；W5/W6 不得借用 W3 证据"),
        },
        "W6_suite": {
            "svd_fft_sparse_real_artifacts": _cap(
                (ROOT / "workloads/directed/fft_radix2_kernel.c").exists()
                and (ROOT / "workloads/directed/sparse_cg_kernel.c").exists()
                and (ROOT / "configs/fsu/suites/w6-fp-v1.json").exists(),
                ["workloads/directed/svd_iterative_kernel.c",
                 "workloads/directed/fft_radix2_kernel.c",
                 "workloads/directed/sparse_cg_kernel.c",
                 "configs/fsu/suites/w6-fp-v1.json"],
                certified("FSU-FP04-F0-W6") and certified("FSU-FP06-F5-W6"),
                ("FSU-FP04-F0-W6 与 FSU-FP06-F5-W6 suite seed 各 3/3"
                 if (certified("FSU-FP04-F0-W6")
                     and certified("FSU-FP06-F5-W6")) else no_cert)),
        },
        "W5_suite": {
            "five_programs_including_2mm": _cap(
                (ROOT / "workloads/ooo/polybench/2mm").exists()
                and (ROOT / "configs/fsu/suites/polybench-fp-v1.json").exists(),
                ["workloads/ooo/polybench/2mm",
                 "configs/fsu/suites/polybench-fp-v1.json"],
                certified("FSU-FP04-F0-W5"),
                ("FSU-FP04-F0-W5 suite seed 3/3（component run 不计 seed）"
                 if certified("FSU-FP04-F0-W5") else no_cert)),
        },
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


def _seed_state_map(out_root, runids):
    """磁盘权威 seed 状态：复用 fsu_index.scan/_seed_state。

    只有 AUTHORITATIVE + chain_report + audit.ok 才算 admitted；
    suite_manifest.json 的 W5 suite seed 只计 1 个 seed（5 component 不计）。
    """
    rows, summary, scope = fsu_index.scan(runids, Path(out_root), None)
    return {r["runid"]: r for r in rows}, summary, scope


def _coverage(runid, audited_status, workload_identity, seed_n, model=None):
    """Coverage semantics are independent of seed completion.

    PILOT_SUBMODEL_ONLY is only for a RunID whose workbook row requires more
    submodels than the validated pilot actually exercised.
    """
    if runid == "FSU-FP06-F5-W3":
        if seed_n == 3:
            return ("PARTIAL",
                    "certified 3/3: FP06-a SA0 / FP06-b SA1 / FP06-c fixed "
                    "mantissa, 16,384 exposures each; covers the F5 "
                    "result-side proxy of FP06-a/b/c only. FP06-d "
                    "partial-product proxy is MISSING; evidence stays in the "
                    "W3 32-bit lane2 sign/mantissa domain")
        return ("PARTIAL",
                f"F5 permanent code path exists, but this RunID has "
                f"{seed_n}/3 formal seeds; no certification")
    if runid == "FSU-FP06-F5-W1":
        if seed_n == 3:
            return ("PARTIAL",
                    "certified 3/3, but this RunID covers only the FP06 "
                    "precision/opClass subset exercised by W1; FP06-d remains "
                    "MISSING and the full workbook submodels are not covered")
        return ("PARTIAL",
                "not run (0/3): FP06-F5-W1 gate/formal seeds are not "
                "complete; the F5 permanent semantics exist in code but "
                "cannot be certified for this RunID")
    if runid == "FSU-FR07-F0-W1":
        # 2026-11-04 position audit: the existing seeds inject AFTER the FU
        # result was written to the PRF cell; the workbook requires modifying
        # the writeback data BEFORE the PRF write. They stay as preserved
        # PROXY_EVIDENCE and are excluded from strict certification until the
        # real PRF-WB hook gate passes.
        return ("PARTIAL",
                "PROXY_EXCLUDED: 3 preserved execute-post-write proxy seeds "
                "are not counted as FR07 certification; the workbook "
                "PRF-WB data-boundary hook is not yet implemented "
                "(FR07-PRF-WB-POSITION-AUDIT.md)")
    if runid in ("FSU-FP06-F5-W4", "FSU-FP06-F5-W5"):
        if seed_n == 3:
            return ("COMPLETE",
                    f"certified 3/3: {runid} formal seeds admitted and "
                    "audit.ok; bounded F5 evidence")
        return ("PARTIAL",
                f"not formally complete ({seed_n}/3): F5 gate evidence exists "
                "and the RunID still needs all three certified seeds")
    if runid in ("FSU-FP04-F0-W6", "FSU-FP06-F5-W6"):
        if seed_n == 3:
            return ("COMPLETE",
                    "certified 3/3: SVD/FFT/sparse-CG suite seed, 3 "
                    "components per seed (components never count as seeds)")
        return ("PARTIAL",
                f"W6 suite {seed_n}/3; gate/model artifacts exist")
    if runid == "FSU-FR03-F5-W3":
        if seed_n == 3:
            return ("COMPLETE",
                    "certified 3/3: permanent Vec cell, real L5 commit/squash, "
                    "runner CHAOSPhysReg path and lifecycle gate")
        return ("PARTIAL",
                f"FR03-F5-W3 {seed_n}/3 after protocol review: seed3 "
                "attempt-1 is a real Masked/unconsumed outcome; attempt-2 "
                "changed the target and is supplemental evidence only")
    if runid in ("FSU-FR03-F5-W5", "FSU-FR03-F5-W6"):
        if seed_n == 3:
            return ("COMPLETE",
                    "certified 3/3: FR03 permanent Vec-cell suite; components "
                    "never count as seeds")
        return ("PARTIAL", f"FR03 FR03 suite {seed_n}/3")
    if runid in ("FSU-FR03-F5-W5", "FSU-FR03-F5-W6"):
        return ("COMPLETE" if seed_n == 3 else "PARTIAL",
                "FR03 permanent Vec-cell suite, components never count as seeds")
    if runid.startswith("FSU-FR03-F5-"):
        return ("BLOCKED",
                f"BLOCKED: FR03-F5 {runid[-4:]}; no suite/artifact gate")
    if runid == "FSU-FP04-F0-W5" and seed_n == 3:
        return ("PARTIAL",
                "certified suite 3/3: each suite seed counts as ONE seed "
                "(5 PolyBench component runs per seed, never added to seed "
                "totals); workbook W5 submodel coverage is still partial")
    if runid == "FSU-FP04-F0-W4":
        return ("PILOT_SUBMODEL_ONLY",
                "pilot covers FP04-c/mant_lo/W4/F0 only; workbook RunID "
                "requires FP04-a sign, FP04-b exp_hi/lo, FP04-c mant_hi/mid/lo, "
                "FP04-d NEON lane result, plus F1/F2/F3 semantics")
    if runid == "FSU-FP04-F0-W1":
        if seed_n:
            return ("PARTIAL",
                    f"official seeds {seed_n}/3 admitted under B0-core with the "
                    "real W1 FP-ScalarProbe; decoded FP32 scalar instructions "
                    "only (sign bit). The workload exercises FP64, special "
                    "values, four rounding modes and FPSR/FPCR, but those are "
                    "not injected per seed")
        return ("PARTIAL",
                "real W1 FP-ScalarProbe artifact and golden exist; this "
                "RunID has 0/3 official seeds")
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


def _f5_readiness(runid, seed_n):
    """F5 readiness is orthogonal to audited_status and seed_completion."""
    if runid == "FSU-FP06-F5-W3":
        return "COMPLETE_3_OF_3" if seed_n == 3 else f"PARTIAL_{seed_n}_OF_3"
    if runid == "FSU-FP06-F5-W1":
        return "COMPLETE_3_OF_3" if seed_n == 3 else "GATE_NOT_COMPLETE"
    if runid.startswith("FSU-FP06-F5-"):
        return "COMPLETE_3_OF_3" if seed_n == 3 else "NOT_RUN"
    if runid == "FSU-FR03-F5-W3":
        return ("COMPLETE_3_OF_3" if seed_n == 3
                else f"PARTIAL_{seed_n}_OF_3")
    if runid in ("FSU-FR03-F5-W5", "FSU-FR03-F5-W6"):
        return "COMPLETE_3_OF_3" if seed_n == 3 else "NOT_RUN"
    if runid.startswith("FSU-FR03-F5-"):
        return "BLOCKED"
    return None


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

    # 磁盘权威 seed 状态（AUTHORITATIVE + audit.ok；suite 只计 1）一次扫描。
    seed_map, seed_summary, seed_scope = _seed_state_map(out_root, rids)

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
            if model.startswith("FP"):
                activation = ("注入动作与 FSU_PROP L0–L5 已落地（FPU 路径）；"
                              "activated 需该 RunID 的真实 consumer/commit 见证")
            else:
                activation = ("注入动作可施加，但该模型尚无 FSU_PROP 事件；"
                              "activated 不能由正式链证据定义")
        elif audit["status"] == "MISSING":
            activation = "该 RunID 的注入动作尚不存在，activated 不可定义"
        else:
            activation = "—"
        seed_row = seed_map[rid]
        seed_n = seed_row["admitted_seeds"]
        coverage_status, coverage_reason = _coverage(
            rid, audit["status"], wl["identity"], seed_n, model=model)
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
            "test_status": (f"已有 {len(status['model_level_tests'])} 个 FSU "
                            "测试文件（编排/链/rate/F5/vec-stuck）；30 模型"
                            "逐模型行为测试未齐全"),
            "three_seed_status": f"{seed_n}/3",
            "seed_completion": f"{seed_n}/3",
            "seed_completion_count": seed_n,
            "seed_completion_source": ("fsu_index.scan: AUTHORITATIVE + "
                                       "audit.ok; W5 suite seed counts 1"),
            "seed_states": {str(s): v.get("state")
                            for s, v in seed_row["seeds"].items()},
            "f5_readiness": _f5_readiness(rid, seed_n),
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
        # 代码/测试存在性与正式 seed 认证严格分开记录。
        "capability_evidence": probe_capability_evidence(seed_map),
        "seed_index": {
            "admitted_seeds_total": seed_summary["admitted_seeds_total"],
            "target_seeds": seed_summary["target_seeds"],
            "suite_seed_dirs": seed_summary["suite_seed_dirs"],
            "suite_seed_admitted": seed_summary["suite_seed_admitted"],
            "component_runs_in_admitted_suites":
                seed_summary["component_runs_in_admitted_suites"],
            "seed_completion_counts": seed_summary["seed_completion_counts"],
            "active_admitted_seeds": seed_scope["active_admitted_seeds"],
            "active_seed_target": seed_scope["active_seed_target"],
            "active_complete_runids": seed_scope["active_complete_runids"],
            "active_runids": seed_scope["active_runids"],
        },
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
        "f5_readiness_counts": dict(Counter(
            m["f5_readiness"] for m in matrix if m["f5_readiness"])),
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
                     f"(F0-W3 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W3'), 0)}/3)",
                     "FP04-a sign: FP32 scalar sign only "
                     f"(F0-W1 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W1'), 0)}/3, B0-core)"]
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
                "W1": "REAL; W1 FP-ScalarProbe "
                      f"F0-W1 {next((m['seed_completion_count'] for m in matrix if m['runid'] == 'FSU-FP04-F0-W1'), 0)}/3 "
                      "(B0-core, FP32 scalar sign only)",
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
              "three_seed_status", "seed_completion", "seed_completion_source",
              "f5_readiness", "coverage_status", "coverage_reason", "pilot",
              "remaining_gaps", "baseline_blockers", "blockers"]
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
             "FP32 与 NEON 全 lane（FP04-d）缺失。FP04 的 FSU PROP 发射端与 F0/F5 传播链已落地，"
             "并已有正式 seed；但子模型覆盖仍不完整。FR01 仍无 FSU PROP 链，不能直接进入"
             "三 seed 执行。", "",
             f"- 磁盘权威 seed 索引：历史全量 {summary['seed_index']['admitted_seeds_total']}/"
             f"{summary['seed_index']['target_seeds']}，活跃 F0/F5 "
             f"{summary['seed_index']['active_admitted_seeds']}/"
             f"{summary['seed_index']['active_seed_target']}；suite seed "
             f"{summary['seed_index']['suite_seed_admitted']} 个对应 "
             f"{summary['seed_index']['component_runs_in_admitted_suites']} 个 component run"
             "（component 不计 seed）。", "",
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
    lines += ["", "## 2.2 F5 RunID readiness（代码能力与正式认证分开）", "",
              "| RunID | f5_readiness | seed_completion | 说明 |",
              "|---|---|---|---|"]
    for m in matrix:
        if m["f5_readiness"]:
            lines.append(f"| {m['runid']} | {m['f5_readiness']} | "
                         f"{m['seed_completion']} | {m['coverage_reason']} |")
    lines += ["", "## 2.3 capability_evidence（静态代码/测试探测，不等于认证）", "",
              "| 模型 | 能力 | code_present | certified | 证据 |",
              "|---|---|---|---|---|"]
    for group, caps in summary["capability_evidence"].items():
        if not isinstance(caps, dict):
            continue
        for name, c in caps.items():
            if not isinstance(c, dict):
                continue
            ev = "; ".join(c["evidence"])
            lines.append(f"| {group} | {name} | {c['code_present']} | "
                         f"{c['certified']} | {ev}；{c['certification']} |")
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
              "不是 FP04 全子模型，也不是 F1/F2/F3）。", "",
              "**FSU-FP04-F0-W5**（PolyBench suite：gemm/2mm/lu/cholesky/jacobi-2d）"
              "已完成 3/3 suite seed：每个 suite seed 的 5 个 component run 只计 "
              "1 个 seed；2mm 已 vendored 且 gate PASS。", "",
              "**FSU-FP06-F5-W3**（FP06-a SA0 / FP06-b SA1 / FP06-c fixed "
              "mantissa）已完成 3/3：每 seed 16,384 exposures、audit/certified "
              "全过；仅认证结果侧代理的 a/b/c，FP06-d partial-product proxy "
              "仍 MISSING。", "",
              "- 已解决的全局能力见 3.3；仍缺的能力见 3.4。", "",
              "## 6. 诚实边界", "",
              "- 本表不把“不支持/未激活/缺观测字段”记为 Masked；三 seed 状态"
              "以磁盘 AUTHORITATIVE + audit.ok 为准，不手写。",
              "- 工作簿声明状态与代码审计状态分列；未观测到的运行时行为标 UNVERIFIED。",
              "- capability_evidence 的 code_present 只表示静态代码/测试存在，"
              "不等于正式认证；certified 只来自磁盘审计通过的正式 seed。",
              "- gem5 二进制与正式 seed 状态由 current_status / seed_index 实测；"
              "FR03-F5 保持 PARTIAL/BLOCKED。", ""]
    (OUT / "IMPLEMENTATION_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[matrix] {len(matrix)} RunID；模型状态 {summary['model_status_counts']}；"
          f"RunID 状态 {summary['runid_status_counts']}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_MATRIX.json'}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_MATRIX.csv'}")
    print(f"[matrix] 写出 {OUT/'IMPLEMENTATION_AUDIT.md'}")


if __name__ == "__main__":
    write_outputs(*build())
