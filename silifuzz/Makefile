CXX ?= g++
CXXFLAGS ?= -O2 -g -std=c++17 -Wall -Wextra -Werror -pthread
CPPFLAGS ?= -Iinclude
BUILD := build
BIN := bin

CORE_OBJS := $(BUILD)/snapshot.o $(BUILD)/player.o
HARNESS_OBJ := $(BUILD)/harness.o

.PHONY: all clean test test-player test-snapshot fuzzers tools

all: $(BIN)/sf_player

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
	$(CXX) $(CXXFLAGS) $^ -o $@

test: test-snapshot test-player test-crosslang

$(BIN)/test_player: tests/test_player.cc $(CORE_OBJS) $(HARNESS_OBJ) | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@
test-player: $(BIN)/test_player
	./$(BIN)/test_player

$(BIN)/test_snapshot: tests/test_snapshot.cc $(BUILD)/snapshot.o | $(BIN)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@
test-snapshot: $(BIN)/test_snapshot
	./$(BIN)/test_snapshot

test-crosslang: $(BIN)/sf_player $(BIN)/test_snapshot
	python3 tests/test_crosslang.py

clean:
	rm -rf $(BUILD) $(BIN)
