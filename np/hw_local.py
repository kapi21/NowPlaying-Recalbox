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


def _run(*args: str, timeout: float = 2) -> str | None:
    try:
        out = subprocess.check_output(list(args), stderr=subprocess.DEVNULL, text=True, timeout=timeout)
        return out.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _iface_operstate(iface: str) -> str | None:
    return _read_text(f'/sys/class/net/{iface}/operstate')


def _parse_ipv4_addrs(text: str | None) -> dict[str, str]:
    """Parse `ip -4 -o addr show` → {iface: ip}."""
    out: dict[str, str] = {}
    if not text:
        return out
    for line in text.splitlines():
        # 3: wlan0    inet 192.168.1.184/24 brd ...
        m = re.search(r'^\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)', line)
        if not m:
            continue
        iface, ip = m.group(1), m.group(2)
        if iface == 'lo' or ip.startswith('127.'):
            continue
        out[iface] = ip
    return out


def _parse_default_route(text: str | None) -> tuple[str | None, str | None]:
    """Parse `ip route get 1.1.1.1` → (iface, src_ip)."""
    if not text:
        return None, None
    line = text.splitlines()[0]
    iface = None
    src = None
    m = re.search(r'\bdev\s+(\S+)', line)
    if m:
        iface = m.group(1)
    m = re.search(r'\bsrc\s+(\d+\.\d+\.\d+\.\d+)', line)
    if m:
        src = m.group(1)
    return iface, src


def _parse_wifi_link(text: str | None) -> dict[str, Any]:
    """Parse `iw dev wlan0 link` → ssid / signal / bitrate."""
    info: dict[str, Any] = {'ssid': None, 'signalDbm': None, 'bitrate': None}
    if not text or 'Not connected' in text:
        return info
    m = re.search(r'^\s*SSID:\s*(.+)$', text, re.MULTILINE)
    if m:
        info['ssid'] = m.group(1).strip() or None
    m = re.search(r'signal:\s*(-?\d+)\s*dBm', text)
    if m:
        try:
            info['signalDbm'] = int(m.group(1))
        except ValueError:
            pass
    m = re.search(r'tx bitrate:\s*([^\n]+)', text)
    if m:
        info['bitrate'] = m.group(1).strip() or None
    return info


def read_network() -> dict[str, Any]:
    """Detect active iface (ethernet/wifi), IP, SSID and signal when available."""
    net: dict[str, Any] = {
        'type': None, 'iface': None, 'ssid': None, 'ip': None,
        'gateway': None, 'signalDbm': None, 'bitrate': None,
    }
    eth_up = (_iface_operstate('eth0') or '').lower() == 'up'
    wlan_up = (_iface_operstate('wlan0') or '').lower() == 'up'
    addrs = _parse_ipv4_addrs(_run('ip', '-4', '-o', 'addr', 'show'))
    route_iface, route_src = _parse_default_route(_run('ip', 'route', 'get', '1.1.1.1'))

    iface = None
    if route_iface in ('eth0', 'wlan0'):
        iface = route_iface
    elif eth_up and 'eth0' in addrs:
        iface = 'eth0'
    elif wlan_up and 'wlan0' in addrs:
        iface = 'wlan0'
    elif eth_up:
        iface = 'eth0'
    elif wlan_up:
        iface = 'wlan0'

    if not iface:
        return net

    net['iface'] = iface
    if iface.startswith('wlan'):
        net['type'] = 'wifi'
    elif iface.startswith('eth'):
        net['type'] = 'ethernet'
    else:
        net['type'] = iface

    net['ip'] = addrs.get(iface) or route_src
    if route_iface == iface:
        # gateway from default route line if present
        route = _run('ip', 'route', 'get', '1.1.1.1') or ''
        m = re.search(r'\bvia\s+(\d+\.\d+\.\d+\.\d+)', route)
        if m:
            net['gateway'] = m.group(1)

    if net['type'] == 'wifi':
        link = _parse_wifi_link(_run('iw', 'dev', iface, 'link'))
        net['ssid'] = link.get('ssid')
        net['signalDbm'] = link.get('signalDbm')
        net['bitrate'] = link.get('bitrate')
    return net


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
        'screenType': None, 'panelButtons': None, 'network': None,
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

    try:
        probe['network'] = read_network()
    except Exception:
        probe['network'] = None

    return probe
