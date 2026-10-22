# workloads/litmus/Makefile — W7 Atomic-Litmus 多核载体（R4-8-FSMC）。
#
# 构建约定（沿用 workloads/directed/ 的既有约定：source + 静态 ELF 都入库）：
#   * <name>.c -> <name>，宿主 aarch64 原生 gcc，`-O2 -static`，无交叉工具链
#   * 每个程序打印 FINAL=<16hex>（tools/classify.py _CHECKSUM_RE），并额外
#     打印一行自解释 oracle（本 litmus 的"禁出现结果"计数）
#
# 与 ooo/directed 的差异（有意为之）：
#   * 这三个是**多核**载体，宿主上可以原生跑（真 aarch64、真 fork、真共享
#     内存），所以"功能验证"在宿主上就能做，不必等 gem5；gem5 FS 只用来
#     验证*模拟平台*的跨核一致性。
#   * 轮次是编译期常量（LITMUS_ROUNDS / LITMUS_ATOM_ROUNDS），因为 golden
#     FINAL 只覆盖"违例计数 + 轮次"，轮次改了就是另一个 golden —— 现场
#     重编译比运行期参数更不容易漂移。
#
# Usage:
#   make -C workloads/litmus            # 三个 litmus 全部构建
#   make -C workloads/litmus smoke      # 宿主原生跑一遍（golden 自检）
#   make -C workloads/litmus payload    # 从构建产物再生成 configs/fs/litmus.rcS
#   make -C workloads/litmus clean

CC      := gcc
CFLAGS  := -O2 -static -Wall -Wextra
LITMUS_ROUNDS ?= 2000
LITMUS_EXTRA := -DLITMUS_ROUNDS=$(LITMUS_ROUNDS)

# FS 预算（**必须**小，否则在 gem5 O3 FS 上跑不完）：实测参照仓库既有记录 ——
# tlb_probe.rcS 头注 "10 rounds ≈ 20 fork ≈ 10 min"（O3 restore），
# m2_ptrchase.rcS 头注 "2000 x fork/exec of cat ≈ 20s each ≈ 12h"。
# 本 litmus 只 fork 一次、之后是跨核握手轮次（每轮含两次核间往返 + 上下文
# 切换），按同样的量级取 LITMUS_ROUNDS_FS=64 / ATOM_ROUNDS_FS=32。
# 宿主 smoke 用大轮次（2000）保证统计强度；两者都是编译期常量，
# golden 只由"测试标识+违例数+轮次"决定，所以轮次不同 = 另一个 golden，
# 由 rcS 打印的 FINAL 现场读取，不靠回忆。
LITMUS_ROUNDS_FS ?= 64
LITMUS_ATOM_ROUNDS_FS ?= 32
LITMUS_ATOM_INCR_FS ?= 4
FS_EXTRA := -DLITMUS_ROUNDS=$(LITMUS_ROUNDS_FS) \
            -DLITMUS_ATOM_ROUNDS=$(LITMUS_ATOM_ROUNDS_FS) \
            -DLITMUS_ATOM_INCR=$(LITMUS_ATOM_INCR_FS)

WORKLOADS := litmus_sb litmus_mp litmus_atomic
FS_WORKLOADS := $(addsuffix _fs,$(WORKLOADS))

# ---- R4-9-FSMC-A：freestanding 变体 ---------------------------------------
# 为什么单列一套编译选项：libc 静态 ELF 642 KB，base64 后每个 ~860 KB，经
# guest 的 `sh` heredoc 在 2 核 Ruby/O3 恢复态下**解不出来**（R4-8-FSMC §3.2：
# 三臂终态一致，压缩臂同样卡住）。freestanding 版零 libc/零 libgcc/无动态
# 装载器：~8 KB，base64 后 ~11 KB，一次 exec 覆盖三个测试（SB/MP/LDXR-STXR）。
#   -nostdlib                不链 crt/libc
#   -ffreestanding           声明没有宿主运行时
#   -no-pie                  ET_EXEC，内核直接映射，无需解释器
#   -fno-stack-protector     否则会拉进 __stack_chk_fail（libc 符号）
#   -fno-asynchronous-unwind-tables  去掉 .eh_frame，纯粹减体积
#   -Wl,-e,_start / --build-id=none / -z noexecstack  入口显式 + 产物可复现
#   -Wl,-N                    text+data 合并进**同一个可写 LOAD 段**，且不留
#                             FileSiz==0 的 .bss 段 —— 这是**必须**的：R4-9-FSMC-A
#                             实测带零长 .bss 段的版本在 gem5 2 核 Ruby/O3 guest 里
#                             一进 _start 就 SIGSEGV（宿主上正常），而仓库里能跑的
#                             nostdlib 先例（sysreg_churn 的内嵌 ELF）正好是单段、
#                             FileSiz==MemSiz。与之配套，源里的全局都给了非零初值
#                             （见 litmus_free.c 里 obuf 上方说明），否则 .bss 会
#                             再长出来。
#   -Wl,--no-warn-rwx-segments  -N 会让 ld 报 "LOAD segment with RWX permissions"
#                             警告；段权限是 -N 的固有结果，显式关掉这条噪声。
FREE_CFLAGS := -O2 -static -no-pie -ffreestanding -nostdlib \
               -fno-stack-protector -fno-asynchronous-unwind-tables \
               -Wall -Wextra -Wl,-e,_start -Wl,--build-id=none \
               -Wl,-z,noexecstack -Wl,-N -Wl,--no-warn-rwx-segments

.PHONY: all fs clean smoke payload $(WORKLOADS) $(FS_WORKLOADS) \
        free smoke_free payload_free lint_free \
        litmus_free_pilot pilot_free smoke_free_pilot payload_free_pilot

all: $(WORKLOADS)

fs: $(FS_WORKLOADS)

# freestanding 组合载体（SB + MP + LDXR/STXR 原子性，一次 exec 全跑）
litmus_free: litmus_free.c
	$(CC) $(FREE_CFLAGS) -o $@ $<

free: litmus_free

# 宿主原生自检（真 aarch64、真 SMP、真共享内存）：三条"禁出现计数"必须为 0，
# FINAL 必须跨运行恒定（它只折叠计数与轮次，不折叠非确定的 SB 直方图）。
smoke_free: free
	@echo "=== litmus_free (native, pin 0,1) ==="; taskset -c 0,1 ./litmus_free; \
	 echo "rc=$$?"; \
	 echo "=== litmus_free (native, pin 2,3) ==="; taskset -c 2,3 ./litmus_free; \
	 echo "rc=$$?"

lint_free: free
	@echo "=== ELF type + dynamic deps (must be ET_EXEC, no INTERP) ==="
	@file litmus_free
	@readelf -l litmus_free | grep -c INTERP | \
	    sed 's/^/INTERP segments: /;s/^0$$/INTERP segments: 0 (static OK)/'
	@echo "=== undefined symbols (must be empty) ==="
	@nm -u litmus_free | sed 's/^/  UNDEF /'

# FS payload 再生成（幂等）：control 臂 + heredoc 阶梯诊断臂。
payload_free: free
	python3 $(CURDIR)/make_free_payload.py --elf $(CURDIR)/litmus_free \
	    --out $(CURDIR)/../../configs/fs/litmus_free.rcS
	python3 $(CURDIR)/make_free_payload.py --elf $(CURDIR)/litmus_free \
	    --out $(CURDIR)/../../configs/fs/litmus_free_diag.rcS --ladder

# ---- R4-8-FSMC-B：小轮次 pilot 载体 ----------------------------------------
# WHY: the canonical `litmus_free` (SB 64 / ATOM 8x2) is the identity the
# campaign + FSMC_GOLDEN_FINAL pin; it must not drift. But on the 2-core
# Ruby/O3 restore the ATOMIC phase of the canonical build does NOT complete
# inside the observation window (R4-9-FSMC-A §2.4/§2.5, re-measured here), so
# a clean ATOMIC oracle — and therefore any injection-vs-fault-free control —
# could never be taken. This pilot build is the SAME source with a smaller
# round count so the LDXR/STXR path is observable; it gets its OWN rcS and
# its OWN golden. It is an injection-instrumentation carrier, NOT a
# replacement for the canonical carrier's identity.
PILOT_CFLAGS := -DLITMUS_FREE_SB_ROUNDS=8 -DLITMUS_FREE_ATOM_ROUNDS=2 \
                -DLITMUS_FREE_ATOM_INCR=1

litmus_free_pilot: litmus_free.c
	$(CC) $(FREE_CFLAGS) $(PILOT_CFLAGS) -o $@ $<

pilot_free: litmus_free_pilot

smoke_free_pilot: pilot_free
	@echo "=== litmus_free_pilot (native, pin 0,1) ==="; taskset -c 0,1 ./litmus_free_pilot; \
	 echo "rc=$$?"

payload_free_pilot: pilot_free
	python3 $(CURDIR)/make_free_payload.py --elf $(CURDIR)/litmus_free_pilot \
	    --out $(CURDIR)/../../configs/fs/litmus_free_pilot.rcS

litmus_sb: litmus_sb.c litmus_common.h
	$(CC) $(CFLAGS) $(LITMUS_EXTRA) -o $@ $<

litmus_mp: litmus_mp.c litmus_common.h
	$(CC) $(CFLAGS) $(LITMUS_EXTRA) -o $@ $<

litmus_atomic: litmus_atomic.c litmus_common.h
	$(CC) $(CFLAGS) $(LITMUS_EXTRA) -o $@ $<

# 宿主原生自检：真多核 aarch64 上"禁出现结果"必须为 0。打印每个 litmus 的
# oracle 行与 FINAL，作为"逻辑本身是对的"的现场证据（与 gem5 无关）。
smoke: all
	@for w in $(WORKLOADS); do echo "=== $$w ==="; ./$$w || echo "EXIT=$$?"; done

# FS 变体：小轮次镜像（guest 里仍然叫 litmus_<test>，见 payload 的
# --strip-suffix _fs）。
define FS_WORKLOAD_template
$(1)_fs: $(1).c litmus_common.h
	$$(CC) $$(CFLAGS) $$(FS_EXTRA) -o $$@ $$<
endef

$(foreach w,$(WORKLOADS),$(eval $(call FS_WORKLOAD_template,$(w))))

# FS payload 再生成（幂等）：把三个小轮次静态 ELF 以 base64 heredoc 内嵌进
# configs/fs/litmus.rcS，使其可经 --readfile 单文件投放到 guest。
# 运行顺序有意固定为 atomic -> sb -> mp：mp 在无一致性的 classic 多核上
# 必然挂死（那正是要取证的现象），放最后才不会挡住前两个的 oracle 输出。
PAYLOAD_ORDER := $(addsuffix _fs,litmus_atomic litmus_sb litmus_mp)
payload: fs
	python3 $(CURDIR)/make_payload.py --dir $(CURDIR) --strip-suffix _fs \
	    --out $(CURDIR)/../../configs/fs/litmus.rcS $(PAYLOAD_ORDER)

clean:
	rm -f $(WORKLOADS) $(FS_WORKLOADS) litmus_free litmus_free_pilot
