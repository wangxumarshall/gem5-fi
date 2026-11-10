# 上游 D13 真基线在 sdc-0103 的复现

本文记录**上游 sdcfuzz 的真 D13**（不是本仓库的本地启发式）在真实 ARM
服务器 `sdc-0103` 上的复现结果。目的有两个：把上一轮“本地重建冒充 D13”
的口径纠正为可核验的外部基线，并为后续 RL/变异研究提供一个真实的对照臂。

## 1. 结论

在 `sdc-0103` 上用上游 `exp02_d13_vs_random` 的同一协议重跑 D13 vs B
（随机基线），每组 100 次、seed 42、最多 3 路并行：

| 模式 | B（随机） | D13（上游） | D13/B | Fisher p | 判定 |
|---|---|---|---:|---:|---|
| bit-flip | 6/100 = 0.06 | 17/100 = 0.17 | **2.833×** | **0.0249** | BEAT（≥1.5× 且 p<0.05） |
| structural | 5/100 = 0.05 | 64/100 = 0.64 | **12.800×** | **5.63e-20** | BEAT |

原始实验（`output/experiments/exp02-d13-vs-random/summary.json`，同一台
0103）为 bit 7/100 vs 22/100（3.143×，p=0.00429）、struct 5/100 vs 64/100
（12.8×，p=5.6e-20）。

- **structural 模式逐项一致**：B 5/100、D13 64/100，与原始实验完全相同；
- **bit 模式方向与量级一致、数值偏低**：B 6 vs 7，D13 17 vs 22，2.833× 对比
  原 3.143×；差异原因见第 5 节，不做掩饰。

因此可以确认：**D13 相对随机基线的优势是可复现的**，结构化故障模式下
几乎逐位复现；bit-flip 模式下复现到 2.8×（仍显著高于预注册的 1.5× 判定线）。

## 2. 环境（真实机器）

| 项 | 值 |
|---|---|
| 主机 | `sdc-0103`（内网 172.168.59.158；外网经 123.60.114.33:33457 登录） |
| 架构 / 核数 | aarch64 / 128 |
| 系统 / 编译器 | openEuler 24.03（内核 5.10 系列），gcc 12.3.1 |
| 上游仓库 | `/home/sdc/wangxu/silifuzz`，origin `git@github.com:wangxumarshall/sdcfuzz.git`，HEAD `707db35d` |
| 上游 GitHub HEAD（复现时） | `4a7a21e018a05e8317ef221362224207d8b19327` |
| D13 workload | `gem5_config/workloads/sdc_probe_workload_d13.c`，sha256 `4143a4bd…67263`（与 GitHub HEAD 克隆逐字节一致） |
| 随机基线 workload | `gem5_config/workloads/sdc_probe_workload_random.c`，sha256 `fb461f72…61be`（同样一致） |
| gem5 | `~/wangxu/gem5-fi-fuzz/build/ARM/gem5.opt`（2026-09-08，v25.1.0.1，ARM target、x86/ARM 原生执行），软链到上游 `sdcfuzz` 期望的 `~/wangxu/gem5-fi/CHAOS/gem5/build/ARM/gem5.opt` |
| gem5 运行依赖 | `~/gem5-deps`（用户态解包 RPM，含 `env.sh`） |

注意：这是**真实 ARM 服务器上运行 gem5-CHAOS 模型**，不是硅片级故障注入。
“真机环境”在这里指真实硬件上跑真实工具链，而不是 WSL 里的模拟环境；
SDC 判定仍然是 gem5 O3 模型的注入结果（`gem5_note: not TSV110 RTL`）。

## 3. 复现步骤

在 `sdc-0103` 上（或通过 ssh 执行）：

```bash
cd ~/wangxu/silifuzz
for MODE in bit struct; do
  for G in B D13; do
    python3 tools/sdc_experiment/sim_sweep.py --group $G --mode $MODE \
      --runs 100 --seed 42 --exp exp02-d13-repro-20261110 --jobs 3
  done
done
```

随后用 `tools/sdc_experiment/sim_sweep.py` 的 `fisher_exact` 汇总，得到
`summary.json`（字段与上游 `scripts/experiments/exp02_d13_vs_random.sh`
一致，另加 `_reproduction` 元数据）。

每次 run 的 fault-clock 由 `Random(seed)` 在 dispatch 前抽定、`--rng-seed =
seed + i`，因此并行度不改变单次 run 参数（上游注释与实现一致）；本次
`--jobs 3` 遵守其“gem5 注入并行 ≤ 4”的 MCE 红线。

## 4. 结果明细

| 模式 | 组 | diverge | masked | no_output | Wilson 95% CI |
|---|---|---:|---:|---:|---|
| bit | B | 6 | 90 | 4 | 0.0278–0.1248 |
| bit | D13 | 17 | 76 | 7 | 0.1089–0.2555 |
| struct | B | 5 | 79 | 16 | 0.0215–0.1118 |
| struct | D13 | 64 | 32 | 4 | 0.5424–0.7273 |

`diverge` 是“干净发散”（程序正常结束但结果与 golden 不同，即 SDC）的计数；
`no_output` 是无输出/超时的那部分（未计入 diverged）。两组 `exit_diverge`
均为 0。

原始 JSON 与汇总在：

- 本仓库：`docs/sdcfuzz/d13-repro/sim_{B,D13}_{bit,struct}.json`、
  `summary.json`
- 板卡：`~/wangxu/silifuzz/output/experiments/exp02-d13-repro-20261110/`

## 5. 与原始实验的差异（诚实记录）

1. **bit 模式偏低**（17 vs 22）。原始实验只留下 `sim_*.json`，没有记录
   当时使用的 gem5 二进制；本次用软链指向 `~/wangxu/gem5-fi-fuzz/build/ARM/
   gem5.opt`（2026-09-08 构建）。bit-flip 的注入位点/RNG 交互对二进制与
   模型细节更敏感，而 structural（byte lane skew）更粗粒度，因此出现
   “struct 完全一致、bit 略低”的模式。这解释是推断，不能证明；下一次复现
   应同时归档 gem5 二进制的 sha256。
2. 原实验与本次都不是硅片结果；不能用它推断真实 Kunpeng 920 的 SDC 率。
3. 路线文档引用的“bit 3.00× / struct 7.79×”来自另一组对照（F4），与
   `exp02` 自己的 `summary.json`（3.143× / 12.8×）不是同一次实验；本文
   对齐的是 `exp02` 的原始产物。

## 6. 对后续工作的含义

- 本仓库的 `sdcfuzz/operand_heuristic.py` 与这组 D13 是**两个不同的东西**，
  不能互相替代；RL/变异研究若要声称“超过 D13”，对照臂必须是本文这条路线
  （上游 workload + 同一注入协议）。
- 下一步（Phase 2）可以在同一块 0103 上，把上游 D13 与新的变异策略放进
  同样的 `sim_sweep` 协议里跑 A/B，复用本文的 `--runs/--seed/--jobs` 与
  Fisher 判定，避免再出现口径不一致。
