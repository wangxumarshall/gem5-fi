# LSU 观测链 L0 解析器扩展：cache "Field:" 系列注入行（OBS-FIX-5）

> 单元：lsu_obs_core.parse_l0 的 cache 注入明细只认 Byte Offset 数据位格式
> （_CACHE_INJ_RE）；CHAOSCache 对 tag/valid/dirty/data_shift/toggle 字段
> 目标（C04/C05/C06/C07/C09 模型族）发出 `Tick: N, Cache Block Addr: X,
> Field: <spec>, <detail>` 行 → injection_line_unparsed + injections_log_missing
> → finalize 拒绝 → driver 确定性崩溃（2026-10-14 C04-F0/F1-W6 实证，
> 隔离证据 p6_formal_full_c04_f{0,1}_w6/*.staging.quarantine.*）。
> 本补丁解锁 C04-F0/F1/F2-W6 + C06-F0/F2-W6 共 5 个合格 RunID
> （提案池 C01-C03 族已全部完成/在跑）。
> 分支：capacity/lsu-slots-24-20261014（28caead8 之上，本地提交不 push）。

## 设计

- 新增 `_CACHE_FIELD_INJ_RE`：`Tick, Cache Block Addr, Field: <spec>, <rest>`
  ——spec 例如 `tag (F5 alias)`/`valid (invalidate)`/`data_shift (C09 rotate
  by 1 byte)`/`<field> (toggle bit N)`；rest 为明细（old/new 等），整行保留
  在 raw。
- parse_l0 cache 分支：Byte Offset 正则不中 → Field 正则尝试 → 均不中才
  violation。Field 记录：site=cache_block:0xADDR，mode=field:<spec>，
  faults=1，field=<rest>。
- 零语义改动：Byte Offset/addrpath 路径、funnel 优先级、violation 语义、
  观测链其余层全部不变。

## 验收

- [x] 1. 红：真实隔离证据行（Field: tag (F5 alias), old_tag=0x23 -> new_tag=
      0x0）→ injection_line_unparsed（已实测）。
- [x] 2. 修复 + 绿：该行解析为 1 条 injection 记录、无 violation；Byte
      Offset 原格式不回退（test_lsu_obs_core 全量回归）。
- [x] 3. n=2 真实端到端：C04-F0-W6 现有 campaign 续跑 --samples 0 1 →
      COMPLETE + v2 审计 PASS。
- [x] 4. 提交 capacity 分支（本地），报告 commit。
