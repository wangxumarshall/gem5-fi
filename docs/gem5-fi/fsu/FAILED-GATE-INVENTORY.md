# 失败 gate / pilot 清单（2026-11-04，第二轮）

> 原则：不删除、不覆盖旧失败证据。下表记录路径、原因、大小与关键文件
> SHA-256。大体积原始目录**只留在服务器**，未进入 Git；本文件明确列出，
> 不能把“工作区 clean”理解为全部证据已推送。

| 目录 | 原因 | 大小 | 关键文件 SHA-256 | Git |
|---|---|---:|---|---|
| `runs/fsu-gates/F5-FP06-W5-GATE` | v1：`bitseg` 与显式 `fault_mask` 冲突 panic | 1.3 MB | `GATE.md` `e4696a7c…` | 未提交（小，可补） |
| `runs/fsu-gates/F5-FP06-W5-GATE-v2` | v2：PolyBench 全正结果使 sign SA0 不激活 | 1.7 GB | `GATE.md` `ab296c93…` | 未提交（大，留服务器） |
| `runs/fsu-gates/F5-FP06-W5-GATE-v3` | v3：单 bit 落在多 bit 字段时 `field_lo/hi` 标注错误 | 1.7 GB | `GATE.md` `36517755…` | 未提交（大，留服务器） |
| `runs/fsu-gates/F5-FP06-W5-GATE-v4` | v4：并发重建导致 gem5 二进制短暂缺失 | 684 MB | `GATE.md` `475aaeb2…` | 未提交（大，留服务器） |
| `runs/fsu-gates/F5-FR03-W5-GATE-s1` | target phys0/V0 触发 libc 路径崩溃，传播流截断 | 16 MB | `seed1/gate_report.json` `96f22509…` | 未提交 |
| `runs/fsu-gates/F5-FR03-W5-GATE-v2-s1` | target47 在 gate 路径崩溃（路径相关结局） | 17 MB | `seed1/gate_report.json` `dc1c42f8…` | 未提交 |
| `runs/fsu-gates/F5-FR03-W5-GATE-v3-s1` | target46：2mm 无 post-install 写/读 | 12 MB | `seed1/gate_report.json` `81043d0c…` | 未提交 |
| `runs/fsu-gates/F5-FR03-W5-GATE-s2` | 2mm mask `0x40000000` 未达激活 L5 | 15 MB | — | 未提交 |
| `runs/fsu-gates/F5-FR03-W5-GATE-s3` | 2mm mask `0x00010000` 未达激活 L5 | 15 MB | — | 未提交 |
| `runs/fsu-gates/F5-FR03-W6-GATE-s2` | SVD/sparse mask `0x40000000` 未达激活 L5 | 4.8 MB | — | 未提交 |
| `runs/fsu-gates/W6-F0-GATE` | v1：submodel `FP04-W6` 被字段审计拒绝；报告 KeyError | 4.1 MB | `gate_report.json` `64d84212…` | 未提交 |
| `runs/fsu-gates/FR03-W5-T47-PILOT` | `requireAllocated` 同 tick 重试写出 294,080,118 行 / 27.9 GB；为保护磁盘停止；日志无损 gzip 后 91 MB | 91 MB | `injection_log_storage.json` `14a80bfe…` | 未提交（大，留服务器） |

## 大文件位置与解压验证

- `runs/fsu-gates/FR03-W5-T47-PILOT/.../attempt-1/inject/fault_injections.log.gz`
  - 原始大小 27,937,611,210 B；原始 SHA-256
    `5feccf0daaf2a976af4570425e37d6c29868d343c505b202d03badb4ea0ec3ec`
  - gzip SHA-256
    `3b13fceeabd69affdbee0fb9ac7607ca297f2c43395cc840014d6c7001057fac`
  - 验证：`gzip -dc <file>.gz | sha256sum` 应等于原始 SHA-256。
- 上述 1.7 GB / 684 MB 目录中的原始 `fpu_injections.log` 未压缩，保持在
  `runs/fsu-gates/` 原位置；未进入 Git。
