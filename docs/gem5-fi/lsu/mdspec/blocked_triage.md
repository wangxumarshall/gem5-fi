# 126 BLOCKED 逐项裁决（互斥分类）

- BLOCKED 总数：126（守恒校验通过：Σ 分类 == 总数）
- 分类统计：RULING=6 / LICENSE=12 / FS-MULTICORE=35 / FS-INFRA=24 / MODE-UNIMPL=49 / HOOK-UNIMPL=0 / OK=0

## 互斥类别定义

| 类别 | 含义 | 解除条件 |
|---|---|---|
| RULING | 模型级裁决封锁（A06 load 侧 / byte-enable） | §2.c 路径 spike 验证 + 测试 |
| LICENSE | SPEC CPU2017 授权缺失（W11） | 取得授权 |
| FS-MULTICORE | 需多核 FS（litmus/PARSEC 语义） | 多核 FS 基础设施落地 |
| FS-INFRA | 需 FS 基础设施（TLB 翻译负载） | FS checkpoint 流水线 |
| MODE-UNIMPL | 规格表 10 标注『先实现』的子模型模式 | 实现该模式 + 测试 |
| HOOK-UNIMPL | 钩子/载体缺口（无模式标注） | 补钩子或补 SE 载体映射 |
| OK | 无上述阻塞（应为 0） | — |

## 需用户批准的延期清单

以下类别**在可预见范围内无法由本轨道单方面解除**，需批准延期：

- **LICENSE**（12 个）：C15-F0-W11, C15-F4-W11, C15-F6-W11, L04-F0-W11, L04-F2-W11, L04-F6-W11, S13-F0-W11, S13-F1-W11, S13-F2-W11, T10-F0-W11, T10-F1-W11, T10-F2-W11
- **FS-MULTICORE**（35 个）：C08-F0-W7, C08-F2-W7, C08-F5-W7, C08-F6-W7, O01-F0-W7, O01-F2-W7, O01-F6-W7, O02-F0-W7, O02-F2-W7, O02-F5-W7, O02-F6-W7, O03-F0-W7, O03-F2-W7, O03-F6-W7, O04-F0-W7, O04-F2-W7, O04-F6-W7, O05-F0-W7, O05-F4-W7, O05-F6-W7, O06-F0-W7, O06-F4-W7, O06-F6-W7, O07-F0-W7, O07-F2-W7, O07-F6-W7, O09-F0-W13, O09-F0-W7, O09-F1-W13, O09-F1-W7, O09-F2-W13, O09-F2-W7, P09-F0-W13, P09-F4-W13, P09-F6-W13
- **FS-INFRA**（24 个）：T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F0-W4, T05-F2-W4, T05-F6-W4, T06-F0-W4, T06-F2-W4, T06-F6-W4, T07-F0-W4, T07-F4-W4, T07-F6-W4, T08-F0-W4, T08-F4-W4, T08-F6-W4, T10-F0-W4, T10-F1-W4, T10-F2-W4
- **RULING**（6 个）：A06-F0-W3, A06-F0-W5, A06-F2-W3, A06-F2-W5, A06-F6-W3, A06-F6-W5

可自行解除（不需批准，但需实现工作）：
- MODE-UNIMPL（49 个）：见下表逐项理由

## 逐项明细

| RunID | 单元 | 模型 | 互斥类别 | 理由 |
|---|---|---|---|---|
| A06-F0-W3 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A06-F0-W5 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A06-F2-W3 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A06-F2-W5 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A06-F6-W3 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A06-F6-W5 | AGU | A06 | RULING | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19) |
| A07-F0-W3 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| A07-F0-W5 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| A07-F4-W3 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| A07-F4-W5 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| A07-F6-W3 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| A07-F6-W5 | AGU | A07 | MODE-UNIMPL | 在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation 增加统一事件；在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点；把  |
| C08-F0-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| C08-F2-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| C08-F5-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| C08-F6-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| C11-F0-W10 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F0-W6 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F2-W10 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F2-W6 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F4-W10 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F4-W6 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F6-W10 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C11-F6-W6 | L1d-Cache | C11 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F0-W10 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F0-W6 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F4-W10 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F4-W6 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F6-W10 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C12-F6-W6 | L1d-Cache | C12 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C14-F5-W10 | L1d-Cache | C14 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C14-F5-W6 | L1d-Cache | C14 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F0-W10 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F0-W11 | L1d-Cache | C15 | LICENSE | campaign:deferred(consumer-side: MSHR occupancy event source only) ; spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） ; workload:workload-level:blocked(spec-l |
| C15-F0-W6 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F4-W10 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F4-W11 | L1d-Cache | C15 | LICENSE | campaign:deferred(consumer-side: MSHR occupancy event source only) ; spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） ; workload:workload-level:blocked(spec-l |
| C15-F4-W6 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F6-W10 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| C15-F6-W11 | L1d-Cache | C15 | LICENSE | campaign:deferred(consumer-side: MSHR occupancy event source only) ; spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） ; workload:workload-level:blocked(spec-l |
| C15-F6-W6 | L1d-Cache | C15 | MODE-UNIMPL | 扩展 src/mem/cache/cache.cc 的access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writebackBlk与MSHR队列事件；为tag/valid/dirty/coh/victim故障建立传播regi |
| L04-F0-W11 | Load Queue | L04 | LICENSE | campaign:deferred(consumer-side: response-pairing event source only) ; spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） ; workload:workload-level:blocke |
| L04-F0-W12 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| L04-F0-W5 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| L04-F2-W11 | Load Queue | L04 | LICENSE | campaign:deferred(consumer-side: response-pairing event source only) ; spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） ; workload:workload-level:blocke |
| L04-F2-W12 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| L04-F2-W5 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| L04-F6-W11 | Load Queue | L04 | LICENSE | campaign:deferred(consumer-side: response-pairing event source only) ; spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） ; workload:workload-level:blocke |
| L04-F6-W12 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| L04-F6-W5 | Load Queue | L04 | MODE-UNIMPL | 新增LQ逐事件跟踪：src/cpu/o3/lsq_unit.cc 的insertLoad/read/checkViolations/completeDataAccess与replay路径；记录lq_idx↔dyn_inst_seq↔request_id↔dest phys-reg映射；L03接入真实 |
| O01-F0-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O01-F2-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O01-F6-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O02-F0-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O02-F2-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O02-F5-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O02-F6-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O03-F0-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O03-F2-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O03-F6-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: litmus needs multi-core FS) |
| O04-F0-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data path needs cache-side SwapResp hook) ; spec:需新增（当前阻塞：缺RMW数据/SwapResp hook） ; workload:workload-level:blocked(multicore-fs:  |
| O04-F2-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data path needs cache-side SwapResp hook) ; spec:需新增（当前阻塞：缺RMW数据/SwapResp hook） ; workload:workload-level:blocked(multicore-fs:  |
| O04-F6-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data path needs cache-side SwapResp hook) ; spec:需新增（当前阻塞：缺RMW数据/SwapResp hook） ; workload:workload-level:blocked(multicore-fs:  |
| O05-F0-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: RMW ordering needs multi-core) ; spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性） ; workload:workload-level:blocked(multicore-fs: litm |
| O05-F4-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: RMW ordering needs multi-core) ; spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性） ; workload:workload-level:blocked(multicore-fs: litm |
| O05-F6-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: RMW ordering needs multi-core) ; spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性） ; workload:workload-level:blocked(multicore-fs: litm |
| O06-F0-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: barrier completion needs multi-core) ; spec:需新增（当前阻塞：需要多核FS barrier完成跟踪） ; workload:workload-level:blocked(multicore-fs |
| O06-F4-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: barrier completion needs multi-core) ; spec:需新增（当前阻塞：需要多核FS barrier完成跟踪） ; workload:workload-level:blocked(multicore-fs |
| O06-F6-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: barrier completion needs multi-core) ; spec:需新增（当前阻塞：需要多核FS barrier完成跟踪） ; workload:workload-level:blocked(multicore-fs |
| O07-F0-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: order-tag swap needs multi-core) ; spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪） ; workload:workload-level:blocked(multicore- |
| O07-F2-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: order-tag swap needs multi-core) ; spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪） ; workload:workload-level:blocked(multicore- |
| O07-F6-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: order-tag swap needs multi-core) ; spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪） ; workload:workload-level:blocked(multicore- |
| O09-F0-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: PARSEC ne |
| O09-F0-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: litmus ne |
| O09-F1-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: PARSEC ne |
| O09-F1-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: litmus ne |
| O09-F2-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: PARSEC ne |
| O09-F2-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand path needs cache-side hook) ; spec:需新增（当前阻塞：缺RMW operand hook） ; workload:workload-level:blocked(multicore-fs: litmus ne |
| P06-F0-W6 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P06-F0-W8 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P06-F2-W6 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P06-F2-W8 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P06-F6-W6 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P06-F6-W8 | 数据预取器 | P06 | MODE-UNIMPL | 新增 CHAOSPrefetchTrace：src/mem/cache/prefetch/stride.cc::calculatePrefetch、queued.cc队列、base.cc::notify与cache request/fill/victim/writeback；为prefetch re |
| P09-F0-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: PARSEC needs multi-core FS) |
| P09-F4-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: PARSEC needs multi-core FS) |
| P09-F6-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: PARSEC needs multi-core FS) |
| S10-F0-W5 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S10-F0-W9 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S10-F2-W5 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S10-F2-W9 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S10-F5-W5 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S10-F5-W9 | Store Queue | S10 | MODE-UNIMPL | 新增 CHAOSLSQTrace：src/cpu/o3/lsq_unit.cc 的insertStore/executeStore/checkViolations/writebackStores/completeStore与lsq.cc请求创建点；为每个SQ事件写sq_idx、dyn_inst_se |
| S13-F0-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F1-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F2-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T01-F0-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F1-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F2-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F0-W4 | L1d-TLB | T02 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F2-W4 | L1d-TLB | T02 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T03-F5-W4 | L1d-TLB | T03 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F0-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F2-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F6-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T05-F0-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(mode unimplemented: valid/global/ASID state) ; spec:需新增（当前阻塞：valid/global/ASID模式未实现） ; workload:workload-level:blocked(fs-infra: TLB |
| T05-F2-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(mode unimplemented: valid/global/ASID state) ; spec:需新增（当前阻塞：valid/global/ASID模式未实现） ; workload:workload-level:blocked(fs-infra: TLB |
| T05-F6-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(mode unimplemented: valid/global/ASID state) ; spec:需新增（当前阻塞：valid/global/ASID模式未实现） ; workload:workload-level:blocked(fs-infra: TLB |
| T06-F0-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(mode unimplemented: permission legal-substitution) ; spec:需新增（当前阻塞：permission/attribute合法替换未实现） ; workload:workload-level:blocked(fs |
| T06-F2-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(mode unimplemented: permission legal-substitution) ; spec:需新增（当前阻塞：permission/attribute合法替换未实现） ; workload:workload-level:blocked(fs |
| T06-F6-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(mode unimplemented: permission legal-substitution) ; spec:需新增（当前阻塞：permission/attribute合法替换未实现） ; workload:workload-level:blocked(fs |
| T07-F0-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(mode unimplemented: hit fabrication/way select) ; spec:需新增（当前阻塞：hit fabrication/way select未实现） ; workload:workload-level:blocked(fs- |
| T07-F4-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(mode unimplemented: hit fabrication/way select) ; spec:需新增（当前阻塞：hit fabrication/way select未实现） ; workload:workload-level:blocked(fs- |
| T07-F6-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(mode unimplemented: hit fabrication/way select) ; spec:需新增（当前阻塞：hit fabrication/way select未实现） ; workload:workload-level:blocked(fs- |
| T08-F0-W4 | L1d-TLB | T08 | FS-INFRA | campaign:deferred(mode unimplemented: walk pairing) ; spec:需新增（当前阻塞：walk/fill pairing未实现） ; workload:workload-level:blocked(fs-infra: TLB workload nee |
| T08-F0-W9 | L1d-TLB | T08 | MODE-UNIMPL | 新增 CHAOSTLBTrace：挂在 src/arch/arm/tlb.cc::lookup/translateTiming 与 table_walker.cc 的walk/refill完成点，记录entry/way、VA/ASID、命中候选、字段before/after、walk_id、PA/f |
| T08-F4-W4 | L1d-TLB | T08 | FS-INFRA | campaign:deferred(mode unimplemented: walk pairing) ; spec:需新增（当前阻塞：walk/fill pairing未实现） ; workload:workload-level:blocked(fs-infra: TLB workload nee |
| T08-F4-W9 | L1d-TLB | T08 | MODE-UNIMPL | 新增 CHAOSTLBTrace：挂在 src/arch/arm/tlb.cc::lookup/translateTiming 与 table_walker.cc 的walk/refill完成点，记录entry/way、VA/ASID、命中候选、字段before/after、walk_id、PA/f |
| T08-F6-W4 | L1d-TLB | T08 | FS-INFRA | campaign:deferred(mode unimplemented: walk pairing) ; spec:需新增（当前阻塞：walk/fill pairing未实现） ; workload:workload-level:blocked(fs-infra: TLB workload nee |
| T08-F6-W9 | L1d-TLB | T08 | MODE-UNIMPL | 新增 CHAOSTLBTrace：挂在 src/arch/arm/tlb.cc::lookup/translateTiming 与 table_walker.cc 的walk/refill完成点，记录entry/way、VA/ASID、命中候选、字段before/after、walk_id、PA/f |
| T10-F0-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F0-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F1-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F1-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F2-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F2-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
