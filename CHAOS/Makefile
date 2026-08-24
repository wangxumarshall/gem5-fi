CHAOS_DIR = CHAOSReg
CHAOS_CACHE_DIR = CHAOSCache
CHAOS_MEM_DIR = CHAOSMem

GEM5_REPO = https://github.com/gem5/gem5
GEM5_DIR = gem5
GEM5_REG_DIR = $(GEM5_DIR)/src/
GEM5_CACHE_DIR = $(GEM5_DIR)/src/mem/cache/
GEM5_MEM_DIR = $(GEM5_DIR)/src/mem/
CONFIG = ARM/gem5.opt
BUILD_DIR = build/$(CONFIG)

all: install_requirements move_chaos_reg move_chaos_tags move_chaos_mem install_gem5_requirements build_gem5

chaosreg: move_chaos_reg install_gem5_requirements build_gem5

chaoscache: move_chaos_tags install_gem5_requirements build_gem5

chaosmem: move_chaos_mem install_gem5_requirements build_gem5

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

move_chaos_reg:
	@if [ -d "$(CHAOS_DIR)" ]; then \
		cp -r $(CHAOS_DIR) $(GEM5_REG_DIR); \
	else \
		echo "CHAOSReg folder not found, does it exist?"; \
		exit 1; \
	fi

move_chaos_tags:
	@if [ -d "$(CHAOS_CACHE_DIR)" ]; then \
		cp -rf $(CHAOS_CACHE_DIR) $(GEM5_CACHE_DIR); \
	else \
		echo "CHAOSCache folder not found, does it exist?"; \
		exit 1; \
	fi

move_chaos_mem:
	@if [ -d "$(CHAOS_MEM_DIR)" ]; then \
		cp -rf $(CHAOS_MEM_DIR) $(GEM5_MEM_DIR); \
	else \
		echo "CHAOSMem folder not found, does it exist?"; \
		exit 1; \
	fi

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

.PHONY: all install_requirements clone_gem5 move_chaos_reg move_chaos_tags move_chaos_mem install_gem5_requirements build_gem5 toolchain install_arm_toolchain
