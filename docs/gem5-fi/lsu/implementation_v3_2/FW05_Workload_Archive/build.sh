#!/bin/sh
# Rebuild fw05_forward from the archived source. The archived binary is the
# exact binary used by the v3.2.7 pilots (SHA256 0cf40509...); a rebuild may
# differ in build-id/metadata bytes, so verify behavior by the checksum.
set -e
cd "$(dirname "$0")"
gcc -O2 -static src/fw05_forward.c -o fw05_forward.rebuilt
./fw05_forward.rebuilt
sha256sum fw05_forward.rebuilt
