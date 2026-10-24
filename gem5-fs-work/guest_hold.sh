#!/bin/sh
# Hold the guest after boot: the harness interacts via the gem5 TCP
# terminal (m5term/socat port 3456) instead of one-shot readfile.
echo "=== GUEST READY (hold) ==="
exec sleep 1000000
