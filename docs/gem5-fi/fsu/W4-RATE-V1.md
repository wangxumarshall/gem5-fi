# W4-rate-v1：W4/FMA-DotProduct 的确定性 ROI 扩展（D2）

> 生成时间：2026-11-02。本文所有数值来自本机真实运行。
> 本版本只完成 workload/golden/census/预注册 ordinal；**未启动任何正式
> F1/F2/F3 三 seed 运行**。

## 1. 身份与关系

| 项 | 短 W4（保留不动） | W4-rate-v1（新增） |
|---|---|---|
| 身份 | W4 / FMA-DotProduct | W4 / FMA-DotProduct（版本 W4-rate-v1） |
| 源码 | `workloads/directed/elemwise_fma_kernel.c` | `workloads/directed/elemwise_fma_kernel_rate_v1.c` |
| 源码 SHA-256 | `7d24eb75d5dd0f10a32821739bb6ce78b9e0450961e59d5fdef4ae2849699d9d` | `e63dbcf7ce881b34078ef713281823f1ecc2e7d04cf79ecbb1c4be37201ac2c0` |
| 二进制 | `workloads/directed/elemwise_fma_kernel` | `workloads/directed/elemwise_fma_kernel_rate_v1` |
| 二进制 SHA-256 | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |
| 元素 N | 8192 | 262144（N_BASE=8192 × REPEAT=32） |
| golden ARRAYHASH | `ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7` | `e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba` |
| 实测 eligible_total | 57,347 | **2,097,155** |

- 未覆盖短 W4 二进制；两者并存，golden 与 SHA-256 各自独立。
- FP 操作不变：FP64 `c[i]=a[i]*b[i]+d[i]`，golden/check 双遍，ARRAYHASH + ULP。
- 输入 LCG 从同一常量 `0x243F6A8885A308D3` 连续生成；只依赖 N。
- 输出额外打印 `W4RATEV1 N=262144 REPEAT=32` 作为身份行。

## 2. 源码与构建

构建命令（host aarch64，与短 W4 相同工具链）：

```bash
gcc -O2 -static -DN_BASE=8192 -DREPEAT=32 \
    -o workloads/directed/elemwise_fma_kernel_rate_v1 \
    workloads/directed/elemwise_fma_kernel_rate_v1.c
```

- 产物：ELF 64-bit LSB executable, ARM aarch64, statically linked。
- 大小：634,848 bytes。
- ROI 参数：`N_BASE=8192`、`REPEAT=32`、`N=262144`、jitter 目标 ±50%。
- 选择依据：D1 结论 F1 首个间隔下界 500,000；±50% 时首个间隔最大
  1,500,000，因此目标 N ≥ 1,500,000。本版实测 2,097,155，留 40% 余量。
  没有根据任何 seed 结果反向调参。

## 3. 无注入 golden（连续 3 次）

命令（三次仅 outdir 不同）：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet -d /tmp/w4rate_golden/run<N> \
  configs/se/ooo_proxy.py --cmd workloads/directed/elemwise_fma_kernel_rate_v1 \
  --cpu O3
```

| run | 退出码 | ARRAYHASH | ULP | simSeconds | simInsts | hostSeconds | wall | maxRSS |
|---|---|---:|---|---:|---:|---:|---:|---:|
| 1 | 0 | `e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba` | 0 | 0.009415 | 28,842,716 | 201.63 | 3:24.09 | 114,952 KB |
| 2 | 0 | 同上 | 0 | 0.009415 | 28,842,716 | 205.22 | 3:27.57 | 114,932 KB |
| 3 | 0 | 同上 | 0 | 0.009415 | 28,842,716 | 222.60 | 3:45.03 | 114,852 KB |

- 三次 stdout 逐字节一致：SHA-256 `0b81fa1b4782b87a4301fb7eface32d15be38f2b8d90facba9a841064b11ede6`。
- 三次 stderr 逐字节一致：SHA-256 `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8`。
- golden（无注入）ARRAYHASH 三次一致，ULP=0。

## 4. eligible census（countOnly 实测，不作线性推测）

命令：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet -d /tmp/w4rate_census \
  configs/se/ooo_proxy.py --cmd workloads/directed/elemwise_fma_kernel_rate_v1 \
  --cpu O3 --chaos_fpu --fpu_count_only --fpu_first_clock 0 \
  --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c
```

| 项 | 实测 |
|---|---:|
| `CHAOS_ELIGIBLE_COUNT` | **2,097,155** |
| 退出码 | 0 |
| simSeconds | 0.009415 |
| simInsts | 28,842,716 |
| hostSeconds | 229.87 |
| wall | 3:52.42 |
| maxRSS | 115,024 KB |

> 注意：2,097,155 不是按 57,347×32 推算（线性推算为 1,835,104）；
> 该差异来自真实 countOnly 计数，本文只记录实测值。

## 5. 预注册 F1/F2/F3 ordinals（seed1/2/3）

文件：`configs/fsu/W4-rate-v1-ordinals.json`
文件 SHA-256：`1df384749d9d97095e1f259d67555871e80344708733597da40cbccd2c3e3924`

| 档位 | seed | 注入数 | 首 ordinal | 末 ordinal | ordinals SHA-256 |
|---|---|---:|---:|---:|---|
| F1 | 1 | 1 | 1,394,471 | 1,394,471 | `b8e80e065b4cbe2352f85fc0ca092e625ddb190aa44e5b1d0e2f67f7fc3ef892` |
| F1 | 2 | 2 | 1,027,869 | 1,716,133 | `b751d246742d462a57fed2e6f8f897783babdbe153761aae87bba2691b10e2dc` |
| F1 | 3 | 1 | 1,306,838 | 1,306,838 | `39e0b89571c30645f0ee14a5f53a3a59230f2422480007513230a67de8e2ccaa` |
| F2 | 1 | 21 | 91,644 | 2,094,621 | `1ef3a0a61e16a6e086a5788f3f6ef2e86e6cc0abe0dca98794e18ef2cf80a1a2` |
| F2 | 2 | 22 | 82,214 | 2,058,002 | `783007882a6f784e997d4a738226baf681326427b0312d2192e8286b0ea6c01c` |
| F2 | 3 | 19 | 115,872 | 2,028,008 | `097afed3c24e7d8d23913ed61faa968d3628fa76b6c4bedb41a3f774456629f3` |
| F3 | 1 | 206 | 11,004 | 2,091,182 | `5ed393fc2e10184bf912e82c33ec762680aab236cb33288cb0e2d59753b15397` |
| F3 | 2 | 202 | 10,298 | 2,085,278 | `8c317216bd3f6cb57a95091694427889adf7f00f83cd9b190c89429c97a9282d` |
| F3 | 3 | 210 | 5,409 | 2,088,070 | `15d4a409c3d807aab196116acf1b7a7b027fc1959075d07b70db4bcb502d99ca` |

生成器：`splitmix64-mod-uniform-interval` v1；interval 闭区间
[ceil(0.5·rate), floor(1.5·rate)]；ordinal 为累加值，严格递增、无重复。

## 6. 官方 manifest

| RunID | manifest SHA-256 |
|---|---|
| `FSU-FP04-F1-W4` | `aa2115145f630ad6aa4143115a71906c7c6118353cd0fa3b8fc61b969e062eb3` |
| `FSU-FP04-F2-W4` | `47ca4ca9d0dcace4620b6f07055371c78886b9bffab8a1029616bc7d1c2f0a12` |
| `FSU-FP04-F3-W4` | `7eafb3e46a1c0e5a59bfed35ab545aa263e42e6a5c511c4887d968ff430a1d7a` |

三个 manifest 均指向 W4-rate-v1、rate divisor 1e6/1e5/1e4、jitter 50、
warmup 0，`load_id` 仍为 W4（同一 workload 身份，版本 W4-rate-v1）。

## 7. 诚实边界

- 本文（D2）生成时没有运行任何正式 F1/F2/F3 seed。**D3 更新（2026-11-02）**：
  已正式运行 `FSU-FP04-F3-W4` seed1（`.../seed1/attempt-1`，206/206 fault）、
  seed2（`.../seed2/attempt-1`，202/202 fault）与 seed3
  （`.../seed3/attempt-1`，210/210 fault），逐 fault `full`，三次 audit 均 PASS；
  另已运行 `FSU-FP04-F2-W4` seed1（21/21）、seed2（22/22）与 seed3（19/19），
  均 audit PASS。当前 seed 完成数为 **9/519**；F2-W4 与 F3-W4 均为 3/3。
  F1 仍未运行。
- F3 机制门禁使用**短 W4**（N=57,347），不是本文件的大 workload；其证据
  单独保存在 `runs/fsu-gates/`。
- 运行时与资源为同机、同 gem5 二进制的单次实测，不是承诺值。
- 二进制/源码/golden/ordinals 的 SHA-256 均已记录；若任一文件变化，
  必须重新生成 golden 与预注册 ordinals，不能沿用旧值。
