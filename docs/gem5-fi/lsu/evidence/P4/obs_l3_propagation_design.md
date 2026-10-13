# obs_l3_propagation_design.md — [LSU][OBS-L3] 真实 L3 传播链设计（纠偏轮 Subagent-A）

日期：2026-10-13 · 分支：`obs2-sub-a`（worktree `.claude/worktrees/lsu-obs2-a`）
提交：① `6c9d5930`（CHAOSPropagation 核心+格式规范）② `bf6512a7`（注入点+LSQ hook）
③ `058e978e`（Python 解析器+测试）④ 本提交（驱动接线+设计文档）

## 1. 背景与纠偏目标

中央纠偏指令（2026-10-13）：当前 L3 = unsupported / commit-divergence-计数
不可接受，必须为 LSU 非 PRF 故障实现**真实传播关联**。本设计以
CHAOSPropagation（新 SimObject，观测只读）沿故障的实际数据通路记
`inj→addr_form→mem_req→resp→taint_reg→consumer→errant_commit` 链，
per-ptag（每故障一条链），并以 `funnel` 行保证 abort 样本携带
attempted/eligible/injected。

**覆盖范围（v1，如实）**：`COVERED_FAMILIES = {"addrpath", "cache"}`。
lsqfwd / prefetch / exmon 家族驱动不加旗标 → obs_core 走 unsupported
（不猜、不冒充）。

## 2. prop_trace.csv.gz v1 格式（钉死契约）

```
# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,request_id,addr,phys_reg,arch_reg,detail
```

- 每节点一行 CSV；数值列无值写**空串**；`addr` 无前缀小写 hex；
  `detail` 为 `k=v;k=v`（无逗号；数值十进制，地址值无前缀 hex）。
- kind：`inj`（注入点，addr=原地址，detail 含 site/family/old/new）·
  `addr_form`（错误地址形成，addr=新地址）· `mem_req`（携带故障的
  Request 离开 LSQ）· `resp`（故障交付响应回 CPU，detail 含
  data_fnv/fault）· `taint_reg`（load 目的 phys reg 入污染集）·
  `consumer`（提交指令读了污染源）· `errant_commit`（首个污染路径
  提交：faulting_load_commit|first_consumer）· `funnel`（ptag=0，
  attempted/eligible/injected 快照）。
- **request_id 列 = `Request::getReqInstSeqNum()`**（契约偏离，如实）：
  gem5 v25 `Request` 无唯一 id()（亲验 mem/request.hh），此为 gem5 实际
  维护的 request→dyn-inst 绑定；未打 seq 的请求（split `_mainReq`）该列
  空串（调用处先判 `hasInstSeqNum()`——get 版本带 assert）。
- crash 持久化：gzopen + **每节点 gzflush(Z_SYNC_FLUSH)**（W2.1 契约；
  prop trace 每 run 仅数节点，逐节点 flush 成本可忽略）；gzip trailer
  由 exit callback gzclose 写入（abort 前缀可被解析器打捞，truncated=
  true）。实证（/tmp 探针）：Python gzip 逐行 yield 后抛 EOFError、
  0 字节文件 0 行无异常。

## 3. 链路图

```
addrpath 家族
  CHAOSAddrPath PRE (pushRequest) ──┐
  CHAOSAddrPath post (sendFragment) ┴→ registerInjection
        → inj + addr_form + addr注册表[new_addr, +size)
  LSQ sendFragmentToTranslation → noteMemRequest → mem_req（范围重叠
        且 dyn_inst_seq 匹配；PRE 家族在 pushRequest 注册、post 家族
        在本函数 corruption 后注册，一次调用覆盖两族）
  LSQUnit completeDataAccess → noteMemResponse → resp（pkt req vaddr
        范围重叠 + dyn_seq 匹配）→ needWB+NoFault 时 taint_reg（与
        writeback completeAcc 条件严格一致；squash 内部拦截）
  Commit::commitHead（W2.1/W2.4 同锚点）→ noteCommit → consumer
        （源 phys reg ∈ 污染集）/ errant_commit（首个：污染 load 自身
        提交或首个 consumer）/ 目的再污染 / 无关生产者 clean-overwrite

cache 家族
  CHAOSCache injectFault → registerCacheFault（data=单字节注册表 ON；
        data_shift=整块 -1 ON；tag/valid/dirty/coh=-2 仅 inj 节点；
        paired-sector 伙伴字节独立链；victim 路径 -2）
  后续同 addrpath 的 mem_req（sendFragment，SE vaddr==paddr 范围重叠）
  → resp → taint_reg → consumer/errant_commit

FUNNEL（两族共用）
  注入时（CHAOSAddrPath both hooks / CHAOSCache 每攻击）→ prop_trace
  funnel 节点（abort 存活）+ 注入日志 "FUNNEL: attempted=.. eligible=..
  injected=.."（simout 流，abort 即丢——best-effort，文档如实）
  exit callback → 终值 funnel（仅正常退出）
```

## 4. Hook 位点清单（文件:行号 = 提交②④后的 worktree 实测）

| 位点 | 文件:行 | 作用 |
|---|---|---|
| CPU accessor | `src/cpu/o3/cpu.hh:521-522` | `chaosPropagation` 指针 + setter（LSQ 侧经 `cpu->chaosPropagation`） |
| Commit accessor | `src/cpu/o3/commit.hh:397-401` | commit 侧指针 + setter（MicroSnap 模式） |
| commit hook | `src/cpu/o3/commit.cc:1311-1318` | `noteCommit`（W2.1/W2.4 锚点第三个 hook，setEntry 循环后 retireHead 前） |
| PRE 注册 | `src/cpu/o3/lsq.cc:790-795` | pushRequest 入口：lastPreHookInjected() → registerInjection |
| post 注册 | `src/cpu/o3/lsq.cc:1181-1186` | sendFragment：maybeCorrupt 返回 true → registerInjection |
| mem_req | `src/cpu/o3/lsq.cc:1194-1196` | sendFragment：corruption 后 noteMemRequest（覆盖两族） |
| resp/taint | `src/cpu/o3/lsq_unit.cc:178-180` | completeDataAccess：needWB 分支前 noteMemResponse |
| addrpath funnel | `src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:188`（post 注入点）/`:347-353`（PRE 注入点）/`:367-390`（notifyFunnelAtInjection）/`:449-460`（exit） | 注入时+exit funnel |
| cache 注册 | `src/mem/cache/CHAOSCache/CHAOSCache.cc:448`（tag）/`:464`（valid）/`:490`（data_shift 整块）/`:509`（dirty/coh）/`:573`（data 字节）/`:613`（paired）/`:726`（victim） | registerCacheFault |
| cache funnel | `CHAOSCache.cc:284-286`（noteFunnelAtInjection）/`:277-278`（attack_attempts）/`:296-297`（attack_eligible）/`:632-634`（每攻击）/ctor exit callback | legacy 漏斗计数+funnel 行 |
| 配置挂载 | `configs/se/lsu_proxy.py`（--chaos_propagation/--prop_trace_file + board.chaos_propagation） | 仿 --chaos_ctrace/--ctrace_file |
| 驱动接线 | `tools/lsu_obs_driver.py`（_obs_args 家族感知 / run_fault+dry / post_process files+l3+build_observation / identity.prop_traced） | 仅覆盖家族+full 模式加旗标 |

## 5. 接口契约（主负责人冻结版；B/C 依赖）

```python
# tools/lsu_l3_propagation.py（Subagent-A 所有）
COVERED_FAMILIES = {"addrpath", "cache"}
parse_prop_trace(path) -> {"truncated", "nodes", "funnel", "malformed"}
build_l3(family, l2, prop_trace_path, inactive=False) -> dict
#   inactive → N/A(inactive_no_activation)；未覆盖/缺失/0 节点 →
#   unsupported；正常 → complete/propagation_trace/
#   correlation_keys=[dynInstSeqNum, request_id, ptag]/evidence/caveats
```

obs_core 委托（B 侧实现，驱动已按契约接线）：
`OC.build_l3(family, l2, inactive=False, prop_trace_path=None)` 与
`OC.build_observation(..., prop_trace_path=None)`。驱动用
`inspect.signature` 探测：obs_core 已接则走委托，否则直连
`LP.build_l3`（同一实现；**兼容回退**——绝不因 B 未合入而退回
unsupported 假象）。

**诚实纪律**：`auxiliary_commit_footprint`（L2 commit_diff 副产品）仅
附注（note 标注"不是传播证据（不冒充）"），绝不入 evidence；commit_diff
divergence 计数绝不冒充传播链。

## 6. 已知边界（caveats，解析器逐条输出）

1. **内存间接污染不覆盖**：污染值经 store 写入内存后被另一 load 读回
   ——污染集仅跟踪 load 目的寄存器（v1 无 store→memory→load 传递）。
2. **errant_commit 口径**：= 首个污染路径提交（传播视角）；字段级首个
   错误提交以 L2 `commit_diff.first_errant_commit` 为准（同一
   dyn_inst_seq 空间可对齐）。
3. **squash 竞态残留**：load 写回（taint）后被 squash、phys reg 回收
   复用 → 罕见 stale-taint 窗口；clean-overwrite 规则界定，v1 无
   squash hook。
4. **addrpath 纯 flag 模式**（S06/L02）：链止于 addr_form（无被污染
   地址）；translation fault（FS）无 completeDataAccess → 链止于
   mem_req。
5. **cache hit/miss 不可分**：CPU 侧 hook 看不到命中与否——clean 块
   逐出后 refetch 的响应可能被误计为 resp（假阳性上界；dirty 块回写
   后 refetch 为真阳性）。
6. **SE vaddr==paddr 假设**：cache 注册表按物理块地址匹配（FS 跨翻译
   不成立；LSU campaign 为 SE）。
7. **cache metadata/victim**：tag/valid/dirty/coh 与 victim 路径链止于
   inj（-2 注册，无投递跟踪）。
8. **组合注入**：CHAOSL1DForward 同挂时其 corruption 发生在
   noteMemResponse 快照之后——L3 链不感知组合注入（campaign 单注入器
   单样本，不触发）。
9. **replay 比对**：replay_check 证据比对含 ctrace sha，未加 prop_trace
   sha（后续可选加固；确定性下两者等价）。
10. **request_id 语义**：= ReqInstSeqNum（§2 契约偏离）；
    `registerCacheFault` 键 = (block_addr, byte_offset, block_size,
    field) 而非 (set,way,tag)——blockAddr 是 CPU 侧响应可比对的唯一
    定位符（regenerateBlkAddr 口径）。

## 7. 编译后置清单（AGU formal 批次终态后执行，禁编译令解除）

前置：AGU formal 生产批次到达终态、guard 门禁解除、无并发 gem5 进程。

1. **编译**（worktree 合回后，或经主负责人批准在主树）：
   ```bash
   cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt   # 绝不 -j126（OOM）
   ```
   门禁：**零新警告/零错误**（gem5 -Werror；本系列新增代码若出警告=
   失败，修复后重验）。首配 conftest ~2min/次属正常，勿中断。
2. **冒烟（新旗标端到端，短流 checklist 载体）**：
   ```bash
   build/ARM/gem5.opt --outdir=/tmp/l3smoke configs/se/lsu_proxy.py \
     --cmd workloads/directed/gap_bfs --cpu O3 --variant B0 \
     --chaos_addrpath --addrpath_mode a01_bit --addrpath_lsu_tier F0 \
     --addrpath_span_events 1000 --addrpath_rng_seed <seed> \
     --chaos_propagation --prop_trace_file /tmp/l3smoke/prop_trace.csv.gz
   python3 tools/lsu_l3_propagation.py /tmp/l3smoke/prop_trace.csv.gz
   ```
   通过判据：trace 含 inj/addr_form/mem_req/resp（链至少到 resp；
   taint_reg/consumer/errant_commit 视故障是否走到写回与消费）；
   `zcat | head -1` = v1 格式头。
   cache 家族冒烟：`--chaos_l1d --l1d_target_field data ...` 同理。
3. **零回归证明**：不带 `--chaos_propagation` 的 golden 重跑 FINAL
   校验和逐字节一致（nullptr 短路 = 零行为改动；W2.1 硬门禁同款）。
   带旗标的 no-fault 运行 workload FINAL 亦应一致（观测只读证明）。
4. **冻结流程**：编译+冒烟通过后，新 gem5.opt sha256 记入冻结清单
   （对照 p4_freeze_agu_formal_20261012.json 的 identity.gem5_opt_sha256
   字段格式），更新 LSU_GEM5_BIN 指向与 guard 冻结记录，再恢复量产。
   旧二进制运行的在途/已完成样本与新二进制样本**不混数**（identity
   gem5_opt_sha256 不同即不同 baseline）。
5. **失败回退**：编译错误/冒烟链断/校验和漂移 → 修复重验；无法短修
   则 revert 本系列 4 提交（纯增量，revert 干净）。

## 8. 验证状态（截至本提交，如实）

- Python 侧：`python3 tests/test_lsu_l3_propagation.py` 40/40 PASS
  （解析 33 + 驱动接线 7）；`tests/test_lsu_obs_driver_cli.py` 15/15
  PASS；`tests/test_lsu_obs_core.py` PASS（回归）。
- C++ 侧：**未经编译**（指令纪律：批次在跑，编译后置）。四个提交均为
  源码级，模式对齐清单见各提交信息（MicroSnap/CommitTrace 逐项）。
  编译验证按 §7 执行后方为完成。
- dry-run 端到端（真实输出摘录，ITEM-002=A01/addrpath/full）：
  `... --chaos_ctrace --ctrace_file .../commit_trace.csv.gz --chaos_msnap
  --msnap_every 1000 --msnap_file .../micro_snap.csv.gz
  --chaos_propagation --prop_trace_file .../prop_trace.csv.gz`
