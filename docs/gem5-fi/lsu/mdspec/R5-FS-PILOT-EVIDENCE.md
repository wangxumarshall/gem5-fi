# R5 集成后 FS 真机 pilot 证据（2026-10-22）

> 目的：为"FS-INFRA 是否真的需要 FS 基础设施"这一判据提供**集成后**的真实运行证据。
> 之前该判据只有集成前的 `runs/lsu/trial_r48_fs/*`（R4-8 时代）与散文陈述。

## 环境（如实记录）

| 项 | 值 |
|---|---|
| 二进制 | `<worktree>/CHAOS/gem5/build/ARM/gem5.opt` sha256 `f4dbfb9a66e0df80…`（R4-10 集成轮构建） |
| 资产 | `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（worktree 内 `gem5-fs/` 为空，须显式指定） |
| checkpoint | `/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| 入口 | `tools/lsu_campaign.py --cells T01-F0-W4 --phase trial --max-seeds-per-cell 1 --max-parallel 1 --fs-timeout 2700` |

## T04-F0-W4 — 完整 L0→L5 链（真机，本轮）

```
"runid": "T04-F0-W4", "phase": "trial", "n_runs": 1, "activated": 1,
"classes": {"Masked":0,"Detected/Contained":0,"SDC":0,"Crash":1,"Timeout":0},
"stop_reason": "seed-cap(1)", "conservation": "OK"
run seed=1 activated=1 outcome=Crash event_count=1572
  L0->L1 proven  L1->L2 proven  L2->L3 proven  L3->L4 proven  L4->L5 proven
  terminal=full provable_to=L5
```

⇒ **"FS 载体在预算内不终止 → 无 L5" 对该格不成立**：T04-F0-W4 在预算内自然终止，
给出 `Crash` 结局与完整五段链。

## T01-F0-W4 — 真实注入（真机，本轮；运行未终止，与 R4-8 观测一致）

```
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
old_pfn: 0x81d75, new_pfn: 0x100000000081d75, FaultType: bit_flip, Mask: 0x100000000000000
```

⇒ FS TLB 注入链在当前二进制下**真实生效**。

## 结论（不夸大）

- FS 基础设施**可用**：注入真实、链可推进，且至少一格的 L5 分类可达。
- 但**不等于** FS-INFRA 24 格可准入：T05/T06/T07/T08 为本轮新实现模式、T10 PPN 分层未参数化，
  均**无逐格真机 pilot**；且 `TLB-AliasPerm` 为 workload 级静态键，整批拒绝该负载。
- 因此本轮**维持 24 格 BLOCKED**，但把理由措辞由已被反驳的"需 FS 基础设施"
  更正为"逐格 campaign 入口 pilot 未完成"（见 `blockers_for_approval.md`）。
- **未**通过删除 `TLB-AliasPerm` 键（会一次性把含未 pilot 新模式的 24 格全部转为 READY）
  来制造准入 —— 那属 GO-CORRECTION 明令禁止的"改分类/放宽阈值制造 GO"。

## 复现命令

```bash
cd <worktree>
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt \
LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/r5_fs_pilot/out --cells T04-F0-W4 --phase trial \
  --max-seeds-per-cell 1 --max-parallel 1 \
  --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 \
  --fs-timeout 2700
```
