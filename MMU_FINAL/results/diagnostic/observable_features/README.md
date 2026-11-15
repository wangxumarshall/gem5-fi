# De-labelled Observable Feature View

`MMU_Diagnostic_Observable_Features.csv/json` is a diagnostic view built from
the frozen feature library. It deliberately excludes:

- `FaultModelID`
- `FaultOrigin` / `InjectionLocation` / `FaultField`
- any injector-only identifier used to infer the model

`TerminalState`, `OracleResult` and `ManifestationType` are retained only with
`_LABEL` suffix; they are labels or software-visible symptoms, never
unconditional origin features.

## Observability tiers

- `SIMULATOR_ONLY`: trace instrumentation; no proven production equivalent.
- `POTENTIALLY_SOFTWARE_OBSERVABLE`: an architectural/software signal is
  plausible, but this campaign did not prove real-hardware availability.
- `PRODUCTION_AVAILABLE`: generic software-visible symptoms (wrong value with
  an oracle, unexpected success, SIGSEGV).
- `UNKNOWN_PRODUCTION_OBSERVABILITY`: cannot be proven available; must not be
  assumed.

`Feature_Observability_Classification.csv` lists every field and its tier.

## Important limitation

No diagnostic classifier was trained and no accuracy is claimed. The
confusability analysis shows when model-free separation is possible from
simulator events and when it is impossible from production signals alone.

See `Confusability_Analysis_NoModelID.md`.
