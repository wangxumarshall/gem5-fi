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

.PHONY: all fs clean smoke payload $(WORKLOADS) $(FS_WORKLOADS)

all: $(WORKLOADS)

fs: $(FS_WORKLOADS)

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
	rm -f $(WORKLOADS) $(FS_WORKLOADS)
