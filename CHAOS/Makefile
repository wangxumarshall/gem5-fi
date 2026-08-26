CHAOS_DIR = CHAOSReg
CHAOS_CACHE_DIR = CHAOSCache
CHAOS_MEM_DIR = CHAOSMem
CHAOS_PHYSREG_DIR = CHAOSPhysReg

GEM5_REPO = https://github.com/gem5/gem5
GEM5_DIR = gem5
GEM5_REG_DIR = $(GEM5_DIR)/src/
GEM5_CACHE_DIR = $(GEM5_DIR)/src/mem/cache/
GEM5_MEM_DIR = $(GEM5_DIR)/src/mem/
GEM5_PHYSREG_DIR = $(GEM5_DIR)/src/cpu/o3/
CONFIG = ARM/gem5.opt
BUILD_DIR = build/$(CONFIG)

all: install_requirements move_chaos_reg move_chaos_tags move_chaos_mem move_chaos_physreg install_gem5_requirements build_gem5

chaosreg: move_chaos_reg install_gem5_requirements build_gem5

chaoscache: move_chaos_tags install_gem5_requirements build_gem5

chaosmem: move_chaos_mem install_gem5_requirements build_gem5

# CHAOSPhysReg is O3-only and lives under src/cpu/o3/. NOTE: this target only
# copies the plugin directory; it does NOT apply the required source patches
# to cpu.hh / free_list.hh / regfile.hh (the o3 accessors + read-trace hooks
# that CHAOSPhysReg.cc calls). Those headers ship pre-patched in the vendored
# gem5 tree (see BASE_VERSION); when refreshing gem5 from upstream you must
# re-apply them — diff them against the standalone copies / git history.
chaosphysreg: move_chaos_physreg install_gem5_requirements build_gem5

toolchain: install_arm_toolchain

install_requirements:
	@sudo apt-get update
	@sudo apt-get install -y build-essential git m4 scons zlib1g zlib1g-dev \
		libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev \
		wget python3-dev python3-venv python3-pip python3-six \
		libboost-all-dev pkg-config bison meson ninja-build \
		libglib2.0-dev libpixman-1-dev gawk texinfo flex \
		libgmp-dev libmpc-dev libmpfr-dev

clone_gem5:
	@if [ ! -d "$(GEM5_DIR)" ]; then \
		git clone $(GEM5_REPO) --recursive ./$(GEM5_DIR); \
	else \
		echo "gem5 already found."; \
	fi

# Clobber-safe sync helper. The top-level CHAOS/ copies and the vendored
# copies under CHAOS/gem5/src/... MUST stay identical (report issue #5: a
# stale top-level copy, when `cp -rf`'d into the vendored tree, would
# silently revert the G3-G7 fixes). This helper is a no-op when the two are
# already identical; if they differ it prints a loud warning and copies the
# VENDORED copy back to top-level (vendored is authoritative — it is what
# scons builds) so the build is never clobbered with stale code.
define sync_chaos
	@if [ ! -d "$(1)" ]; then echo "$(1) not found"; exit 1; fi; \
	if diff -rq "$(1)" "$(2)" >/dev/null 2>&1; then \
		echo "  $(1) <-> $(2): identical (no copy)"; \
	else \
		echo "  WARNING: $(1) and $(2) DIFFER — syncing VENDORED -> top-level"; \
		echo "  (vendored is authoritative; this prevents a stale top-level"; \
		echo "   copy from clobbering the fixed build source)"; \
		cp -rf $(2)/. $(1)/; \
	fi
endef

move_chaos_reg:
	@$(call sync_chaos,$(CHAOS_DIR),$(GEM5_REG_DIR)/$(CHAOS_DIR))

move_chaos_tags:
	@$(call sync_chaos,$(CHAOS_CACHE_DIR),$(GEM5_CACHE_DIR)$(CHAOS_CACHE_DIR))

move_chaos_mem:
	@$(call sync_chaos,$(CHAOS_MEM_DIR),$(GEM5_MEM_DIR)$(CHAOS_MEM_DIR))

move_chaos_physreg:
	@$(call sync_chaos,$(CHAOS_PHYSREG_DIR),$(GEM5_PHYSREG_DIR)$(CHAOS_PHYSREG_DIR))

install_gem5_requirements:
	@echo "Installing Python dependencies..."
	@pip3 install -r $(GEM5_DIR)/requirements.txt

build_gem5:
	@cd $(GEM5_DIR) && \
		scons $(BUILD_DIR) -j$(shell nproc) && \
			cd ..

install_arm_toolchain:
	@sudo apt-get update
	@sudo apt-get install -y gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

.PHONY: all install_requirements clone_gem5 move_chaos_reg move_chaos_tags move_chaos_mem move_chaos_physreg install_gem5_requirements build_gem5 toolchain install_arm_toolchain
