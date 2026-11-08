#!/bin/sh
# Optional: wake Android tablet + open Chrome marquee (requires local ADB binary)
# Set NP_TABLET and NP_MARQUEE_URL before use. ADB binary is NOT shipped in this repo.
NP=/recalbox/share/now-playing
TABLET="${NP_TABLET:-}"
URL="${NP_MARQUEE_URL:-http://127.0.0.1:8787/marquee?fs=1}"
LOG="${NP}/logs/wake-marquee.log"
if [ -z "$TABLET" ]; then
  echo "NP_TABLET not set (e.g. 192.168.x.x:5555); skip wake" >>"$LOG"
  exit 0
fi

mkdir -p "${NP}/logs" /tmp/adblib
echo "$(date -Iseconds 2>/dev/null || date) wake start tablet=$TABLET" >>"$LOG"

# Debian adb + libs (exfat: copy to /tmp)
cp -a "${NP}/bin/lib/." /tmp/adblib/ 2>/dev/null || true
cp -f "${NP}/bin/adb.linux" /tmp/adb.linux
chmod +x /tmp/adb.linux
export LD_LIBRARY_PATH=/tmp/adblib
export HOME="$NP"
export ADB_VENDOR_KEYS="${NP}/.android/adbkey"
ADB=/tmp/adb.linux

"$ADB" start-server >>"$LOG" 2>&1 || true
"$ADB" connect "$TABLET" >>"$LOG" 2>&1
sleep 1
STATE=$("$ADB" -s "$TABLET" get-state 2>/dev/null || true)
echo "state=$STATE" >>"$LOG"
if [ "$STATE" != "device" ]; then
  echo "tablet not ready" >>"$LOG"
  exit 2
fi

"$ADB" -s "$TABLET" shell input keyevent KEYCODE_WAKEUP >>"$LOG" 2>&1
"$ADB" -s "$TABLET" shell settings put system accelerometer_rotation 0 >>"$LOG" 2>&1
"$ADB" -s "$TABLET" shell settings put system user_rotation 1 >>"$LOG" 2>&1
"$ADB" -s "$TABLET" shell settings put global policy_control immersive.full=com.android.chrome >>"$LOG" 2>&1

i=0
while [ $i -lt 30 ]; do
  wget -q -O /dev/null "$URL" 2>/dev/null && break
  i=$((i + 1))
  sleep 1
done

"$ADB" -s "$TABLET" shell am force-stop com.android.chrome >>"$LOG" 2>&1
sleep 1
"$ADB" -s "$TABLET" shell am start -a android.intent.action.VIEW -d "$URL" \
  -n com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity \
  --esa command_line_args '--disable-fre,--no-default-browser-check,--no-first-run' >>"$LOG" 2>&1
sleep 5

cx=640; cy=440; bx=1210; by=755
n=0
while [ $n -lt 3 ]; do
  "$ADB" -s "$TABLET" shell input tap $cx $cy >>"$LOG" 2>&1
  sleep 1
  "$ADB" -s "$TABLET" shell input tap $bx $by >>"$LOG" 2>&1
  sleep 1
  n=$((n + 1))
done
sleep 1
"$ADB" -s "$TABLET" shell input tap $cx $cy >>"$LOG" 2>&1
echo "$(date -Iseconds 2>/dev/null || date) wake done" >>"$LOG"
exit 0