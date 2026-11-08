from __future__ import annotations

import os
import re
import subprocess
from typing import Any


def _read_text(path: str) -> str | None:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().strip()
    except OSError:
        return None


def _vcgencmd(*args: str) -> str | None:
    try:
        out = subprocess.check_output(['vcgencmd', *args], stderr=subprocess.DEVNULL, text=True, timeout=2)
        return out.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def read_local_probe() -> dict[str, Any]:
    """Sustituye el SSH probe del PC con lecturas locales."""
    probe: dict[str, Any] = {
        'tempC': None, 'freqMHz': None, 'load1': None, 'uptimeSec': None,
        'voltCore': None, 'throttled': None, 'fbMode': None, 'fbInterlaced': None,
        'screenType': None, 'panelButtons': None,
    }

    raw_temp = _read_text('/sys/class/thermal/thermal_zone0/temp')
    if raw_temp and raw_temp.isdigit():
        probe['tempC'] = round(int(raw_temp) / 1000.0, 2)
    else:
        vt = _vcgencmd('measure_temp')
        if vt:
            m = re.search(r"temp=([0-9.]+)", vt)
            if m:
                probe['tempC'] = float(m.group(1))

    thr = _vcgencmd('get_throttled')
    if thr and '=' in thr:
        probe['throttled'] = thr.split('=', 1)[1].strip()

    clk = _vcgencmd('measure_clock', 'arm')
    if clk and '=' in clk:
        try:
            hz = int(clk.split('=', 1)[1])
            probe['freqMHz'] = int(round(hz / 1_000_000))
        except ValueError:
            pass

    volts = _vcgencmd('measure_volts', 'core')
    if volts and '=' in volts:
        m = re.search(r"([0-9.]+)V", volts)
        if m:
            probe['voltCore'] = float(m.group(1))

    load = _read_text('/proc/loadavg')
    if load:
        parts = load.split()
        if parts:
            try:
                probe['load1'] = float(parts[0])
            except ValueError:
                pass

    up = _read_text('/proc/uptime')
    if up:
        try:
            probe['uptimeSec'] = int(float(up.split()[0]))
        except ValueError:
            pass

    # fb mode (best-effort)
    for cand in (
        '/sys/class/graphics/fb0/virtual_size',
        '/sys/class/graphics/fb0/modes',
    ):
        t = _read_text(cand)
        if t:
            if 'x' in t.lower():
                probe['fbMode'] = t.split(',')[0].strip().split('\n')[0].strip()
            break

    return probe
