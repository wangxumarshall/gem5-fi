# LSU 并发提升规程（4→6→8）Runbook — 2026-10-12

- 起草：Subagent-B（OBS-4/4b/8b，worktree `lsu-obs-b` 分支 `obs-sub-b`）。
- 执行人：**服务器总负责人**（本 runbook 只描述操作，不起 gem5）。
- 判据来源：用户指令 2026-10-12 三.2-3（30 分钟连续资源门 + TRIP 降档 + 0101 磁盘
  红线），实现于 `tools/lsu_hostmon.py::decide_cap`（提交 `[LSU][OBS-4]`，本分支）；
  RAMP6 判据于 `[LSU][OBS-4c]` 收紧为连续槽闲置、`[LSU][OBS-4e]` 收紧为**连续 ≥15 拍**（2026-10-12 17:35:29
  换样间隙单拍 slots_held=3 误触发 cap4→6，实证修正）。
- 并发竞争验收（阶段一验收 G）已通过：`tests/test_claim_concurrency.py` 19/19
  PASS（提交 `[LSU][OBS-4b]`）：claim 唯一性 / 槽竞争（SLOTS=2 恰好 2 成功）/
  run 并发上限（SLOTS=3 峰值=3、15 次竞争拒绝零突破）/ 心跳 5s 更新。

## 0. 事实基线（2026-10-12 17:15-17:35 实测）

| 项 | 值 |
|---|---|
| 内存 | 29 GiB，MemAvailable ≈ 22 GiB；**仅 NUMA node1 有内存**（numactl --cpunodebind=1 --membind=1） |
| Swap | SwapTotal 15.59 GiB，SwapFree ≈ 14.85 GiB |
| /home | 354 GiB 总量，free ≈ 153.6 GiB；guard 磁盘红线 = max(50, 20%) = **70.8 GiB** |
| /tmp | tmpfs 15 GiB，free ≈ 12 GiB（**低于磁盘红线**：guard 目录不得放 /tmp） |
| 槽位 | 4/4 被 `p4_agu_formal_20261012` 四实例 driver 占用（python3 PID **1995570 / 1995598 / 1995622 / 1995696**，勿动）；锁目录 `runs/lsu/guard` |
| hostmon | 常驻 python3 PID **2107378**（nohup，OBS-4c 重启，输出 `runs/lsu/obs/hostmon/`） |
| W1 Masked 种子 | **不存在**：`runs/lsu/pilot_w1` 已有 1124 份 l5_verdict 全部 outcome=Crash（2026-10-12 17:15 扫描）→ §3 首选路径当前不可用，走回退路径 |

## 1. 前置条件（全部满足才可升 6）

1. **E2E PASS 已交中央**（OBS 计划 Task 5 `handoff_e2e`；未获中央 PASS 不启动）。
2. **≥1 生产 driver 退出且槽确已空**：双重核验——
   ```bash
   cd /home/sdc/gem5-fi-ding && LSU_GUARD_DIR=runs/lsu/guard python3 tools/lsu_guard.py status
   # 该槽锁消失或 live=false；
   tail -1 runs/lsu/obs/hostmon/hostmon_*.jsonl | python3 -c "import json,sys; print('slots_held =', json.loads(sys.stdin.read())['slots_held'])"
   # slots_held 同步 <4（hostmon 与 guard 双源一致）
   ```
3. **hostmon 常驻在跑**：`slot_policy.json` 的 `updated` 距今 <2 分钟，JSONL 每分钟
   追加一行；`ps -p 2107378` 存活（若已死：§附录 A 重启，历史窗口从 JSONL 自动续）。

## 2. 槽位策略机制：hostmon 自动判定 + 手动 seed 合规途径

- **自动（首选）**：hostmon 每拍跑 `decide_cap`。RAMP6 判据（OBS-4c 收紧）=
  `cap==4` 且**连续 ≥15 拍** `slots_held < 4`（持续闲置=driver 退出；OBS-4e 2026-10-13：3 拍区分不了换样/item 间隙（实测 05:56-05:58 三连拍全为存活 driver 换样间隙，误触 4→6→8），15 分钟连续闲置只有真退出能造成；生产换样
  间隙 <60s 只闪断 1 拍，不触发——2026-10-12 17:35:29 单拍闪断误触发实证）
  且最新拍 `mem_available_gib ≥ 12` → `slot_policy.json` 翻为
  `{"cap":6,"state":"RAMP6"}`。
- **手动 seed（合规途径，全程留痕）**：hostmon **只在启动时**读 `slot_policy.json`
  的 `cap` 作初值，运行中每拍重写该文件——因此手动改值必须走"停→改→重启"：
  ```bash
  kill 2107378                                # 1) 停 hostmon（记录停机时刻）
  python3 - <<'EOF'                           # 2) 改 cap（reason 必须写授权与证据）
  import json, time
  p = "/home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/slot_policy.json"
  d = json.load(open(p))
  d.update({"cap": 6, "state": "RAMP6",
            "reason": "manual_seed: <授权人+理由+触发证据（slots_held/mem 实测值）>",
            "updated": time.strftime("%F %T")})
  json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
  EOF
  #  3) 重启（obs-sub-b 合并进主树前用 worktree 路径，合并后用主树路径）
  cd /home/sdc/gem5-fi-ding && LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
    nohup python3 tools/lsu_hostmon.py --interval 60 \
    --out /home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon \
    >> /home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/hostmon.nohup.log 2>&1 &
  #  重启后自动从 hostmon_*.jsonl 尾部续历史（30 分钟 RAMP8 窗口不重置）
  ```
- **驱动侧生效**：`slot_policy.json` 的 cap 是声明性产物；真正生效 = **新启动**的
  driver 带 `LSU_GUARD_SLOTS=<cap>`（obs_driver 亦可 `--slots <cap>`）。已在跑的
  driver 保持其启动时槽数（只持有 ≤4 槽，安全）；升/降档都不影响在跑样本。

## 3. 长时负载来源（升档观察窗的槽位填充）

按用户指令 2026-10-12：优先 (1) 既有 W1 Masked 种子重放；否则 (2) no-fault W1
golden 工程重跑。两路都经 `lsu_obs_driver.py`（W1 Phase A 强制 `--obs-mode l0l5`，
全量 ctrace 体积不可行——驱动内置诚实降级，`coverage_scope=none_full_run_forbidden_
pending_phaseB`）。

**(1) 发现并重放 W1 Masked 种子**（当前 1124 份全 Crash，此路径暂不可用；种子出现
后按此执行）：
```bash
# 发现（列出 outcome==Masked 的 W1 样本；输出空=仍无种子）
python3 - <<'EOF'
import json, glob
for p in sorted(glob.glob('/home/sdc/gem5-fi-ding/runs/lsu/pilot_w1/ITEM-*/ITEM-*_s*/l5_verdict.json')):
    v = json.load(open(p))
    if v.get('outcome') == 'Masked':
        print(p, 'attempted=', v.get('attempted'), 'activated=', v.get('activated'))
EOF
# 重放（<W1-ITEM> 如 ITEM-003，<S> 为上一步样本号 sN 中的 N）
cd /home/sdc/gem5-fi-ding
LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/build/ARM/gem5.opt \
PYTHONHASHSEED=0 LSU_GUARD_SLOTS=6 \
python3 tools/lsu_obs_driver.py \
  --items <W1-ITEM> --phase screening \
  --campaign obs_ramp6_$(date +%Y%m%d) \
  --samples <S> --replay-policy per_sample \
  --obs-mode l0l5 --outdir-root runs/lsu/obs
```

**(2) 回退：no-fault W1 golden 工程重跑（双份，兼作 Phase B baseline 预热）**。
golden 缓存按 `<outdir-root>/golden/<baseline_key>/` 存放，同 root 同 key 只算
一份——**双份必须用不同 `--outdir-root`**：
```bash
cd /home/sdc/gem5-fi-ding
# 第一份
LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/build/ARM/gem5.opt \
PYTHONHASHSEED=0 LSU_GUARD_SLOTS=6 \
python3 tools/lsu_obs_driver.py --items ITEM-003 --phase screening \
  --campaign obs_ramp6_golden_a_$(date +%Y%m%d) --target 1 \
  --obs-mode l0l5 --outdir-root runs/lsu/obs
# 第二份（独立 outdir-root → 独立 golden 缓存）
LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/build/ARM/gem5.opt \
PYTHONHASHSEED=0 LSU_GUARD_SLOTS=6 \
python3 tools/lsu_obs_driver.py --items ITEM-003 --phase screening \
  --campaign obs_ramp6_golden_b_$(date +%Y%m%d) --target 1 \
  --obs-mode l0l5 --outdir-root runs/lsu/obs_ramp6_b
```
（工程判断备注：新起 `lsu_w1_rerun.py` formal 实例带 `LSU_GUARD_SLOTS=6` 延续
`p4_agu_formal_20261012` 亦是等效长载荷——四实例本就持续换样占槽；是否采用由
总负责人裁量并记录。）

## 4. 执行步骤（4→6）

1. 核对 §1 三项前置（E2E PASS 交中央 / 槽确已空双源核验 / hostmon 在跑）。
2. 等待或触发 RAMP6（§2）：确认 `slot_policy.json` → `"cap":6,"state":"RAMP6"`。
3. 以 `LSU_GUARD_SLOTS=6` 启动 §3 负载（新 driver 占第 5 槽——降序抢占先占高位槽
   5/4，与旧 driver 的 0..3 不冲突）。
4. 进入观察窗（§5）≥30 分钟（建议 60）：新槽位持续有载荷、hostmon 逐拍记录。
5. 观察窗结束且全程无 TRIP/警告 → 维持 cap 6 继续生产；升 8 另按 §6 判据。

## 5. 观察窗（30-60 分钟）记录项

**hostmon 每 60s 自动记录**（`runs/lsu/obs/hostmon/hostmon_YYYYMMDD.jsonl`，每拍
一行，勿手工编辑）：
`t` / `gem5_procs[{pid,rss_gib,cpu_pct,etime_s}]` / `mem_available_gib` /
`swap_free_gib` / `committed_as_gib` / `si_ps` / `so_ps`（vmstat pswpin/pswpout
差分÷间隔秒，页/s；启动后首拍为 null=缺测）/ `load_1` / `blocked_n` / `gem5_n`
（排除 Z 僵尸）/ `home_free_gib` / `tmp_free_gib` / `obs_growth_gib`（相对窗口
首拍的 /home 消耗）/ `slots_held`（主锁目录活锁数，glob 含高位槽）。

**总负责人每 5-10 分钟人工核查**：
```bash
cat /home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/slot_policy.json    # cap/state/evidence
EV=/home/sdc/gem5-fi-ding/runs/lsu/guard/guard_events.log
# 观察窗开始时记录基线：W0=$(grep -c '"warning": true' $EV); T0=$(grep -cE '"trip": "[^n]' $EV)
grep -c '"warning": true' $EV                  # 与基线 W0 差值=观察窗内新增 warning
grep -E '"trip": "[^n]' $EV | tail             # 非 null TRIP（基线 T0 之后必须无新增）
dmesg -T | grep -i "out of memory\|oom" | tail # 必须无新条目
df -h /home                                    # free > 70.8 GiB 红线
```
（注意：`grep '"trip":'` 会匹配全部 `"trip": null` 常规采样行——历史累计约 2.1 万条，
必须用 `'"trip": "[^n]'` 过滤非 null；`guard_events.log` 中存在 2026-10-12 之前的
历史 TRIP 记录（如 `MemAvailable<6GiB (4.37)`，pgid 900810），判定只看观察窗内新增。）
核查要点：`gem5_n ≤ slots_held`（换样间隙可短暂偏小）；`si_ps/so_ps` 持续为 0；
`blocked_n` 恒 0；`obs_growth_gib` 增速可控（<1 GiB/10min）。

## 6. 升 8 判据（= `decide_cap` RAMP8，hostmon 自动判定）

`cap==6` 且最近**连续 ≥30 拍（30 分钟）**全部满足：
- `mem_available_gib ≥ 16`，`swap_free_gib ≥ 8`；
- 无连续 >5 拍 `si_ps>0` 或 `so_ps>0`（偶发换页 ≤5 拍可容忍）；
- `blocked_n` 全 0；
- /home 任意 10 拍（10 分钟）增量 <1 GiB。
满足 → `slot_policy.json` 翻 `"cap":8,"state":"RAMP8"` → 新 driver
`LSU_GUARD_SLOTS=8`。任一不满足 → 维持 6（`reason` 字段给出具体否决理由）。
本阶段硬上限 8（用户指令 2026-10-12 三.3）。

## 7. TRIP 降档动作（hostmon TRIP_DOWN；不停健康样本、仅停新派发）

TRIP 条件（窗口内任一）：`mem<8 连续 2 拍`，或 `任一拍 mem<6`，或
`任一拍 swap_free<2` → `slot_policy.json` 翻 `"cap": max(4, cap-2),
"state":"TRIP_DOWN"`。
执行语义：
- **已运行样本不动**：guard 的 run 级 TRIP 只杀锁内自家 PGID；hostmon TRIP_DOWN
  只降声明 cap，绝不 kill 任何进程。
- **仅停新派发**：新 driver 以降后 cap 启动（`LSU_GUARD_SLOTS=<降后值>`）；
  MemAvailable<10 GiB 时 guard STOP_DISPATCH 直接拒绝新 experiment acquire。
- 恢复：TRIP 事件滚出 hostmon 60 拍窗口且 §2 RAMP6 判据满足（槽闲置 + mem≥12）
  → 自动回升 6；再升 8 须重建完整 30 拍 RAMP8 窗口。

## 8. 回退到 4 的条件（任一即回退；动作同 §2 手动 seed，cap 改 4）

- `guard_events.log` 出现任何 run 级 TRIP 事件；
- hostmon `state=TRIP_DOWN` 持续 ≥5 拍（约 5 分钟）未恢复；
- `MemAvailable < 10 GiB` 持续 ≥5 分钟（STOP_DISPATCH 区间）；
- `si_ps>0 或 so_ps>0` 连续 >5 拍；
- dmesg 出现 OOM-kill 证据；
- /home 增速 ≥1 GiB/10min 且观察窗内无收敛迹象，或 free 逼近 70.8 GiB 红线；
- `blocked_n` 持续非 0；
- 总负责人裁量判断（必须在 slot_policy.json 的 reason / handoff 记录理由）。
回退后：等待在跑样本自然结束（不 kill）；槽回落 ≤4 后 hostmon 依 §2 判据择机
再升。

## 9. 记录产物路径与 handoff 摘要字段

| 产物 | 路径 |
|---|---|
| hostmon 逐拍 JSONL | `/home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/hostmon_YYYYMMDD.jsonl` |
| 槽位策略（每拍原子重写） | `/home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/slot_policy.json` |
| hostmon nohup 日志（每拍单行摘要） | `/home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/hostmon.nohup.log` |
| guard 事件流（acquire/release/TRIP/warning） | `/home/sdc/gem5-fi-ding/runs/lsu/guard/guard_events.log` |
| ramp 负载产物 | `runs/lsu/obs/<campaign>/...`（obs_driver）或 formal 延续产物 |

handoff 摘要字段（写入 ramp 段，交中央）：
```
ramp: {
  window: {start, end, ticks},                  # 观察窗起止与拍数
  cap_timeline: [{t, from, to, reason}],        # 每次变档（含手动 seed 的 reason 全文）
  evidence: {mem_min_gib, swap_min_gib, sustained_swap, blocked_events,
             home_delta_gib_10min},             # 取 slot_policy.json evidence 快照
  peak: {gem5_n, slots_held},                   # 观察窗内峰值（从 JSONL 统计）
  trip_events: [...],                           # guard_events.log TRIP 全量引用
  refusals: {slot_full, stop_dispatch, transient_stale},  # 槽竞争/停派发/释放竞态计数
  artifacts: {hostmon_jsonl, slot_policy, nohup_log}      # 绝对路径
}
```

## 附录 A：hostmon 重启模板（跨会话常驻，勿常停）

```bash
cd /home/sdc/gem5-fi-ding   # obs-sub-b 合并进主树前：
                           # cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-obs-b
LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
nohup python3 tools/lsu_hostmon.py --interval 60 \
  --out /home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon \
  >> /home/sdc/gem5-fi-ding/runs/lsu/obs/hostmon/hostmon.nohup.log 2>&1 &
# 记录新 PID；重启自动续历史（最新 JSONL 尾部 60 拍）与 cap（slot_policy.json）
```

## 附录 B：已知竞态提示（不影响正确性，影响重试噪音）

guard v2 释放竞态（OBS-4b 实测）：run 的目标进程退出到锁 unlink 之间（monitor
做 /proc 存活扫描，约 0.1-0.5 s）锁文件存在但持有者已死——此刻并发的 acquire
（rc=2 "陈旧"）或 gate（rc=1 "陈旧槽"）会被**瞬时**拒绝。处置：driver 重试即可
（≥1s 后锁必已消失）；**不要** clear-stale，除非 1s 后死锁仍在（那才是真异常）。
升档期间多 driver 高频重试会放大该噪音，属预期现象。
