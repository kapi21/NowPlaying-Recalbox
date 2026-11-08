#!/bin/sh
ROOT=/recalbox/share/now-playing
PIDFILE="$ROOT/now-playing.pid"
if [ ! -f "$PIDFILE" ]; then
  echo "not running"
  exit 0
fi
PID="$(cat "$PIDFILE")"
kill "$PID" 2>/dev/null || true
sleep 1
kill -9 "$PID" 2>/dev/null || true
rm -f "$PIDFILE"
echo "stopped $PID"