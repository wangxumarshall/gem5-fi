# Phase 0 / Phase 1 文档符合性独立审计（2026-11-14）

- 审计依据：`sdcfuzz/sdcfuzz-v1.2.md` v1.2 的 §4.2、§5.1 与 §7
- 主机：`sdc-0103`（aarch64，128 核），gem5 `build/ARM/gem5.opt`
- 工作目录：`test_phase1_v1/`（`verify.py`、自建负载、`report.md`、`results.json`、
  `evidence/**`）。本文只做结论汇总，逐项证据在工作目录里。

## 口径

本次审计不读取仓库既有的验证文档，也不调用仓库测试脚本的断言：`verify.py`
自带微负载，自己跑 gem5、自己解析 `stats.txt`，并按 `CHAOS/gem5` 的计数定义
重算每个指标。唯一的“复用”是 `tools/autousens.py` 与
`scripts/test-template-coverage.py` 本身——它们是被审计对象，检查的是能否
工作，而不是引用其结论。

差分方法：RF/L1 用同二进制 n 与 2n 两档运行求每操作代价；IBR 用同形状
asm 环逐类运行后减 nop 基线。这样 prologue、循环开销与编译器噪声相互抵消。

## 结论：17 项中 12 PASS / 2 PARTIAL / 0 FAIL / 3 UNVERIFIABLE

### Phase 0

| 项 | 判定 | 实测 |
|---|---|---|
| D13 操作数启发式（上游） | PASS | 源文件含 4/4 启发式步骤；两次运行输出逐字一致（`SUM=118831515424667458 CRC=dbc8bf2a`） |
| 19 个种子模板 | PASS | 19 条存在；`alu-add-carry`/`mul64`/`l1d-load-stream` 真实运行，校验和与生成器期望一致 |
| gem5-CHAOS 注入 | PASS | 自建负载注入 1 次 bit flip，`numFaultsInjected=1`，fault log 落盘；该次命中被屏蔽 |
| 4 板 446 核部署 | UNVERIFIABLE | 本机无该集群，仓库无部署日志 |
| 论文 p2 草稿 | UNVERIFIABLE | 仓库不含草稿 |

### Phase 1

| 项 | 判定 | 实测 |
|---|---|---|
| RF ACE | PASS | 每 `add` 读 2.00、写 1.00；`intAceRatio=bitCycles/(physIntRegs×64×cycles)` 重算一致 |
| L1 ACE | PASS | 冷行 256 行：读 +256、填充 +253；热行：读 +256、填充 0；写 +256；比值重算一致 |
| FU IBR | PASS | 五类 2000 次：输入位 250688/383808/255872/256128/256000，与 `ports×64×n` 在 5% 内；`ibrRatio` 分母为 `units×ports×64×cycles`，重算一致 |
| 指令→结构映射 | PASS | 6/6 属性成立（`add` 只激 alu、`ldr` 只激 l1d 且 ≥0.5/指令、`fadd` 激 fpadd+vec）；两次运行逐位一致 |
| 映射结构范围 | **PARTIAL** | 文档列 8 类；实现 9 类但缺 **LSQ/ROB 的逐指令归因**、**TLB 完全没有** |
| 逆向靶向 | PASS | 自查 l1d 第一名 `ldr` = target 选择；候选 1.001 次 L1D 激活/指令 |
| ISA 合法性约束 | **PARTIAL** | 仅从 17 条固定片段组合，无 Microprobe 式约束求解器 |
| 跨结构联合优化 | PASS | `l1d+alu` Pareto size=6；knee `add,add,ldr,ldr` 实测净激活 l1d=1285、alu=162240 |
| 结构覆盖度评估 | PASS | 合成矩阵 6 状态 + 3 缺口与期望一致（含用计数器下限把 5 次 L1I 判为 `unobserved`）；真实 19 模板 19/9/9、无 `never_observed` |
| SAD | PASS | `usedSum/(samples×capacity)` 重算一致；容量 128/48/42 与 kp920 proxy 配置一致 |
| 确定性执行 | PASS | 同 guest 两次运行，RF/IBR 四计数器逐位一致 |
| seccomp 兼容 | UNVERIFIABLE | 无 snapshot/runner 链路，无法证明 |

## 与文档的三处实质差距

1. **结构范围**（§5.1）：文档要求逐指令记录 LSQ/ROB/TLB；实现用 SAD 的 ROI
   聚合替代 LSQ/ROB，TLB 无实现。映射是 9 类，不是文档列举的全集。
2. **ISA 约束**（§5.1）：文档要求 Microprobe 式约束系统；实现以固定片段表
   保证合法性，表达力限于 17 条片段。
3. **seccomp**（§5.1）：无执行链路，只能标未验证。

Phase 0 的两项不可验证属于环境/外部交付物，不影响本地实现判定。

## 方法学记录

第一版 RF 探针得出“每 add 读 3 写 2”的结论，原因是基线与实验的循环体被
编译器差异化优化。改为同一 asm 模板、只替换助记符后复测为 2 读 1 写——
说明探针本身也必须被证伪，这也是本次不引用既有测试结果的原因。

## 复现

```bash
cd ~/sdc-mhw
python3 test_phase1_v1/verify.py                  # 全量，约 8–10 分钟
python3 test_phase1_v1/verify.py --only P1.1,P1.2 # 单项
```

产物：`test_phase1_v1/report.md`（逐项证据路径）、`results.json`、
`evidence/**`（gem5 stats/log/二进制）。该目录不纳入 git，避免把 70 MB
运行产物塞进仓库；`verify.py` 与负载可随时重跑。
