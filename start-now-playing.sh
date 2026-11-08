#!/bin/sh
ROOT=/recalbox/share/now-playing
cd "$ROOT" || exit 1
mkdir -p "$ROOT/logs"
PIDFILE="$ROOT/now-playing.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "already running pid=$(cat "$PIDFILE")"
  exit 0
fi
export NP_API_BASE="${NP_API_BASE:-http://127.0.0.1:81}"
export NP_SHARE_ROOT="${NP_SHARE_ROOT:-/recalbox/share}"
export NP_PORT="${NP_PORT:-8787}"
export NP_ES_STATE="${NP_ES_STATE:-/tmp/es_state.inf}"
# share is exfat (noexec): invoke interpreter explicitly
nohup nice -n 10 python3 "$ROOT/server.py" >>"$ROOT/logs/now-playing.log" 2>&1 &
echo $! >"$PIDFILE"
echo "started pid=$! port=$NP_PORT"