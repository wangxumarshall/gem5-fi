# LSU Platform v3.2 common base

- `config_parser.py` reads the frozen Excel and validates 60 SampleRunIDs/seeds.
- `manifest.py` writes a run manifest; seed is copied from Excel, never generated.
- `fault_manager.py` implements F0/F5/F6 state machine.
- `trace_writer.py` writes Trace v3.1 JSONL (events + PropagationEdge + summary).
- `trace_validator.py` validates JSONL records.
- `terminal.py` keeps RunStatus / FaultActivationStatus / TerminalState / TraceCompleteness separate.
- `tests/test_platform.py` unit tests.

This is the Gate-1 common base. It does not modify gem5 source.
