#!/bin/bash
# W8.1 Wave B 哨兵看门狗（编排者）：每 5 分钟检查；DONE→exit 0；异常→exit 1（附证据）；30 分钟心跳。
cd /home/sdc/gem5-fi
hb=0
while true; do
  if grep -q "Wave B formal DONE" runs/ooo_w81_gate/driver_waveB.log; then
    echo "WATCHDOG: DONE detected @ $(date +%H:%M)"; exit 0
  fi
  if ! pgrep -f "driver_waveB4" >/dev/null; then
    echo "WATCHDOG ALERT: driver_waveB4 dead @ $(date +%H:%M)"; tail -5 runs/ooo_w81_gate/driver_waveB.log; exit 1
  fi
  if grep -qE "CAMPAIGN FAILED|INCOMPLETE" runs/ooo_w81_gate/driver_waveB.log; then
    echo "WATCHDOG ALERT: failure lines @ $(date +%H:%M)"
    grep -E "CAMPAIGN FAILED|INCOMPLETE" runs/ooo_w81_gate/driver_waveB.log | tail -3; exit 1
  fi
  a=$(free -g | awk '/^Mem:/{print $7}')
  if [ "${a:-0}" -lt 10 ]; then
    echo "WATCHDOG ALERT: available=${a}G < 10G @ $(date +%H:%M)"; exit 1
  fi
  cp=$(pgrep -cf "campaign[.]py campaigns/ooo-w81" || echo 0)
  if [ "$cp" -eq 0 ] && ! grep -q "Wave B formal DONE" runs/ooo_w81_gate/driver_waveB.log; then
    echo "WATCHDOG: all campaigns exited @ $(date +%H:%M) — completion gate should print DONE shortly (or lanes died; checking log tail)"; tail -4 runs/ooo_w81_gate/driver_waveB.log
  fi
  hb=$((hb+1))
  if [ $((hb % 6)) -eq 0 ]; then
    s=$(for p in $(pgrep -f "destid_bitflip" 2>/dev/null); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -oE "rob_rng_seed [0-9]+" | grep -oE "[0-9]+$"; done | sort -n | tail -1)
    echo "WATCHDOG heartbeat @ $(date +%H:%M): gem5=$(pgrep -cf 'gem5[.]opt') avail=${a}G campaigns=$cp e082_max_rep=$((s-21260925))"
  fi
  sleep 300
done
