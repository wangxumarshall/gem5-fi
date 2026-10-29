# T05-F2-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T05-F2-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T05`）
- fault type / 子模型：`valid_clear`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3 --cells T05-F2-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`9ef2a09c3645fb8dcb26b546337b7e37c2fffba4`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T09:25:41+08:00`，end=`2026-10-28T09:52:55+08:00`）
- 运行目录进程：gem5_pid=`3821450`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：3330（chain_report.event_count=`3330`）
- fault_id 数：666

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238095622710`，event_id=`0`
- 被改字段：`valid_clear`；before=`1`，after=`0`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: valid_clear (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: valid_clear (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238095622710, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238119323319, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238396924773, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483730, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238488895044, Site: arm_tlb_lookup_hit, VA: 0xffffff80013644d4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238599126036, Site: arm_tlb_lookup_hit, VA: 0x7ffedc42f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238751359983, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483a60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238976152632, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483bc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239096161503, Site: arm_tlb_lookup_hit, VA: 0xffffff800192cdf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239212314234, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483be0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239353479261, Site: arm_tlb_lookup_hit, VA: 0x7fe7c617e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239514329250, Site: arm_tlb_lookup_hit, VA: 0x7fe7c61b28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239615208270, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483d50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239776261389, Site: arm_tlb_lookup_hit, VA: 0x557542c8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239867413812, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a173c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240082962714, Site: arm_tlb_lookup_hit, VA: 0xffffff8001363408, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240283968840, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240455360277, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949be00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240601560597, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9fc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240778297350, Site: arm_tlb_lookup_hit, VA: 0x7fe80e23b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240857980587, Site: arm_tlb_lookup_hit, VA: 0x7fe80e2f58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240933579246, Site: arm_tlb_lookup_hit, VA: 0xffffff8001b9daf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241038045342, Site: arm_tlb_lookup_hit, VA: 0x7fe80e3a80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241188459777, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241422930072, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002dec0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241581874635, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241668316773, Site: arm_tlb_lookup_hit, VA: 0x7ff63fb680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241830922005, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c6488, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242067236454, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bce18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242246566278, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bce08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242344738008, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242507140443, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242693982081, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bcc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242810662284, Site: arm_tlb_lookup_hit, VA: 0xffffff8001d4d4f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243066091599, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493be0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243284620518, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493f68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243390175524, Site: arm_tlb_lookup_hit, VA: 0x7facb7bdac, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243483200739, Site: arm_tlb_lookup_hit, VA: 0x7ff8741b27, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243650872899, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243793545084, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243965102688, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000749a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244127485143, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bcf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244270917234, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5ad40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244386188514, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244489125474, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244568257929, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244683968436, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bc108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244742532147, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244830729195, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244947076065, Site: arm_tlb_lookup_hit, VA: 0xffffff800155b834, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245033189865, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b898, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245124089208, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245210824053, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245266889265, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245350871199, Site: arm_tlb_lookup_hit, VA: 0xffffff8003245f88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245426083911, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245476507437, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245517308262, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245572354827, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245621597868, Site: arm_tlb_lookup_hit, VA: 0x7fbd8145a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245680762311, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b860, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245893500693, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246009226185, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246190559337, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246350330739, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002dec8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246494211381, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246657561534, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 247417919748, Site: arm_tlb_lookup_hit, VA: 0x55699cf808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 247901971212, Site: arm_tlb_lookup_hit, VA: 0x55699cede4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 248697972414, Site: arm_tlb_lookup_hit, VA: 0x55699d2278, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249046877493, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bac8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249199859691, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249273882594, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249315352416, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249352425972, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249383499867, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249415305696, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00082288, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249449191776, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249474354921, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249502701879, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249537440439, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249570828351, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249597531621, Site: arm_tlb_lookup_hit, VA: 0xffffff80011ba1e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249636773340, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249696201519, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249754318011, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249778128177, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249820259337, Site: arm_tlb_lookup_hit, VA: 0xffffff8001446b6a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249867369180, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249924143682, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249973425351, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250084140192, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250126877079, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250187179716, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250237622556, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250291471320, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250326132624, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250381302732, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250411189149, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4760, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250454102193, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939b4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250482439827, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250506515727, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250567520994, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00091140, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250590643848, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250633396719, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250728784902, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250763060259, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250816730535, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250870416129, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250925267889, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250966905543, Site: arm_tlb_lookup_hit, VA: 0xffffff80014ae000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251011374696, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251074732275, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a8ff8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251100003978, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251134301979, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251188485408, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251212125411, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000a21c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251242218954, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251290705086, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251333498583, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda164, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251394089265, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251418370959, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251462317635, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251554950576, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251624261862, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251682905160, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd6c38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251725999023, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251791476813, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251883072792, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251960177277, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252079636365, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252280489311, Site: arm_tlb_lookup_hit, VA: 0xffffff800158bc48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252365197851, Site: arm_tlb_lookup_hit, VA: 0xffffff8001002a28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252479498769, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b578, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252531677205, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252627838614, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b648, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252720421272, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252766737576, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919b30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252867001545, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918c00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253003036374, Site: arm_tlb_lookup_hit, VA: 0xffffff8001be65c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253156020903, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a24, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253293288498, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd94, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253348166232, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c7b648, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253450248714, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253558835352, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253650042054, Site: arm_tlb_lookup_hit, VA: 0xffffff80014d1f90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253803172104, Site: arm_tlb_lookup_hit, VA: 0x7fda2d8530, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253912809024, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254036975067, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254154117474, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254219792733, Site: arm_tlb_lookup_hit, VA: 0xffffff8001afb820, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254316734694, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254405611062, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc5a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254473348590, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254512851381, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254615419044, Site: arm_tlb_lookup_hit, VA: 0x7fda2d8be0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254749944384, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254931366447, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255108149820, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2ab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255247030800, Site: arm_tlb_lookup_hit, VA: 0x5564154350, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255352957101, Site: arm_tlb_lookup_hit, VA: 0x5564152018, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255524191362, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255681163566, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255846316248, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255934057086, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256151341584, Site: arm_tlb_lookup_hit, VA: 0x5564154278, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256289906214, Site: arm_tlb_lookup_hit, VA: 0x55641518a4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256411017648, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256557862323, Site: arm_tlb_lookup_hit, VA: 0x556414f0b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256708317051, Site: arm_tlb_lookup_hit, VA: 0x55641550b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257202899640, Site: arm_tlb_lookup_hit, VA: 0x5564155368, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257389835517, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257566062780, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00065a80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257625877239, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257675989410, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257720338350, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257820791130, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257864605272, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257905312524, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257983828263, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258102443862, Site: arm_tlb_lookup_hit, VA: 0xffffffc008d03ba0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258183727164, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000968f4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258351457266, Site: arm_tlb_lookup_hit, VA: 0xffffff8001019328, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258537555315, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258604983819, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b620, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258650988768, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258745462200, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258803309295, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b478, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258838687215, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258961475970, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258999936138, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480608, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259114358601, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259221296889, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259332651423, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b430, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259375791906, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259560279234, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b568, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259615501623, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000688b4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259663521222, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259801271334, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b810, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259860333546, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259984163925, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260034098274, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260125938009, Site: arm_tlb_lookup_hit, VA: 0xffffff800191c250, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260215160031, Site: arm_tlb_lookup_hit, VA: 0x7f81df3318, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260319653766, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260459256024, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4758, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260567134371, Site: arm_tlb_lookup_hit, VA: 0xffffff800191d790, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260652529890, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b788, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260729228781, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260784854433, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260953582203, Site: arm_tlb_lookup_hit, VA: 0x5584347b30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261051039981, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261295958817, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261378173520, Site: arm_tlb_lookup_hit, VA: 0x558434af88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261463632642, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261622651464, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261709147215, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261878291568, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262095017292, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262178458101, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262336668066, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262509185709, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262741192137, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263112605019, Site: arm_tlb_lookup_hit, VA: 0x558434dbc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263537795736, Site: arm_tlb_lookup_hit, VA: 0xffffff800327fa70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263860168041, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493f10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263911341150, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263938562235, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263963125647, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264031212492, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00073380, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264067678656, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264178417140, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264223559619, Site: arm_tlb_lookup_hit, VA: 0xffffff80014ae248, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264250565253, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264328281126, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264379696992, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002e1c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264430426545, Site: arm_tlb_lookup_hit, VA: 0xffffff80011ba1e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264573258903, Site: arm_tlb_lookup_hit, VA: 0xffffff8001af4070, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264737403927, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264844623600, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264914581905, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265012359030, Site: arm_tlb_lookup_hit, VA: 0xffffff800191a480, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265130759844, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265175063829, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265339831563, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b440, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265431065904, Site: arm_tlb_lookup_hit, VA: 0xffffff800189d024, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265488268977, Site: arm_tlb_lookup_hit, VA: 0xffffff80019171d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265526259948, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265741172154, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265792642632, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b868, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265860860346, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265987645101, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266135974290, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266237705457, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266335700697, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b798, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266478164424, Site: arm_tlb_lookup_hit, VA: 0x7fb25f21c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266579556264, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266652864882, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266750564085, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b74e, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266817728187, Site: arm_tlb_lookup_hit, VA: 0xffffff800183ad60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266919747066, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266979648105, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267048294723, Site: arm_tlb_lookup_hit, VA: 0x55904b92f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267207609582, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267358964076, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267516757791, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267602547915, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267764783850, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267851492055, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267932093373, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2710, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268020677700, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268257171303, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268423704603, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268596470331, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268751404908, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2c70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268856108433, Site: arm_tlb_lookup_hit, VA: 0x55904bf99c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269275219236, Site: arm_tlb_lookup_hit, VA: 0x55904c2650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269626995774, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269878330188, Site: arm_tlb_lookup_hit, VA: 0xffffffc008beb594, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269991147924, Site: arm_tlb_lookup_hit, VA: 0x7ff8741a20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270134449479, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270195612588, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270241321167, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda170, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270294379389, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270408073914, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270459483120, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270517852359, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270590784354, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270735199794, Site: arm_tlb_lookup_hit, VA: 0xffffff80018ff150, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270914512635, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271010450934, Site: arm_tlb_lookup_hit, VA: 0xffffff8001914648, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271146528387, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271209995190, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271291279158, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003f18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271379283732, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271527187014, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c9ac1a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271629837261, Site: arm_tlb_lookup_hit, VA: 0xffffff8001840008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271715858487, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b408, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271782687258, Site: arm_tlb_lookup_hit, VA: 0xffffff8001b79c68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271894111389, Site: arm_tlb_lookup_hit, VA: 0xffffff800261d450, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271969210548, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272061399600, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c9122c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272194357509, Site: arm_tlb_lookup_hit, VA: 0xffffff8001408920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272297411019, Site: arm_tlb_lookup_hit, VA: 0xffffff8001433078, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272345288427, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272417133510, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272497197033, Site: arm_tlb_lookup_hit, VA: 0xffffff8001acd850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272592557244, Site: arm_tlb_lookup_hit, VA: 0x7fded845c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272726732934, Site: arm_tlb_lookup_hit, VA: 0xffffff8001acdd28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272788374231, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272884914261, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b530, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272927351448, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272993563503, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273053177496, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b770, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273126821778, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273200895630, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949baa0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273319436304, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273436815807, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273548240937, Site: arm_tlb_lookup_hit, VA: 0x5581dc3378, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273695968062, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273931592202, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274012899813, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c912b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274174356528, Site: arm_tlb_lookup_hit, VA: 0x5581dc26c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274397423904, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274478684229, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274646633778, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274809733515, Site: arm_tlb_lookup_hit, VA: 0x5581dc2ef8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274976796285, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275132281644, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275567222934, Site: arm_tlb_lookup_hit, VA: 0x5581dc2ea8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276010025022, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276129369891, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276289867899, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00070a48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276360509853, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276390402597, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276452465805, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276548208966, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00097a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276609113334, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b18c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276676969743, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276707533149, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276743499813, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276771329955, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276961580847, Site: arm_tlb_lookup_hit, VA: 0xffffff8000b89470, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277136652933, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277255754379, Site: arm_tlb_lookup_hit, VA: 0xffffff8001355b08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277364911779, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277413701274, Site: arm_tlb_lookup_hit, VA: 0xffffff80014e4cf6, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277496548677, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277553307861, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b720, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277649003736, Site: arm_tlb_lookup_hit, VA: 0xffffff80018cfcd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277763254371, Site: arm_tlb_lookup_hit, VA: 0xffffff8001408920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277837492725, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b590, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277878692484, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277924953843, Site: arm_tlb_lookup_hit, VA: 0xffffff80019187c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278017416288, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278157748482, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b978, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278240478669, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278323880850, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd68d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278440724889, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b568, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278489225340, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278599827960, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b720, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278647059015, Site: arm_tlb_lookup_hit, VA: 0xffffff8001917c98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278724432231, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278818892676, Site: arm_tlb_lookup_hit, VA: 0x7fe39a8718, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278988105294, Site: arm_tlb_lookup_hit, VA: 0xffffff80013621e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279105352263, Site: arm_tlb_lookup_hit, VA: 0xffffff800191bb5c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279215713458, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b1dc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279259222905, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279363813543, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279405998316, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279506311569, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279620604828, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279766773846, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279927404721, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280090022940, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949baf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280183373496, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280346272767, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361ce4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280510534341, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280676637072, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280836270279, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281009243799, Site: arm_tlb_lookup_hit, VA: 0x5583bce638, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281241773037, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281536402446, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282150743157, Site: arm_tlb_lookup_hit, VA: 0xffffffc008d03b60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282357056970, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282543383457, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282586566564, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00050990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282629401686, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282691954071, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282792513078, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282844441098, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b2b58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282910226913, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282957340752, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283042358982, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283335647067, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b510, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283390928730, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4720, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283468296618, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364ed8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283563011475, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b560, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283628470950, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc3b, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283692500523, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283762262025, Site: arm_tlb_lookup_hit, VA: 0xffffff8001840000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283853099430, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283980998736, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00074840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284028856497, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b660, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284102624988, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b540, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284141502738, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284224499325, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284413246722, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284491967256, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b780, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284564062089, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284619640122, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284759224731, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284801895684, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284859189333, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bcd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284927028093, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285010806897, Site: arm_tlb_lookup_hit, VA: 0x7fab928328, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285158835054, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285237237573, Site: arm_tlb_lookup_hit, VA: 0xffffff800191b0c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285334047666, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285380335332, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c7b410, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285496579971, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285564358125, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c6941a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285679349352, Site: arm_tlb_lookup_hit, VA: 0x7fcab14136, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285797358225, Site: arm_tlb_lookup_hit, VA: 0x55b32d2350, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285924530259, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286097598018, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286212592575, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286377720615, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286535275236, Site: arm_tlb_lookup_hit, VA: 0x55b32d7508, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286625243511, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286782552711, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286951759335, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287121849408, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287284460301, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287450779815, Site: arm_tlb_lookup_hit, VA: 0x55b32d6f30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287811095139, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c698b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288164842038, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288422447841, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288608545557, Site: arm_tlb_lookup_hit, VA: 0x7ff8741be0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288695473209, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288725413572, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288786783141, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288829798083, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288925770681, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493998, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288958437315, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288991948437, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289045351647, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289100476467, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289155698523, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289208372796, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289477159074, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289552191300, Site: arm_tlb_lookup_hit, VA: 0xffffff8001395814, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289586215575, Site: arm_tlb_lookup_hit, VA: 0xffffff8001562778, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289675639395, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289716007986, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289782590670, Site: arm_tlb_lookup_hit, VA: 0xffffff800191a6e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289892818332, Site: arm_tlb_lookup_hit, VA: 0xffffff80014810f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289939998771, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290020818537, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290086518438, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290215508985, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290290694058, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b400, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290329303743, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290508222645, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbe8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290600464977, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b720, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290713413915, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480c28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290794636611, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919320, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290932449327, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b760, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290999403306, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291122405181, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bce0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291333657384, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291414152475, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291548389104, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd46f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291632647428, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b5488, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291707044623, Site: arm_tlb_lookup_hit, VA: 0xffffff8001911c48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291794514399, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003dd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291886635519, Site: arm_tlb_lookup_hit, VA: 0x7fe2650f20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292033130211, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292193916264, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292364378298, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292449233691, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292616121636, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2a70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292745890071, Site: arm_tlb_lookup_hit, VA: 0x55aa2f1d58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292869955881, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292952421000, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293186794392, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293351053302, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293521957227, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293821279605, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293971525875, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294333007365, Site: arm_tlb_lookup_hit, VA: 0xffffff800155ba88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294744698595, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bba0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294902375760, Site: arm_tlb_lookup_hit, VA: 0xffffff800158bae8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294941521242, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006f188, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295006099266, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493968, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295041962367, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295099539066, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295209696132, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3df0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295244231229, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295267094010, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295326189855, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295368088248, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295431003270, Site: arm_tlb_lookup_hit, VA: 0xffffff800197b600, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295601858577, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295765851087, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006ff08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295823179035, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295966830906, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b600, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296012413944, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b430, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296101014255, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296186521329, Site: arm_tlb_lookup_hit, VA: 0xffffff80011953de, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296315775945, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b410, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296390766879, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b280, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296445712545, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00074848, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296538659172, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296748426861, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b748, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296828413128, Site: arm_tlb_lookup_hit, VA: 0xffffff800191a4e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296977533858, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b848, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297094675266, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b760, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297152630586, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b780, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297201281553, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297265551552, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297307111617, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297395126514, Site: arm_tlb_lookup_hit, VA: 0x7f820c6000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297541682478, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b540, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297678440250, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297724590720, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297789239340, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297858004839, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297913459329, Site: arm_tlb_lookup_hit, VA: 0xffffff8001912e50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297973159236, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298104973956, Site: arm_tlb_lookup_hit, VA: 0x7fd3038888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298197997173, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298275357402, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298449874710, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298607774652, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298773412182, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298863100404, Site: arm_tlb_lookup_hit, VA: 0x55c85991f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299014155531, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299183245272, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299344459896, Site: arm_tlb_lookup_hit, VA: 0xffffff80031eaa90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299429215056, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299592706068, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299674120572, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299912884236, Site: arm_tlb_lookup_hit, VA: 0xffffff8003224e30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300289727682, Site: arm_tlb_lookup_hit, VA: 0x55c8593b50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300566313819, Site: arm_tlb_lookup_hit, VA: 0xffffff800326e740, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300851352495, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493fb8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300914925525, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301057104537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301128813756, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301163949918, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301214690793, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301236941520, Site: arm_tlb_lookup_hit, VA: 0xffffff8001432908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301269965796, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301349703312, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301412189430, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301457383524, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0009f6c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301538720772, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3e00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301611560859, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301735584711, Site: arm_tlb_lookup_hit, VA: 0xffffff800194a708, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301944305781, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301979187864, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b100, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302100879051, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302143978575, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c91b48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302226907896, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302361040629, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302439008916, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302569184943, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302656360680, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302710283703, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006b888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302877352800, Site: arm_tlb_lookup_hit, VA: 0xffffff80019d9bc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303013350999, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc4f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303136076484, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303206733756, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303301483245, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b820, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303410560392, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303464027538, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bfb8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303589306134, Site: arm_tlb_lookup_hit, VA: 0x7fb1ef953c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303667271757, Site: arm_tlb_lookup_hit, VA: 0x7fb1d5edfc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303802347879, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303922514925, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303966063999, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304068872421, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304123698873, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304147994886, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304312102281, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304442678907, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304614182898, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304785711531, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304952462613, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305116707537, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305199853641, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305367392934, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305530216614, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305675408943, Site: arm_tlb_lookup_hit, VA: 0x559ca4e4e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305771309280, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305851544298, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306086966973, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306243190926, Site: arm_tlb_lookup_hit, VA: 0xffffffc008be6980, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306768215709, Site: arm_tlb_lookup_hit, VA: 0x559ca48690, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307161717813, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307333023669, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493878, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307380469842, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307440088830, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307498422771, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307607783301, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c6e88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307627456275, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307694525139, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307752277662, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307805163723, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00098388, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307871961858, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308035781874, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bcb0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308205632187, Site: arm_tlb_lookup_hit, VA: 0xffffff800183adb4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308243412702, Site: arm_tlb_lookup_hit, VA: 0xffffff8001afb728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308342806209, Site: arm_tlb_lookup_hit, VA: 0xffffff8001b5f808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308424949983, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b470, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308496206988, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308582313462, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00075fc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308629277118, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308764093167, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918500, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308804381505, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308870318502, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b450, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308931612147, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309005953731, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309169877310, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b820, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309248918856, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bd24, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309347930079, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b810, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309404457495, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b630, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309523872627, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b818, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309573398718, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309617226180, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309716576064, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309838046805, Site: arm_tlb_lookup_hit, VA: 0xffffff80013651d4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309948622119, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b690, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309991790574, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310140977571, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310208482332, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310294328067, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b800, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310372518798, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310422711222, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc4f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310552821981, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310631334723, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310838099751, Site: arm_tlb_lookup_hit, VA: 0x558cc5d350, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311013618723, Site: arm_tlb_lookup_hit, VA: 0x558cc56558, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311109595650, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311267349405, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311436277641, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311590774656, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311754282984, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311873744403, Site: arm_tlb_lookup_hit, VA: 0x558cc58d08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312085679589, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312321209823, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312674892120, Site: arm_tlb_lookup_hit, VA: 0x558cc5c500, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312906559554, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313295500890, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313431366555, Site: arm_tlb_lookup_hit, VA: 0x7ff87419c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313642406637, Site: arm_tlb_lookup_hit, VA: 0xffffff8001d96840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313778469438, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313888728402, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313934432985, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313988496534, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314045922717, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314169575274, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314271177903, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314353564434, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b610, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314422635960, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314480809395, Site: arm_tlb_lookup_hit, VA: 0x7fe95d8da8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`2663`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 3330 个事件，为可读性第 3 章只逐条叙述**主链** 4 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=2660`，`tick=314480809395`，`corr=origin`，`request_id=361577749`，`dyn_inst_seq=361577749`，`field=valid_clear`，`before=1`，`after=0`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=2661`，`parent_event_id=2660`，`tick=314480809395`，`corr=seq_primary`，`request_id=361577749`，`dyn_inst_seq=361577749`，`walk_id=0`，`va=7fe95d8da8`，`entry_index=9`，`way=-1`，`field=post_lookup`，`before=1`，`after=0`，`state_before=vpn=7fe95d8;asid=15;valid=1;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8`，`state_after=vpn=7fe95d8;asid=15;valid=0;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8`
  该事件把 TLB 表项的状态/字段从 `vpn=7fe95d8;asid=15;valid=1;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8` 变为 `vpn=7fe95d8;asid=15;valid=0;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2662`，`parent_event_id=2661`，`tick=314480809395`，`corr=seq_primary`，`request_id=361577749`，`dyn_inst_seq=361577749`，`va=7fe95d8da8`，`field=valid_clear`，`state_before=1`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `1` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=2663`，`parent_event_id=2662`，`tick=314480809395`，`corr=seq_primary`，`request_id=361577749`，`dyn_inst_seq=361577749`，`walk_id=0`，`va=7fe95d8da8`，`pa=825f0da8`，`entry_index=9`，`way=-1`，`field=effective_pa_unchanged`，`before=825f0da8`，`after=825f0da8`，`state_before=vpn=7fe95d8;asid=15;valid=1;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8`，`state_after=vpn=7fe95d8;asid=15;valid=0;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `825f0da8` 变为 `825f0da8`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 2660 | `inj` | L0 | CHAOSArmTLB | `361577749` | `—` | `1` → `0` |
| 2661 | `tlb_lookup` | L1 | DTLB CAM | `361577749` | `7fe95d8da8` | `vpn=7fe95d8;asid=15;valid=1;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8` → `vpn=7fe95d8;asid=15;valid=0;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8` |
| 2662 | `tlb_state` | L2 | DTLB 表项 | `361577749` | `7fe95d8da8` | `1` → `0` |
| 2663 | `tlb_translate_result` | L2 | MMU 翻译 | `361577749` | `825f0da8` | `vpn=7fe95d8;asid=15;valid=1;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8` → `vpn=7fe95d8;asid=15;valid=0;global=0;pfn=825f0;ap=1;mtype=2;page_size=1000;pa=825f0da8` |


（第 4 章仅逐条列出主链 4 个事件；其余 3326 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `inj` | 666 | 0 | 2660 |
| `tlb_lookup` | 666 | 1 | 2661 |
| `tlb_state` | 666 | 2 | 2662 |
| `tlb_translate_result` | 666 | 3 | 2663 |
| `chain_end` | 666 | 2664 | 3329 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
2660(inj) → 2661(tlb_lookup) → 2662(tlb_state) → 2663(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 2660 | — | 314480809395 | `origin` | `361577749` | 666 |
| 2661 | 2660 | 314480809395 | `seq_primary` | `361577749` | 666 |
| 2662 | 2661 | 314480809395 | `seq_primary` | `361577749` | 666 |
| 2663 | 2662 | 314480809395 | `seq_primary` | `361577749` | 666 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=2663），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`valid_clear` 把被命中表项的 valid 位由 1 改为 0。该表项在本次查询**已经被匹配**（`tlb_lookup` 显示的是 post_lookup 状态），因此本次翻译仍用它原来的 pfn 完成；被清零的位只可能影响**之后**对同一 VPN 的查询（本流未观测到再次查询；因有效 PA 未变，本型号**不开**关联臂，`corr=seq_primary` 只是标签，链如实止于 L2）。因此本次翻译的有效 PA 不变、无下游 L3+ 事件，结局是 L2 `effective_pa_unchanged` 含住（Masked）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`66271205`，eligible=`66271205`，injected=`666`（日志应用行 666 条），activated=`666`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/prop_evt.txt.gz` — SHA-256 `3dcaf3825b794be2d51ca80fc31e88021a46fa94e07fae986e7927f9fbf6f3b6`（140850 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/chain_report.json` — SHA-256 `1631cbf0fd1f1184c692644fdd3aae96446457f627b1f49cfd38230715e7267d`（503882 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/stats.txt` — SHA-256 `a8b3705dd12cc062cf1522a21eabae3d7e6abf8db5b0c9b753941aba51dd9556`（427682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/run.out` — SHA-256 `098a64b99be8ba3d2c67d2835fdfa7c4f565d9e565c83ae5b833773d14df1f32`（70220 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/run.err` — SHA-256 `75c8553cca8d0a645f25adaf093fffa9cd6ef8994e4a526426801917f0e59e6e`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/T05-F2-W4/seed3/armtlb_injections.log` — SHA-256 `317f03814a1e7c5c4498992fabecee0c546cd06e367947c8decfa4b4aa46329b`（88576 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3/manifest.json` — SHA-256 `4b50664d384f01a8537785cb7de87154c57446c89e25915bcb2e63b31469b3de`（2110 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

