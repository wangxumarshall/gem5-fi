# Task 3.3 conflict sequence: same-tag aliasing on the L1D (64KiB, 4-way,
# 64B blocks -> 256 sets; set index = addr bits [11:6]).
# AArch64 ldr/str unsigned-imm offsets top out at 4095 and the wrapper's
# sanitizer strips depth-0 '#', so the 4096-multiple addresses are formed
# by stepping the base: "add x8, x8, 4096" (GAS decimal imm, no '#') then
# "str xN, [x8]". x8 walks mem[0], mem[4096], ..., mem[393216]: bits
# [11:0] stay 0 across every access -- the L1D set index AND the tag low
# bits repeat, while the tags differ (addr >> 12 differs). 96 aliases x
# 5 iters = 480 conflicting accesses vs a 4-way L1D: constant
# evict/refill thrash (per-set working set 96, ways 4). Store data is
# irrelevant (dead writes fine); what matters is 96 distinct tags cycling
# through the tag array. mem region 2MiB covers 5 x 393216 + 64.
add x8, x8, 4096
str x9, [x8]
add x8, x8, 4096
str x10, [x8]
add x8, x8, 4096
str x11, [x8]
add x8, x8, 4096
str x12, [x8]
add x8, x8, 4096
str x13, [x8]
add x8, x8, 4096
str x14, [x8]
add x8, x8, 4096
str x15, [x8]
add x8, x8, 4096
str x16, [x8]
add x8, x8, 4096
str x17, [x8]
add x8, x8, 4096
str x18, [x8]
add x8, x8, 4096
str x19, [x8]
add x8, x8, 4096
str x20, [x8]
add x8, x8, 4096
str x21, [x8]
add x8, x8, 4096
str x22, [x8]
add x8, x8, 4096
str x23, [x8]
add x8, x8, 4096
str x24, [x8]
add x8, x8, 4096
str x25, [x8]
add x8, x8, 4096
str x26, [x8]
add x8, x8, 4096
str x27, [x8]
add x8, x8, 4096
str x28, [x8]
add x8, x8, 4096
str x9, [x8]
add x8, x8, 4096
str x10, [x8]
add x8, x8, 4096
str x11, [x8]
add x8, x8, 4096
str x12, [x8]
add x8, x8, 4096
str x13, [x8]
add x8, x8, 4096
str x14, [x8]
add x8, x8, 4096
str x15, [x8]
add x8, x8, 4096
str x16, [x8]
add x8, x8, 4096
str x17, [x8]
add x8, x8, 4096
str x18, [x8]
add x8, x8, 4096
str x19, [x8]
add x8, x8, 4096
str x20, [x8]
add x8, x8, 4096
str x21, [x8]
add x8, x8, 4096
str x22, [x8]
add x8, x8, 4096
str x23, [x8]
add x8, x8, 4096
str x24, [x8]
add x8, x8, 4096
str x25, [x8]
add x8, x8, 4096
str x26, [x8]
add x8, x8, 4096
str x27, [x8]
add x8, x8, 4096
str x28, [x8]
add x8, x8, 4096
str x9, [x8]
add x8, x8, 4096
str x10, [x8]
add x8, x8, 4096
str x11, [x8]
add x8, x8, 4096
str x12, [x8]
add x8, x8, 4096
str x13, [x8]
add x8, x8, 4096
str x14, [x8]
add x8, x8, 4096
str x15, [x8]
add x8, x8, 4096
str x16, [x8]
add x8, x8, 4096
str x17, [x8]
add x8, x8, 4096
str x18, [x8]
add x8, x8, 4096
str x19, [x8]
add x8, x8, 4096
str x20, [x8]
add x8, x8, 4096
str x21, [x8]
add x8, x8, 4096
str x22, [x8]
add x8, x8, 4096
str x23, [x8]
add x8, x8, 4096
str x24, [x8]
add x8, x8, 4096
str x25, [x8]
add x8, x8, 4096
str x26, [x8]
add x8, x8, 4096
str x27, [x8]
add x8, x8, 4096
str x28, [x8]
add x8, x8, 4096
str x9, [x8]
add x8, x8, 4096
str x10, [x8]
add x8, x8, 4096
str x11, [x8]
add x8, x8, 4096
str x12, [x8]
add x8, x8, 4096
str x13, [x8]
add x8, x8, 4096
str x14, [x8]
add x8, x8, 4096
str x15, [x8]
add x8, x8, 4096
str x16, [x8]
add x8, x8, 4096
str x17, [x8]
add x8, x8, 4096
str x18, [x8]
add x8, x8, 4096
str x19, [x8]
add x8, x8, 4096
str x20, [x8]
add x8, x8, 4096
str x21, [x8]
add x8, x8, 4096
str x22, [x8]
add x8, x8, 4096
str x23, [x8]
add x8, x8, 4096
str x24, [x8]
add x8, x8, 4096
str x25, [x8]
add x8, x8, 4096
str x26, [x8]
add x8, x8, 4096
str x27, [x8]
add x8, x8, 4096
str x28, [x8]
add x8, x8, 4096
str x9, [x8]
add x8, x8, 4096
str x10, [x8]
add x8, x8, 4096
str x11, [x8]
add x8, x8, 4096
str x12, [x8]
add x8, x8, 4096
str x13, [x8]
add x8, x8, 4096
str x14, [x8]
add x8, x8, 4096
str x15, [x8]
add x8, x8, 4096
str x16, [x8]
add x8, x8, 4096
str x17, [x8]
add x8, x8, 4096
str x18, [x8]
add x8, x8, 4096
str x19, [x8]
add x8, x8, 4096
str x20, [x8]
add x8, x8, 4096
str x21, [x8]
add x8, x8, 4096
str x22, [x8]
add x8, x8, 4096
str x23, [x8]
add x8, x8, 4096
str x24, [x8]
