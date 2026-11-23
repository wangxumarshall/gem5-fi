# 严格按原文的三代理语料与区域配对（2026-11-23）

本目录有两套配对方法，**不要混用**：

| 工具 / 证据 | 生成端 | 能得到什么 |
| --- | --- | --- |
| `tools/pairgen.py` → `evidence/pairs-2026-11-23/` | **定向**（限定词表、补表、按类均衡、寄存器分区、`--centered-data`） | 类覆盖 100% 的配对；但分布不是 SiliFuzz，属于本项目扩展 |
| `tools/pairgen_paper.py` → `evidence/pairs-paper-2026-11-23/` | **原文**（ifuzz 无过滤 + Capstone/Unicorn 代理 + 原样 fixer） | 同分布语料 + 可量化的区域重叠；单条流只能覆盖模板区域的一部分 |

结论要归因于 SiliFuzz 本身时用后者；前者只能作为"定向扩展"的对照。

## 生成端（零定向）

```bash
python3 tools/pairgen_paper.py corpus --work work/paper-YYYYMMDD \
        --ifuzz-n 80000 --cap-seconds 180 --uc-seconds 180
```

- `bin/ifuzzgen` 默认表（1212 条）均匀抽样，无任何过滤；
- `bin/capstone_fuzz` / `bin/unicorn_fuzz` 为 libFuzzer 目标，覆盖引导；
- `sf_fix` 默认 4 数据页、默认初态，`--ref-cores 0,32,64,96 --repeat 3`。

本轮：99,834 个候选 → 95,475 条快照（ifuzz 92,634 / Capstone 1,622 / Unicorn 904 /
无法按内容回查的代理短输入 315），接受率 95.6%；拒绝 2,990 `syscall`、1,336 `timeout`。

## 覆盖区域

两条轴，都取自代理自身：

1. `R(x) = ∪ F(w) − F(nop)`：`F(w)` 为插桩 Capstone 解码 `w` 时置位的 SanitizerCoverage
   计数器集合，由 `tools/covfingerprint/covdrv_capstone.cc` 读回（与代理同一套插桩）。
   代理每条输入只解码一条指令，故模板与流都按逐指令并集，比较对称。
2. 助记符：Capstone 对每个字给出的 mnemonic，决定流碰了哪些解码分支族。

**纯度** = 流助记符中属于模板的比例；**覆盖** = 模板助记符被走到的比例。

## 选流

(助记符纯度, 计数器精确率) 阶梯 1.00/0.95 → 0.90/0.90 → 0.80/0.90 → 0.80/0.80 →
0.70/0.70 → 0.50/0.50 逐级放宽；级内按覆盖率、区域共享数、长度接近度排序。
硬门：端态 PC 落在末尾 `BRK`。

## 结果（也是这套方法的上限）

- 20/20 配对成立、全部跑到末尾；流长 **2–4 条**（模板 15–81 条）；
  助记符纯度 0.67–1.00、覆盖率 0.12–0.50；计数器精确率 0.50–1.00。
- **满纯度下最长流只有 3–4 条指令**（在 95,475 条语料里全量枚举）；
  对应覆盖率上限 0.13–0.50。不要求纯度时，覆盖率上限也只有 0.36–1.00。
- 若干模板的助记符在 95,475 条语料里**极稀有或完全缺失**（按"含该助记符的快照条数"统计，
  含单指令快照）：o2 的 `b.ne` **0** 次；v1/v6 的 `dup` 各 **15** 次；
  v5 的 LSE 只有 `casa`/`casal`/`ldadd` 各 **1** 次，`ldadda`/`ldaddl`/`swp`/`swpal` 为 **0**。
  也就是说这些区域"能到但稀有到凑不出两条以上且在区域内"的流。
- 20 条流里只有 3 条不与其他模板共享区域：短流用的都是 `movk/eor/ldr` 这类通用指令。
- 机群：128 核 sweep 2,560 次、50/1000 采样 3,407,260 次、4 核窗口 2×60 s，0 不匹配。

## 为什么覆盖率上不去

模板 4–16 个助记符，ifuzz 表约 400 个。n 条指令全落在模板助记符集内的概率约 p^n
（p≈0.1–0.3）；n=10 已是 1e-5–1e-6，n=30 基本不可能。要"长流且不出圈"，
只能给生成器加约束——那就是 `pairgen.py`，而它不再是原文。

## 复现

```bash
python3 tools/pairgen_paper.py corpus  --work work/paper-YYYYMMDD \
        --ifuzz-n 80000 --cap-seconds 180 --uc-seconds 180
python3 tools/pairgen_paper.py regions --work work/paper-YYYYMMDD --operate-purity 0.8
python3 tools/pairgen_paper.py verify  --work work/paper-YYYYMMDD --cores 0-127
python3 tools/pairgen_paper.py report  --work work/paper-YYYYMMDD --copy-to <dir>
```

`--reuse-corpus` 可在修复已完成后只重建索引（不重跑生成与修复）。

## 边界

- 区域是**解码路径**口径，不含执行轨迹与微架构结构（译码宽度、发射端口、缓存）。
- Unicorn 侧覆盖率被 TCG/派遣代码主导（任意输入约 1346 个计数器），仅作辅助。
- 原文用 XED + Centipede，本仓库用 Capstone + libFuzzer（`docs/paper-mapping.md`）。
- 未跨微架构验证。

完整叙述见 `~/sdc-mhw-docs/docs/sdcfuzz/sdcfuzz-silifuzz-pairs-paper-2026-11-23.md`。
