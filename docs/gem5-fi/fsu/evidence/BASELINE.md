# FSU 基线构建与 smoke 证据（2026-11-02）

## 1. 构建 A（默认 Python 3.8，**不可用**）

| 项 | 值 |
|---|---|
| tag | `20261102T120626` |
| 命令 | `scons -j4 build/ARM/gem5.opt`（默认 python3-config） |
| 开始/结束 | 2026-11-02T12:06:26 / 2026-11-02T14:06:50 |
| 退出码 | 0 |
| 元数据 | `build-20261102T120626.meta.txt`（SHA-256 `f2dc2054abbef931cc42bdec4ce4312941eca2d64a168ed9a7c9156209cc1c9c`） |
| 日志 | `build-20261102T120626.log`（SHA-256 `05cedf168b9ea3a16a178d3df928d18326f3d2c5f17befbc2f6c321f60798e34`） |
| 二进制 SHA-256 | `de5cba558c25c16887130f70e77befb5a8b570a2d3319f8f212cbff703d6d720` |
| 二进制大小/mtime | 1233285056 / 2026-11-02 14:06:43 |
| 嵌入 Python | `PYVER 3.8.18` |
| 结论 | **不可用于运行**：`configs/se/ooo_proxy.py` 导入 gem5 stdlib 时触发 `TypeError: unsupported operand type(s) for |: 'type' and 'type'`（PEP 604 需 Python ≥3.10）。该二进制已被构建 B 覆盖，仅保留元数据证据。 |

## 2. 构建 B（Python 3.11，**权威基线**）

| 项 | 值 |
|---|---|
| tag | `20261102T140829` |
| 命令 | `PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j4 build/ARM/gem5.opt` |
| 开始/结束 | 2026-11-02T14:08:29 / 2026-11-02T15:43:48 |
| 退出码 | 0 |
| 元数据 | `build-20261102T140829.meta.txt`（SHA-256 `6df234970135a716a4f164c821301682d9c2d9eb53eea9a5f5b240f62c5fabd4`） |
| 日志 | `build-20261102T140829.log`（SHA-256 `04c43f9fbfc0ef3071555eb0beab81be758fc9872fce811d8857e1c2da5caf87`） |
| 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `deab9936abbb5e3b0da4e8a0bdd3ed716d9c689c3c10c223ed0b80b887ff3060` |
| 二进制大小/mtime | 1245781408 / 2026-11-02 15:43:40 |
| 嵌入 Python | `PYVER 3.11.9 (main, Oct 26 2026, 18:37:14) [GCC 10.3.1]`（实测） |
| 工具链 | gcc/g++ 10.3.1；SCons 4.11.1；SCons 解释器 Python 3.8.18；嵌入 Python 3.11.9 |
| 源码 HEAD | `2f65a647a00f057b7cf74c3443af53d08f10a594`（构建时 fsu HEAD） |

## 3. Baseline smoke / golden（无注入）

工作负载：`workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`）。

命令（run1 与 run2 相同，仅 outdir 不同）：

```
CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/baseline_smoke/run<N> \
  configs/se/ooo_proxy.py --cmd workloads/directed/elemwise_fma_kernel --cpu O3
```

| 项 | run1 | run2 |
|---|---|---|
| 退出码 | 0 | 0 |
| ARRAYHASH | `ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7` | 同左 |
| ULP | 0 | 0 |
| simSeconds | 0.000232 | 0.000232 |
| simTicks | 232472625 | 232472625 |
| simInsts | 842114 | 842114 |
| stdout SHA-256 | `457c78dcbd899dfa4eb314e9ae7c7e62df07c3b239e4339933dfc0205adae068` | 同左 |
| stderr SHA-256 | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` | 同左 |

两次运行 `ARRAYHASH`/`ULP` 与 stdout/stderr 哈希完全一致；golden 与
`tools/runner.py` 的 `elemwisefma-golden-v1` 一致。

原始文件：`docs/gem5-fi/fsu/evidence/baseline_smoke/run{1,2}.{out,err}`、
`run{1,2}-stats.txt`（SHA-256 见 `sha256sum` 输出/提交历史）。

## 4. 已知配置差异（未掩盖）

- `configs/se/ooo_proxy.py` C3 默认：4-wide、ROB=128、IQ=64、physInt=128、
  physFloat=192、physVec=48、2.6 GHz。
- FSU 工作簿 B0：ROB=40、IQ=32、fetch/decode/rename=3/3/3、
  dispatch/issue/writeback/commit=8/8/8、physFloat=192、physVec=48。
- 本 baseline smoke 与后续 pilot 使用 C3 默认；B0 参数化是后续实现项，
  不在本证据中冒充已实现。

## 5. 结论

- 权威运行二进制：`deab9936abbb5e3b0da4e8a0bdd3ed716d9c689c3c10c223ed0b80b887ff3060`。
- 无注入 golden 可复现；可作为 FP04 pilot 的基线。
- 尚未运行任何注入/seed；真实计数仍为 0/173 RunID、0/519 seed。
