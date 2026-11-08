# Repository Instructions

This file provides guidance to Codex when working in this repository.

## Restriction

The target architecture must be ARM, and running platform should be ARM or X86.

## Verification

After changing code, verify the result with real commands. Do not infer success
from code inspection alone.

1. **Clean build**: treat every warning or error introduced by the change as a
   failure.
2. **Functional verification**: run the affected behavior and report the
   actual observed output. Do not report predicted results as evidence.
3. **Regression check**: run at least one relevant unaffected test and confirm
   that it passes without a segmentation fault or other unexpected failure.

If verification fails, fix the problem and run the checks again. Never skip a
required check or fabricate a result. If a check cannot be run, state that
clearly and explain why.

## Placeholder Tests

When porting a feature that cannot yet be fully implemented, such as SMI
counting on ARM or an IST backend, the test must return `EXIT_SKIP` from
`test_init` and give this reason:

```text
to be implemented (placeholder): <what's missing>
```

A no-op test that returns `EXIT_SUCCESS` is incorrect because it falsely
reports `pass`. The `mce_check` test is an exception: it is a real EDAC-backed
test on ARM64 and should pass.

## Communication

All work and reported results must be grounded in facts, strict reasoning, or
direct evidence. Be honest about uncertainty and limitations. Explain results
in clear, concise language that people can understand.
