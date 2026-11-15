# Failed / Timeout / Incomplete

- No failed, timed-out or trace-incomplete sample.

## Observation limitations (frozen instrumentation scope)
- The frozen binary does not emit per-instruction IFU fetch response, decode, or IFU-specific commit events. Instruction-side samples therefore use MMU translation/permission -> Execute Request -> Guest Oracle, exactly as approved; these downstream nodes are marked NOT_EMITTED_BY_FROZEN_BINARY, not fabricated.
- M03 R01-R04 terminate SQUASHED with PropagationStatus PARTIAL by design: the false-hit translation is squashed before a data-side consumer. TraceCompleteness is COMPLETE for every one of them.
- M06 is a detected-and-contained translation fault (PASS_EXPECTED_DETECTION); this is a legal terminal, not a run failure.
