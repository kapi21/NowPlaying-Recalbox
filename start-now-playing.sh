#!/bin/sh
ROOT=/recalbox/share/now-playing
cd "$ROOT" || exit 1
mkdir -p "$ROOT/logs"
PIDFILE="$ROOT/now-playing.pid"

# PID reuse trap: after reboot a stale pidfile can match an unrelated process
# (e.g. getty). Only treat as running if cmdline still looks like server.py.
is_now_playing_pid() {
  pid="$1"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null) || return 1
  echo "$cmd" | grep -q 'server\.py' || return 1
  return 0
}

if [ -f "$PIDFILE" ]; then
  OLD="$(cat "$PIDFILE" 2>/dev/null)"
  if is_now_playing_pid "$OLD"; then
    echo "already running pid=$OLD"
    exit 0
  fi
  echo "stale pidfile pid=$OLD — removing"
  rm -f "$PIDFILE"
fi

export NP_API_BASE="${NP_API_BASE:-http://127.0.0.1:81}"
export NP_SHARE_ROOT="${NP_SHARE_ROOT:-/recalbox/share}"
export NP_PORT="${NP_PORT:-8787}"
export NP_ES_STATE="${NP_ES_STATE:-/tmp/es_state.inf}"
# share is exfat (noexec): invoke interpreter explicitly
nohup nice -n 10 python3 "$ROOT/server.py" >>"$ROOT/logs/now-playing.log" 2>&1 &
echo $! >"$PIDFILE"
echo "started pid=$! port=$NP_PORT"