# sdcfuzz vs SiliFuzz：随机故障注入对照

本目录是 `docs/sdcfuzz/silifuzz-vs-sdcfuzz-fi-2026-11-14.md` 的实验代码。

## 运行

```bash
cd ~/sdc-mhw
python3 fi_research/sdcfuzz_vs_silifuzz/fi_campaign.py --n 40 --jobs 8
```

- `--n` 每条流的注入次数；`--jobs` 并行 gem5 进程数（本机 8 安全，
  30 GiB 内存，单进程约 1.2 GiB）。
- 首次运行会解析 `silifuzz/work/corpus/ifuzz` 的 30k 条 snapshot，生成
  `work/snapshot_prefixes.json` 缓存；之后复用。
- 结果写到 `m5out/silifuzz-vs-sdcfuzz-fi/summary.{json,md}` 和
  `runs/<stream>/rNNN/`。

## 两条臂

- **sdcfuzz**：`sdcfuzz/generator.py` 渲染 `fp-add` / `fp-mul` 模板，
  3 组非饱和操作数，每条流 3600 条指令（3200 条 FP）。
- **silifuzz**：从 95,402 条固定 snapshot 中取 `pc → sig_addr` 的执行前缀，
  过滤为寄存器-only，拼接成 6 个 3600 指令块（每块 2323–2350 条 FP/SIMD）。

两臂共用同一个 guest harness（沙箱、m5 ROI、x0–x30+q0–q31+128 字数据的
FNV oracle），只有指令块不同。

## 注入

`CHAOSFPU`：每个 FP 源读按 p=0.001 注入一次瞬态 bit flip，`max_faults=1`，
`bit_segment=all`。整数寄存器注入（CHAOSReg / CHAOSPhysReg arch_*）在 O3
上被重命名旁路（本 harness 对照 12/12 Masked），因此没有纳入正式实验。

## 关键结果（n=40/流）

| 组 | 有效 | SDC | 率 | Wilson 95% CI |
|---|---:|---:|---:|---|
| sdcfuzz | 240 | 178 | 0.7417 | [0.6828, 0.7929] |
| silifuzz | 240 | 0 | 0.0000 | [0.0000, 0.0158] |

Fisher p = 3.83e-78；流级 6/6 vs 0/6，p = 0.00216。

## 复现注意

- 必须使用修复后的 harness：保存/恢复 x18–x30、SP、LR；否则 C 侧 oracle
  会被 ABI 污染，所有注入显示 Masked。
- 模板的 `ldrf/str` 用 x27 作为数据缓冲基址；harness 把 `g_in[27]` 固定为
  沙箱基址，否则 `--DDATA0/1` 不生效。
- fp-mul 默认 1.5×2.25 在 200 次迭代后溢出到 inf，SDC 被吸收；正式实验
  使用 1±ε 的非饱和乘数。
