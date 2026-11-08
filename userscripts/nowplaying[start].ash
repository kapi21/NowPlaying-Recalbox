#!/bin/ash
# ES event Start — Now Playing + wake P80X
NP=/recalbox/share/now-playing
[ -f "$NP/start-now-playing.sh" ] || exit 0
sh "$NP/start-now-playing.sh" || true
if [ -f "$NP/wake-marquee.sh" ]; then
  ( sleep 8; sh "$NP/wake-marquee.sh" ) >/dev/null 2>&1 &
fi
exit 0