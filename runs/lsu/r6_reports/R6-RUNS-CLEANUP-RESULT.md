# runs/lsu 清理结果（本轮未删除任何内容）

- 生成时间 `2026-10-27T17:56:12`
- 清理计划 DELETE 候选：**0**（KEEP_AUTHORITATIVE 41 / KEEP_SUPPORT 9 / REVIEW_REQUIRED 106）
- 实际删除：**无**；释放：**0 B**
- 原因：清理计划中 DELETE_DUPLICATE / DELETE_INTERRUPTED 均为 0：权威索引只对 seed 级路径做了重复判定，runs/lsu 下的顶层遗留目录无法按第 9 节条件证明可安全删除，故全部标 REVIEW_REQUIRED 并保留。
- `df -h /home`：`/dev/mapper/openeuler-home  354G  266G   70G   80% /home`；`du -sb runs/lsu` = 820,423,234 B
- 传播路径 MD：**51 份**；权威证据：见 `R6-AUTHORITATIVE-EVIDENCE.json`（51 seed）
- 清理前后权威证据零变化（未删除即零风险）。