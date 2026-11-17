# Installation (Recalbox)

[Español](INSTALL.md) · **English**

Requirements: **Recalbox ≥ 10** (tested on 10.1.1), Python 3 on the image, LAN.

## 1. Copy to the share

From a PC (Samba `\\RECALBOX\share` or SCP), place the repo contents at:

```text
/recalbox/share/now-playing/
```

Minimum layout: `server.py`, `np/`, `www/`, `start-now-playing.sh`, `stop-now-playing.sh`, `userscripts/`.

> The share is often **exFAT (noexec)**: do not run `./script.sh`; use `sh script.sh`.

## 2. RA credentials (optional)

```sh
cp config/ra.local.txt.example /recalbox/share/now-playing/ra.local.txt
# edit user= and apikey=
```

## 3. Boot userscript

Copy `userscripts/nowplaying[start].ash` to:

```text
/recalbox/share/userscripts/nowplaying[start].ash
```

(LF, not CRLF.)

## 4. Manual start (smoke test)

Via SSH:

```sh
sh /recalbox/share/now-playing/start-now-playing.sh
```

Open on phone/tablet (same Wi‑Fi):

```text
http://<RECALBOX-IP>:8787/minira
http://<RECALBOX-IP>:8787/
```

`/marquee` redirects to `/minira`.

Stop:

```sh
sh /recalbox/share/now-playing/stop-now-playing.sh
```

## 5. Tablet / ADB wake (optional)

Not shipped in this repo. To wake an Android tablet at boot:

1. Put a Linux-compatible `adb` under `bin/` (see `wake-marquee.sh`)
2. Export `NP_TABLET=IP:5555` and `NP_MARQUEE_URL=http://RECALBOX-IP:8787/minira?fs=1`

## Language

UI language follows Recalbox `system.language` (`es` / `en`; others fall back to English). Override with `NP_LANG=en` or `NP_LANG=es` (see `config/env.example`).

## Tests (PC or Pi)

```sh
cd /recalbox/share/now-playing   # or a local clone
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
