CXX ?= g++
CXXFLAGS ?= -O2 -g -std=c++17 -Wall -Wextra -Werror -pthread -fPIE
CPPFLAGS ?= -Iinclude
BUILD := build
BIN := bin

CORE_OBJS := $(BUILD)/snapshot.o $(BUILD)/player.o
HARNESS_OBJ := $(BUILD)/harness.o

.PHONY: all clean test test-player test-snapshot test-crosslang fuzzers deps

all: $(BIN)/sf_player $(BIN)/sf_fix $(BIN)/sf_checker

$(BUILD):
	mkdir -p $(BUILD)
$(BIN):
	mkdir -p $(BIN)

$(BUILD)/snapshot.o: src/snapshot.cc include/silifuzz/snapshot.hh | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@
$(BUILD)/player.o: src/player.cc include/silifuzz/player.hh include/silifuzz/protocol.hh include/silifuzz/snapshot.hh | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@
$(BUILD)/harness.o: src/harness.cc include/silifuzz/player.hh include/silifuzz/protocol.hh include/silifuzz/snapshot.hh | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -mgeneral-regs-only -c $< -o $@
$(BUILD)/sf_player.o: src/sf_player.cc include/silifuzz/player.hh | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

$(BIN)/sf_player: $(CORE_OBJS) $(HARNESS_OBJ) $(BUILD)/sf_player.o | $(BIN)
	$(CXX) $(CXXFLAGS) $^ -o $@ -pie

$(BIN)/sf_fix: src/sf_fix.cc $(CORE_OBJS) $(HARNESS_OBJ) | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@ -pie

$(BIN)/sf_checker: src/sf_checker.cc $(CORE_OBJS) $(HARNESS_OBJ) | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@ -pie

test: test-snapshot test-player test-crosslang test-e2e

$(BIN)/test_player: tests/test_player.cc $(CORE_OBJS) $(HARNESS_OBJ) | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@ -pie
test-player: $(BIN)/test_player
	./$(BIN)/test_player

$(BIN)/test_snapshot: tests/test_snapshot.cc $(BUILD)/snapshot.o | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@ -pie
test-snapshot: $(BIN)/test_snapshot
	./$(BIN)/test_snapshot

test-crosslang: $(BIN)/sf_player $(BIN)/test_snapshot
	python3 tests/test_crosslang.py

test-e2e: $(BIN)/ifuzzgen $(BIN)/sf_fix $(BIN)/sf_player $(BIN)/sf_checker
	./tests/test_e2e.sh

# ---- fuzzing proxies (paper section 2.4) ---------------------------------
FUZZ_CXX ?= clang++
FUZZ_FLAGS ?= -O1 -g -fsanitize=fuzzer,address -fno-omit-frame-pointer
CAP_DIR := third_party/capstone
CAP_BUILD := third_party/capstone-build
UC_DIR := third_party/unicorn
UC_BUILD := third_party/unicorn-build

deps:
	./scripts/build_deps.sh

$(BIN)/capstone_fuzz: proxies/capstone_fuzz.cc $(CAP_BUILD)/libcapstone.a | $(BIN)
	$(FUZZ_CXX) $(FUZZ_FLAGS) -I$(CAP_DIR)/include $< $(CAP_BUILD)/libcapstone.a -o $@ -lpthread

$(BIN)/unicorn_fuzz: proxies/unicorn_fuzz.cc $(UC_BUILD)/libunicorn.a | $(BIN)
	$(FUZZ_CXX) $(FUZZ_FLAGS) -I$(UC_DIR)/include $< $(UC_BUILD)/libunicorn.a -o $@ -lpthread -lm

fuzzers: $(BIN)/capstone_fuzz $(BIN)/unicorn_fuzz $(BIN)/ifuzzgen

$(BIN)/ifuzzgen:
	cd tools/ifuzzgen && go build -o ../../$(BIN)/ifuzzgen .

clean:
	rm -rf $(BUILD) $(BIN)
