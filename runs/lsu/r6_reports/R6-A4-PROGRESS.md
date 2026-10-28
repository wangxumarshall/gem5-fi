# R6-A4 进度（滚动更新，唯一活动记录）

- 起始 HEAD：`df39c4e8ad3e9ac4e1f536076b6b5fa70b542bce`
- 起始工作树：clean；本地=远端=HEAD；`origin/fi-ding=659fa4cf`
- 旧二进制 SHA：`c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e`
- 起始状态：65/90 合格（旧二进制，不重跑）
- 本轮范围：25 格（清单见 FINAL-REPORT / 计划）

## 已确认事实（只读）

- [x] 分支/HEAD/远端一致、工作树干净、无 gem5/scons/pytest/campaign 在跑（仅有主检出 `r6_n8_batch_monitor.sh` bash 监控，不动）。
- [x] A05-F2-W3 s1 真实证据：`attempted=156129 eligible=91623 injected=0`（R=434），首火位 F2 max=140806 → 根因确认。
- [x] A01-F1-W3 s2 真实事件链含 `tlb_fault → squash_discarded(L4, contained=1, request_id=6126737, corr=seq_primary, tick 单调)`；缺 L0→L3 前缀导致拒准入。
- [x] A07-F0-W3 s1 注入日志：`ready → resume(consumed=1, squashed=1)`，prop_evt 仅 inj/chain_end。

## 进展

| 时间 | 事件 | 结果 |
|---|---|---|
| 2026-10-28 | 接管现场、只读确认 | 通过 |
| 2026-10-28 | 机制定位（repeat/A01/A07） | 完成 |
| 2026-10-28 | A01 checker 白名单（`_a01_translation_squash_witness`）+ 新测试 | 合成 15 用例全过；真实 `A01-F1-W3 s2` / `A01-F2-W3 s2` 两条流：terminal=detected_contained，admitted=True，path=contained，violations=[] |
| 2026-10-28 | 重跑 harness：`tools/r6_a4_batch.sh` + `TIMEOUT` 覆盖 | 已写，未运行（等 canary） |

| 2026-10-28 | A07-b checker 契约实现 + 严格化（Lane C 9 类反例） | A01/A07 契约/准入测试全 PASS；已提交 `e0d46a83` 并推送 |
| 2026-10-28 | A07-b C++ 事件发射（Lane B） | 已改 5 个 C++ 文件，**未构建**（等 census 结束） |
| 2026-10-28 | LSU 路径 maxFaults=1 封顶 + measure-only eligible census 模式 + repeat 上限 131072 | 已改 C++/config/workload header，**未构建/未重编 workload** |
| 2026-10-28 | 提交 `c90fe85f` A01 窄白名单初版 → `e0d46a83` 收紧版 | 已推送 |
| 2026-10-28 | 构建（scons -j16） | SCONS_EXIT=0；新二进制 sha256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 2026-10-28 | workload 重建（仅 repeat 上限 4096→131072） | 四个 golden 逐字不变：W3 728e604ffcec539d / W0 07568da9f3ad5665 / W5 1f4cbf14327717df / W9 030921682b3731f2 |
| 2026-10-28 | 提交 `cfc608c4` A07-b 生命周期 + maxFaults 封顶 | 已推送 |
| 2026-10-28 | canary（新二进制，tag `_r6a4c`） | A05-F2-W3 s1: injected=1, detected_contained, admitted/certified；A01-F2-W9 s1: arch fault delivered, detected_contained；A02-F2-W9 s1: full（errant_commit+consumer）；A07-F0-W3 s1: inj→resume→squashed→chain_end, detected_contained；A01-F1-W3 s2: squash 白名单 detected_contained；全部 violations=[] |

## census 关键发现（旧二进制，需用 measure-only 复测）

- F2 首火位（LCG 精确）：seed1=106412、seed2=99417、seed3=140806（max）。
- 旧 R 验证（未封顶）出现 injected=2（A04-a/A05-d 等长 repeat）→ 需要 maxFaults 封顶。
- A08-a：过滤后 eligible delta ≈ 10.75/iter（W3）、2.0/iter（W5）→ R=15706/84418，需上限 131072。
- A08-b：eligible 恒 21（r1/r5/r10），疑似仅启动流有同 tick store-first 配对 → 可能结构性 NO_FIRE。
- A01/A02-F2-W9 **已解决**：Lane A 用 `--addrpath_warmup_events 10000000`（超出流长，
  完全不触发）测得未注入流 E1=264751、delta≈261854；seed1/2/3 首火位
  106412/99417/140806 **全部 < E1** ⇒ repeat_factor=1，首趟即确定性首火。
  真实注入流为 inj→…→tlb_fault→**arch_translation_fault(delivered, L2,
  contained=1)**→chain_end ⇒ 既有通用终局规则判 detected_contained。guest SEGV
  由 chaos_guest_segv 退出事件收口（campaign exit=0；census 表的 exit=1 是分类列）。
- A08-b：待新二进制/干净测量确认 delta 是否恒 0（疑似结构性 NO_FIRE）。
- 旧 census 的 verify 运行被注入污染 → Lane A 已改用污染隔离重跑；新二进制将提供 measure-only 模式。

## 未决

- Lane A：F2/gap census 与 repeat 表（进行中）
- Lane B：A07-b 生命周期 C++（进行中，未构建）
- Lane C：A01 真实流机制核对报告（进行中）
- 构建：等 Lane A census 结束（scons 期间 gem5=0）
