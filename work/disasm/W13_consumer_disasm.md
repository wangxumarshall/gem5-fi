# W13 consumer 指令反汇编 (mmu_w13.dyn)

Binary: `workloads/mmu_w5x3/mmu_w13.dyn`
Build: `gcc -O2 -static-pie -march=armv8-a+simd` (dynamically-linked guest ELF;
SHA256 `83d1d942e5d15d98a89d16c5474dc15a7d2f7f307abdfe5de69964148897563b`,
embedded base64+xz in `campaign/rcs/M05-C0*.rcS`).

The three PCs are the consumer instruction (the second instruction after the
faulted load) of the three M05 data-side contexts.  `x23` is the alias pointer
`ta` (0x4010001000), `x27` is `&sink`, `x25` is the scalar returned as
`observed`.  MARKER_T=0x7d (target sentinel), MARKER_D=0x51 (decoy sentinel).

---

## C05 (guest ctx R03, LDR -> CMP -> conditional branch)  —  consumer @ 0x401b50

```
401b4c: 394002f9   ldrb w25, [x23]          ; v = *ta   (faulted load; decoy 0x51)
401b50: 12001f39   and  w25, w25, #0xff     ; zero-extend  <-- CONSUMER (consumer_of=<load>)
401b54: 7101f73f   cmp  w25, #0x7d          ; v == sentinel ?
401b58: 540003e0   b.eq 401bd4              ; equal  -> branch=1 path
401b5c: d2804000   mov  x0, #0x200          ; else sink=0x200 (branch=2)
401b60: 92401f39   and  x25, x25, #0xff
401b64: 5280005c   mov  w28, #0x2           ; *branch = 2
401b68: f9001b60   str  x0, [x27,#48]
401b6c: 17ffff79   b    401950              ; return v (w25)
...
401bd4: d2802000   mov  x0, #0x100          ; equal path: sink=0x100
401bd8: 5280003c   mov  w28, #0x1           ; *branch = 1
401bdc: d2800fb9   mov  x25, #0x7d          ; v = 0x7d
```

Oracle 对应：读取正确 sentinel 0x7d → `cmp ==` → branch=1、observed=0x7d →
`W13_RESULT result=PASS`；M05 将 alias 翻译重定向到 decoy 页读取 0x51 →
`cmp !=` → branch=2、observed=0x51 → `result=FAIL`（SDC）。

---

## C04 (guest ctx R04, LDR -> address -> second LDR)  —  consumer @ 0x401bb4

```
401ba8: 394002e0   ldrb w0, [x23]           ; v = *ta   (faulted load; decoy 0x51)
401bac: 92400c00   and  x0, x0, #0xf        ; offset = v & 0x0F
401bb0: 38606af9   ldrb w25, [x23, x0]      ; w = *(ta + offset)  (second load)
401bb4: 92401f39   and  x25, x25, #0xff     ; zero-extend  <-- CONSUMER (consumer_of=<load>)
401bb8: f9001b79   str  x25, [x27,#48]      ; sink = w
401bbc: 17ffff65   b    401950              ; return v = w
```

Oracle 对应：正确 0x7d → offset=0x0d → 第二个 load 读 0x7d → PASS；decoy
0x51 → offset=0x01 → 第二个 load 读 decoy 页字节 0x51 → observed=0x51 → FAIL。
即错误数据经"地址派生二次 load"进入 W13_RESULT。

---

## C03 (weak/dead consumer, `--ctx C03`)  —  consumer @ 0x401c0c

```
401c08: 394002e0   ldrb w0, [x23]           ; dead = *ta   (faulted load; decoy 0x51)
401c0c: 12001c00   and  w0, w0, #0xff       ; zero-extend  <-- CONSUMER (consumer_of=<load>)
401c10: 3902dfe0   strb w0, [sp,#183]       ; store to local `dead`
401c14: 3942dfe0   ldrb w0, [sp,#183]       ; reload `dead` (compiler artifact of (void)dead)
401c18: d2800019   mov  x25, #0x0           ; v = 0  (value is discarded)
401c1c: 17ffff4d   b    401950              ; return v = 0
```

Oracle 对应：C03 的 `run_context` 显式将重定向读到的字节装入 `dead` 局部变量后
丢弃，并把返回值强制为 0（`pass = g_weak_consumer ? 1 : ...`）。因此即使
faulted load 读到了 decoy sentinel 0x51，最终 `observed=0x0`、`result=PASS`
——这是"值被读取但死（weak/dead consumer）"的掩盖，而非 SDC。消费指令 0x401c0c
确实消费了 decoy 值，但后续 `mov x25,#0` 覆盖了结果。

---

## 物理寄存器依赖 (rf_writeback -> consumer)

`rf_writeback` 事件 `field=int:<N>` 记录 faulted load 写回的物理寄存器；`consumer`
事件 `field=consumer_of=<load_dyn_inst_seq>` 记录消费该寄存器的动态指令。
同一事务内 producer load 的 dyn_inst_seq 与 consumer 的 dyn_inst_seq 相邻
(例如 C03-T01: load 24240476 → consumer 24240477)，consumer 自己的 commit
`commit_seq` 紧随其后，可据此重建完整 Data Dependency DAG。
