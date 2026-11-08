from __future__ import annotations

import os
import re
import subprocess
from typing import Any


CRT_OPTIONS_CANDIDATES = (
    '/boot/crt/recalbox-crt-options.cfg',
    '/recalbox/share/system/configs/crt/recalbox-crt-options.cfg',
)


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


def parse_fb_mode(modes: str | None, virtual_size: str | None) -> tuple[str | None, bool]:
    """Parse framebuffer mode from sysfs (same contract as PC SSH probe)."""
    if modes:
        m = re.search(r'(\d+)x(\d+)([pi])?', modes, re.IGNORECASE)
        if m:
            return f'{m.group(1)}x{m.group(2)}', (m.group(3) or '').lower() == 'i'
    if virtual_size:
        m = re.match(r'^(\d+)\s*,\s*(\d+)$', virtual_size.strip())
        if m:
            return f'{m.group(1)}x{m.group(2)}', False
    return None, False


def parse_crt_options(text: str | None) -> tuple[int | None, int | None]:
    """Parse screen type + panel buttons from recalbox-crt-options.cfg."""
    if not text:
        return None, None
    screen_type = None
    panel_buttons = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if '=' not in s:
            continue
        key, _, val = s.partition('=')
        key = key.strip()
        val = val.strip()
        if key == 'options.screen.type':
            try:
                screen_type = int(val)
            except ValueError:
                pass
        elif key == 'options.jamma.controls.panel_buttons':
            try:
                panel_buttons = int(val)
            except ValueError:
                pass
    return screen_type, panel_buttons


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

    modes = _read_text('/sys/class/graphics/fb0/modes')
    if modes:
        modes = modes.split('\n', 1)[0].strip()
    vsize = _read_text('/sys/class/graphics/fb0/virtual_size')
    mode, interlaced = parse_fb_mode(modes, vsize)
    probe['fbMode'] = mode
    probe['fbInterlaced'] = interlaced

    for cand in CRT_OPTIONS_CANDIDATES:
        cfg = _read_text(cand)
        if cfg is None:
            continue
        st, pb = parse_crt_options(cfg)
        probe['screenType'] = st
        probe['panelButtons'] = pb
        break

    return probe
