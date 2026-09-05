# Progress Log

## Session: 2026-09-05 (5 new dumps batch)

### Current Status
- Phase 1 complete (main-session triage)
- Phase 2 in progress: cases 14/15/17 reports done; cases 13 & 16 have crash forensics
  (15 & 19 sessions respectively) but reports NOT yet written — this session (2026-09-05 evening)
  completes them serially (host has only ~4G free, crash sessions must be serialized).
- Session continuation log: 2026-09-05 evening session resumed; verified env
  (crash 8.0.4, vmlinux-0102 present, both vmcores present); plan updated.

### Phase 1 主会话初筛结论（全部实证）
| 案 | 转储 | CPU | uptime | 前兆 | 致命签名 | 特色 |
|---|------|-----|--------|------|----------|------|
| 13 | 21:53:28 | 179 | 33272s | 13 WARNING+13 spurious | mi-scavenger, FBG+0x140, x27=73b8...(hi16 7位翻转) | 最长存活 9.2h |
| 14 | 22:09:49 | 168/169/180/50/55 | ≥397s(截断) | 458+ list corruption | CPU180 Oops FAR=ffffb75e...; CPU179 x27=FAR-0x120 | **多核级联/持久写坏** |
| 15 | 22:27:27 | 179 | 552s | 4 WARNING+4 spurious | rcu_sched, FBG+0x140, x27=00ff...(hi16 8位翻转) | incomplete + 内核线程受害 |
| 16 | 22:39:38 | 179 | 347s | 8 WARNING+8 spurious | NetworkManager, FBG+0x140, x27=ffff..bda5..(hi16完好) | 极短存活 + spurious 地址聚集 |
| 17 | 23:37:57 | 179 | 2838s | **0 WARNING** | systemd-coredum, get_pfnblock_flags_mask+0x3c, x3=0 | **读出SDC直接实锤** |

### 关键实证
1. 案13/15/16: FAR - x27 = +0x120 全部闭合（python3 验证），致命指令 f9409377 = LDR x23,[x27,#0x120]
2. 案14: crash rd 读出 ffff6057fffbe990 处 prev=ffffd8101333948（vmemmap struct page 地址 = 同类指针替换签名）；
   per_cpu_offset[168]=0xffffc8a2436be000, [179]=0xffffc8a243834000 (stride 0x22000)
3. 案17: mem_section root=0xffff6057fffafb00, [0xc08]=ffff6057fffaeb00 非零，section_mem_map=0xfffffc000000000f 有效；
   但寄存器转储 x3=0 → load 读出≠内存真值
4. 5 案 dmesg 均无 RAS/EDAC/mce 记录（负证据）

### Actions Taken
- 确认 5 个新转储（09-04 21:53–23:37）无既有报告；12 个旧转储已有报告（不动）
- 建计划 .planning/2026-09-05-vmcore-cases-5newdumps/task_plan.md
- 切分支 research/vmcore-cases-5newdumps-0940batch
- 派发 5 个独立后台 subagent（每案一个，独立报告目录）

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| crash 加载案17 vmcore | bt 输出 | bt 完整 35 帧 | pass |
| crash 加载案14 vmcore | rd 读出 | rd 成功 | pass |
| crash 加载案17 (incomplete 未见) | - | - | - |

### Errors
| Error | Resolution |
|-------|------------|
