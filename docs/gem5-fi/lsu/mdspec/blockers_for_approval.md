# 外部阻塞 77 项 — 需用户裁决清单

> 生成自 `tools/lsu_blocked_triage.py` 的互斥分类。这 4 类**不能由本轨道单方面解除**
> （需外部基础设施/许可，或已由既定裁决封存），故单独列出请求裁决。
> 其余 49 项 MODE-UNIMPL 属可自行实现（不需批准，需要工作量），见 blocked_triage.md。

## RULING（6 项）

- **阻塞机理**：A06 load 侧定宽完成契约 + byte-enable 未实现（store-only 安全路径已在案）；解除需 §2.c 路径 spike 验证 + 测试
- **解除条件**：实现 load 侧 size 注入（放大器路径或 LSQRequest 层）+ byte-enable 钩子，并补 spike 证据
- **建议处置**：批准延期（已按规格裁决封存）

| RunID | 单元 | 模型 |
|---|---|---|
| A06-F0-W3 | AGU | A06 |
| A06-F0-W5 | AGU | A06 |
| A06-F2-W3 | AGU | A06 |
| A06-F2-W5 | AGU | A06 |
| A06-F6-W3 | AGU | A06 |
| A06-F6-W5 | AGU | A06 |

## LICENSE（12 项）

- **阻塞机理**：SPEC CPU2017 需授权；SE 侧无合法载体可替代（许可缺口是负载真实属性）
- **解除条件**：取得 SPEC CPU2017 授权，或正式裁决以 SE 近似负载替代（需您书面同意改变规格负载）
- **建议处置**：批准延期 / 或给出替代方案

| RunID | 单元 | 模型 |
|---|---|---|
| C15-F0-W11 | L1d-Cache | C15 |
| C15-F4-W11 | L1d-Cache | C15 |
| C15-F6-W11 | L1d-Cache | C15 |
| L04-F0-W11 | Load Queue | L04 |
| L04-F2-W11 | Load Queue | L04 |
| L04-F6-W11 | Load Queue | L04 |
| S13-F0-W11 | Store Queue | S13 |
| S13-F1-W11 | Store Queue | S13 |
| S13-F2-W11 | Store Queue | S13 |
| T10-F0-W11 | L1d-TLB | T10 |
| T10-F1-W11 | L1d-TLB | T10 |
| T10-F2-W11 | L1d-TLB | T10 |

## FS-MULTICORE（35 项）

- **阻塞机理**：语义需多核（litmus MP/SB/LB/IRIW/Dekker、PARSEC 共享队列）；SE 单核不可判别
- **解除条件**：多核 FS 平台（SMP + 跨核一致性）落地
- **建议处置**：批准延期，排入 FS 阶段

| RunID | 单元 | 模型 |
|---|---|---|
| C08-F0-W7 | L1d-Cache | C08 |
| C08-F2-W7 | L1d-Cache | C08 |
| C08-F5-W7 | L1d-Cache | C08 |
| C08-F6-W7 | L1d-Cache | C08 |
| O01-F0-W7 | 原子与同步 | O01 |
| O01-F2-W7 | 原子与同步 | O01 |
| O01-F6-W7 | 原子与同步 | O01 |
| O02-F0-W7 | 原子与同步 | O02 |
| O02-F2-W7 | 原子与同步 | O02 |
| O02-F5-W7 | 原子与同步 | O02 |
| O02-F6-W7 | 原子与同步 | O02 |
| O03-F0-W7 | 原子与同步 | O03 |
| O03-F2-W7 | 原子与同步 | O03 |
| O03-F6-W7 | 原子与同步 | O03 |
| O04-F0-W7 | 原子与同步 | O04 |
| O04-F2-W7 | 原子与同步 | O04 |
| O04-F6-W7 | 原子与同步 | O04 |
| O05-F0-W7 | 原子与同步 | O05 |
| O05-F4-W7 | 原子与同步 | O05 |
| O05-F6-W7 | 原子与同步 | O05 |
| O06-F0-W7 | 原子与同步 | O06 |
| O06-F4-W7 | 原子与同步 | O06 |
| O06-F6-W7 | 原子与同步 | O06 |
| O07-F0-W7 | 原子与同步 | O07 |
| O07-F2-W7 | 原子与同步 | O07 |
| O07-F6-W7 | 原子与同步 | O07 |
| O09-F0-W13 | 原子与同步 | O09 |
| O09-F0-W7 | 原子与同步 | O09 |
| O09-F1-W13 | 原子与同步 | O09 |
| O09-F1-W7 | 原子与同步 | O09 |
| O09-F2-W13 | 原子与同步 | O09 |
| O09-F2-W7 | 原子与同步 | O09 |
| P09-F0-W13 | 数据预取器 | P09 |
| P09-F4-W13 | 数据预取器 | P09 |
| P09-F6-W13 | 数据预取器 | P09 |

## FS-INFRA（24 项）

- **阻塞机理**：需 FS 基础设施（TLB 地址翻译负载 4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI）
- **解除条件**：FS checkpoint 流水线跑通 TLB 翻译负载（内核+磁盘镜像已就位）
- **建议处置**：批准延期，排入 FS 阶段

| RunID | 单元 | 模型 |
|---|---|---|
| T01-F0-W4 | L1d-TLB | T01 |
| T01-F1-W4 | L1d-TLB | T01 |
| T01-F2-W4 | L1d-TLB | T01 |
| T02-F0-W4 | L1d-TLB | T02 |
| T02-F2-W4 | L1d-TLB | T02 |
| T03-F5-W4 | L1d-TLB | T03 |
| T04-F0-W4 | L1d-TLB | T04 |
| T04-F2-W4 | L1d-TLB | T04 |
| T04-F6-W4 | L1d-TLB | T04 |
| T05-F0-W4 | L1d-TLB | T05 |
| T05-F2-W4 | L1d-TLB | T05 |
| T05-F6-W4 | L1d-TLB | T05 |
| T06-F0-W4 | L1d-TLB | T06 |
| T06-F2-W4 | L1d-TLB | T06 |
| T06-F6-W4 | L1d-TLB | T06 |
| T07-F0-W4 | L1d-TLB | T07 |
| T07-F4-W4 | L1d-TLB | T07 |
| T07-F6-W4 | L1d-TLB | T07 |
| T08-F0-W4 | L1d-TLB | T08 |
| T08-F4-W4 | L1d-TLB | T08 |
| T08-F6-W4 | L1d-TLB | T08 |
| T10-F0-W4 | L1d-TLB | T10 |
| T10-F1-W4 | L1d-TLB | T10 |
| T10-F2-W4 | L1d-TLB | T10 |

**合计 77 项**（RULING 6 + LICENSE 12 + FS-MULTICORE 35 + FS-INFRA 24）

## 备选（若您希望缩小延期范围）

- **LICENSE(12)**：若同意以 SE 近似负载（如 `sqlite_like`/`gap_bfs` 替代 SPEC 采样区间）跑，
  可让其中部分 RunID 转为可运行，但**这改变了规格负载**，需您明确批准口径变更。
- **FS-INFRA(24)**：TLB 翻译负载的 SE 载体缺口最大；若 FS checkpoint 流水线跑通即可全部转 PARTIAL/PASS。
- **FS-MULTICORE(35)**：依赖多核 FS，短期无替代（O 系 SE 载体探针只能验证注入器机制，不能算作这些格）。
