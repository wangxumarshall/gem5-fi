# 试点 RunID `FSU-FP04-F0-W4`：三 seed 完成报告（3/3）

> 生成时间：2026-11-02；本文所有数值来自本机真实运行与逐 seed 审计。

## 1. 结论

- RunID：`FSU-FP04-F0-W4`（FP04 / F0 / W4）。
- 模型：FP04（FSU Pipe 结果位翻转，子模型 FP04-c = mantissa；本试点注入 `mant_lo`）。
- 工作负载：`workloads/directed/elemwise_fma_kernel`（REAL 产物，ARRAYHASH/ULP golden）。
- 三个独立 seed 全部 admitted，逐 seed 审计 `ok=true, failures=[]`。
- **该 RunID 达到 COMPLETE_3_OF_3**；其余 172 个 RunID 仍为 0/3；总计 3/519 合格 seed。

## 2. 身份

| 项 | 值 |
|---|---|
| 源码 HEAD | `8e86d1ba0421741f96bd5986da7a4cdb9dae48a7` |
| gem5 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `f9a7cd9b4de6a47dbaceaa4dac0b58bbf8ba5bbbe8f1c8241a9e71be7af98c32` |
| 构建 | `PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j4 build/ARM/gem5.opt` |
| 最终发射端构建 tag | `20261102T161607`（exit 0；前一发射端构建 `20261102T155856` 用于字段修正验证） |
| 嵌入 Python | 3.11.9 |
| workload SHA-256 | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 3. 三 seed 结果

| seed | attempt | eligible | skip | 根 tick | 根 sn | 根 PC | phys | before → after | mask | terminal | layers | L5 | oracle | audit |
|---|---|---:|---:|---:|---:|---|---:|---|---|---|---|---|---|---|
| 1 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2` | 57347 | 45070 | 80411485 | 281328 | `0x00000000004005e0` | 6 | `0x4080580000000000` → `0x4080580000000020` | `0x0000000000000020` | full | L0,L1,L2,L3,L4,L5 | 5 | SDC | PASS |
| 2 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed2/attempt-1` | 57347 | 13908 | 33769120 | 94347 | `0x00000000004005ec` | 32 | `0x3fe25604189374bc` → `0x3fe256041893f4bc` | `0x0000000000008000` | full | L0,L1,L2,L3,L4,L5 | 5 | SDC | PASS |
| 3 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed3/attempt-1` | 57347 | 19337 | 41840645 | 126926 | `0x00000000004005e8` | 6 | `0x408db00000000000` → `0x408db00000004000` | `0x0000000000004000` | full | L0,L1,L2,L3,L4,L5 | 5 | SDC | PASS |

## 4. 证据哈希与位置

| seed | prop_evt SHA-256 | chain_report SHA-256 | seed MD SHA-256 |
|---|---|---|---|
| 1 | `18fab2087555ee3260ce76dc9226aebaa9c5089b3a4e28791478514dc536c706` | `5c73e7fbda73b1bbcfbefcdd8c1bc8cae818d4d420e8327b17ea40617eccbe44` | `bfe6e8d50ec70bf2041b5129b84cb88a003fb88235a337129d8d4d290f6fb101` |
| 2 | `fc5ca226fac390fde8425e87dbb9abf78b164f94c344a5ea4586c56180eb8cb7` | `b338b479c67861450c3b6bd007220082914d8de4039248137a54ca7e2e762638` | `073bd54c0c339998bdf6728b1caab619e929c148a325655dbebb67ced97bfbe4` |
| 3 | `627228f14370648e6fc60c213d1cb839c6f7fe832769b7dddef7d9cf76092d6a` | `3dab47a6a569818a710e87966b1f2b1cdd7072fd67ce20e37c4f03a06784a66a` | `c8caf264fb440916c28b1cca9f133cca73ad29936e00facd3e4a65432812e7c6` |

权威 Markdown：

- `runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W4/FSU-FP04-F0-W4-seed1.md`
- `runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W4/FSU-FP04-F0-W4-seed2.md`
- `runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W4/FSU-FP04-F0-W4-seed3.md`

原始证据目录：

- `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2/`（manifest.json、census/、inject/、run.out、run.err、stats.txt、oracle.json、chain_report.json、evidence_sha256.json）
- `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed2/attempt-1/`（manifest.json、census/、inject/、run.out、run.err、stats.txt、oracle.json、chain_report.json、evidence_sha256.json）
- `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed3/attempt-1/`（manifest.json、census/、inject/、run.out、run.err、stats.txt、oracle.json、chain_report.json、evidence_sha256.json）

## 5. 独立性

- 三个 seed 的 selection/injection seed 分别为 1/2/3，`skip` 分别为 45070/13908/19337。
- 根事件 tick 分别为 80411485/33769120/41840645，sn、PC、phys reg、before/after、mask 均不同。
- 每份 `prop_evt.txt.gz`、`chain_report.json`、seed Markdown 的 SHA-256 均不同；
  所有事件的 `run_id`/`sample_run_id` 与所属 seed 一致（审计已逐条校验）。
- seed1 的 attempt-1 因 `unit`/`fault_mask` 字段问题被保留为历史 lineage；
  attempt-2 是 AUTHORITATIVE（问题修复后重跑，原始 attempt-1 未被覆盖）。

## 6. 门禁 1–10

| # | 门禁 | 结果 | 证据 |
|---|---|---|---|
| 1 | 无注入 golden | PASS | `docs/gem5-fi/fsu/evidence/BASELINE.md`：ARRAYHASH=ced113…f43e7、ULP=0，两次一致 |
| 2 | eligible/count-only 普查 | PASS | census `CHAOS_ELIGIBLE_COUNT=57347` |
| 3 | 单次故障注入 | PASS | 每个 seed `faults_injected=1`、根事件唯一 |
| 4 | attempted/eligible/activated 可区分 | PASS | 1 / 57347 / 1；activated 只认 L2 真实消费 |
| 5 | 注入日志 ↔ 根事件 | PASS | `fpu_injections.log` 的 tick/sn 与根事件一致 |
| 6 | 同一 manifest 可重放 | PASS | seed2 重放：PROP-EVT 逐字节相同，ARRAYHASH 相同 |
| 7 | 原始事件流完整非截断 | PASS | gzip EOF 完整，`truncated=false` |
| 8 | checker/chain report | PASS | `terminal=full`、`admitted=true`、`violations=[]` |
| 9 | 单 seed Markdown | PASS | 三份十节 Markdown，审计逐行 parent/kind 校验 |
| 10 | 审计器发现伪造/缺事件/错误终局/跨 seed | PASS | `tests/test_fsu_seed_audit.py` 7 项负向测试 + 本次审计 |

## 7. 诚实边界

- 仅 `FSU-FP04-F0-W4` 达到 3/3；**其余 172 个 RunID 未启动**，总计 3/519 seed。
- FP04 仍是部分覆盖：仅 FP64 低 64 位结果字段；FP32 字段与 NEON 全 lane（FP04-d）未实现。
- 当前使用 `ooo_proxy.py` C3 默认（ROB=128/IQ=64/4-wide）；工作簿 B0（ROB=40/IQ=32/3-wide/8-8-8）尚未参数化。
- gem5 是功能级模型；本结果不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不占 L0–L5；L5 见证是真实 `commit/errant_commit` 事件（event_id=5）。
- 三个 seed 是独立运行与独立原始证据；没有跨 seed/跨 RunID 复制。
