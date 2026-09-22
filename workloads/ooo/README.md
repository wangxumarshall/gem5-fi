# workloads/ooo — OoO 北极星 W1 负载集

`docs/gem5-fi/ooo/`（OoO 微架构故障注入北极星）的 W1 负载建设目录。

- 执行计划：`docs/superpowers/plans/2026-09-23-ooo-w1-workloads.md`
- 负载定义与校验方式（冲突以它为准）：`docs/gem5-fi/ooo/03-workloads.md`

## 组织方式（仿 workloads/directed/：源码 + 静态 ELF 并存入库）

- 每个负载一个子目录：`<name>/<name>.c`（源码）与 `<name>/<name>`（构建产物，静态链接
  AArch64 ELF，宿主原生 gcc `-O2 -static`，无需交叉工具链）。
- 构建：`make -C workloads/ooo`（全部）或 `make -C workloads/ooo <name>`（单个）；
  新负载落库时在 Makefile 的 `WORKLOADS` 列表（或显式规则）中登记。
- 输出惯例：自设核打印一行 `FINAL=<16hex>`（`tools/classify.py` 的 `_CHECKSUM_RE`，
  与 directed/ v1.1+ 内核同款格式）。无注入运行的 FINAL 值即该负载 golden，
  注册进 `tools/runner.py` 的 `GOLDEN_IDS`。

## SE 预算纪律（W1 Global Constraints，硬门）

- **每个负载在 C3 SE（`build/ARM/gem5.opt --outdir=<dir> configs/se/ooo_proxy.py
  --cmd workloads/ooo/<name>/<name> --cpu O3`）下的 `stats.txt` `hostSeconds`
  实测必须 ≤ 60 s**；超预算 = 缩规模重测，不算完成。
- **golden 稳定**：同一 ELF 两次 gem5 运行 FINAL 行逐字节一致，且与宿主原生运行
  一致（native == gem5，确定性）。
- 事件密度（`tools/event_density.py`）实测入档；探针核另有密度门
  （branch_mispred ≥5% mispredicts/commits、dep_chain flIntLe8/flVecLe6 ≥1%、
  rob_fill robOver80 ≥50% 且 div 在场），不达标不算完成。

## 负载台账（实测值随 W1 任务逐行填写）

| workload | 任务 | golden (FINAL=16hex) | C3 SE hostSeconds | simInsts | 事件密度要点 | 状态 |
|---|---|---|---|---|---|---|
| smoke | W1.0 | `45737cc9a76c0dce` | 1.18 / 1.19（两次） | 308057 | —（框架冒烟核，非探针，无密度门） | done |
| branch_mispred | W1.5a | （待实测） | （待实测） | （待实测） | mispredicts/commits ≥5% | pending |
| dep_chain（int/vec 两版） | W1.5b | （待实测） | （待实测） | （待实测） | flIntLe8 ≥1%（int）/ flVecLe6 ≥1%（vec） | pending |
| rob_fill（int/fp 两版） | W1.5c | （待实测） | （待实测） | （待实测） | robOver80 ≥50% 且 div>0 | pending |
| coremark | W1.1 | （待实测） | （待实测） | （待实测） | 自带 CRC 校验 | pending |
| embench | W1.2 | （待实测） | （待实测） | （待实测） | 每程序自带校验退出码 | pending |
| polybench | W1.3 | （待实测） | （待实测） | （待实测） | 全数组 array_hash | pending |
| gap / libjpeg | W1.4 | （待实测） | （待实测） | （待实测） | 语义代理 checksum / 逐像素 hash | pending |

## smoke 实测记录（W1.0，2026-09-23）

- 构建：`make -C workloads/ooo smoke` → `gcc -O2 -static -Wall -Wextra`，
  零 warning；`file`：ELF 64-bit ARM aarch64, statically linked。
- gem5 C3 SE 两次（`--outdir=/tmp/ooo_w10_s1`、`/tmp/ooo_w10_s2`）：均 EXIT=0，
  FINAL 行逐字节一致（`od -c` 确认 `FINAL=45737cc9a76c0dce\n`），
  hostSeconds 1.18 / 1.19（<5 s 达标，远低于 60 s 预算）。
- 宿主原生运行一次：EXIT=0，FINAL 与 gem5 一致（native == gem5）。
