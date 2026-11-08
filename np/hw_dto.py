from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def temp_level(c: float) -> str:
    if c >= 75:
        return 'hot'
    if c >= 60:
        return 'warn'
    return 'ok'


def throttled_flags(raw: str | None) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    s = str(raw).strip().lower().replace('0x', '')
    try:
        v = int(s, 16)
    except ValueError:
        return []
    bits = [
        (0, 'undervoltage'), (1, 'freq_capped'), (2, 'throttled'), (3, 'soft_temp_limit'),
        (16, 'undervoltage_past'), (17, 'freq_capped_past'), (18, 'throttled_past'),
        (19, 'soft_temp_limit_past'),
    ]
    return [name for bit, name in bits if (v & (1 << bit)) != 0]


def _screen_type_name(v: Any) -> str | None:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return {
        0: '15kHz', 1: '15kHz', 2: 'multi 15/25kHz', 3: '31kHz',
        4: 'multi 15/31kHz', 5: 'tri-frecuencia',
    }.get(n)


def hw_dto(
    system_info: dict | None,
    probe: dict | None,
    storage: dict | None,
    versions: dict | None,
    mqtt_age_sec: float = -1,
    probe_age_sec: float = -1,
    api_online: bool = True,
) -> dict:
    mqtt_ok = system_info is not None and mqtt_age_sec >= 0 and mqtt_age_sec <= 5
    probe_ok = probe is not None and probe_age_sec >= 0 and probe_age_sec <= 15
    si = system_info if mqtt_ok else None
    pr = probe if probe_ok else None

    temp_c = None
    temp_from_mqtt = False
    if si and isinstance(si.get('temperature'), dict):
        temps = si['temperature'].get('temperatures') or []
        if temps:
            temp_c = float(temps[0])
            temp_from_mqtt = True
    elif pr and pr.get('tempC') is not None:
        temp_c = float(pr['tempC'])

    temp = None
    if temp_c is not None:
        display = round(temp_c, 1) if temp_from_mqtt else temp_c
        temp = {'c': display, 'level': temp_level(temp_c)}

    cores: list[str] = []
    core_nums: list[float] = []
    if si and isinstance(si.get('cpus'), dict):
        items = sorted(si['cpus'].items(), key=lambda kv: int(kv[0]))
        for _, val in items:
            cons = (val or {}).get('consumption') or [0]
            n = round(float(cons[0]), 1)
            core_nums.append(n)
            # Equivalente aproximado a PS '{0:#0.#}' → 2.5, 20.4, 19, 26.3
            if abs(n - round(n)) < 1e-9:
                cores.append(str(int(round(n))))
            else:
                cores.append(f'{n:.1f}')

    avg = round(sum(core_nums) / len(core_nums), 1) if core_nums else None
    cpu = None
    if cores or pr:
        cpu = {
            'cores': cores,
            'avg': avg,
            'freqMHz': pr.get('freqMHz') if pr else None,
            'load1': pr.get('load1') if pr else None,
        }

    ram = None
    if si and isinstance(si.get('memory'), dict):
        total = float(si['memory'].get('total') or 0)
        avail_l = si['memory'].get('available') or [0]
        avail = float(avail_l[0])
        if total > 0:
            ram = {
                'totalMB': int(round(total / (1024 * 1024))),
                'usedMB': int(round((total - avail) / (1024 * 1024))),
                'pct': int(round(((total - avail) / total) * 100)),
            }

    power = None
    if pr:
        power = {
            'voltCore': pr.get('voltCore'),
            'throttled': pr.get('throttled'),
            'throttledFlags': throttled_flags(pr.get('throttled')),
        }

    video = None
    if pr:
        video = {
            'mode': pr.get('fbMode'),
            'interlaced': pr.get('fbInterlaced'),
            'hz': None,
            'khz': None,
            'screenType': _screen_type_name(pr.get('screenType')),
            'panelButtons': pr.get('panelButtons'),
        }

    store = None
    if storage and isinstance(storage.get('storages'), dict):
        for ent in storage['storages'].values():
            if (ent or {}).get('recalbox') == 'share':
                size = float(ent.get('size') or 0)
                used = float(ent.get('used') or 0)
                if size > 0:
                    store = {
                        'shareTotalGB': int(round(size / (1024 ** 3))),
                        'shareUsedGB': int(round(used / (1024 ** 3))),
                        'pct': int(round((used / size) * 100)),
                    }
                break

    ver = None
    if versions:
        kernel = str(versions.get('linux') or '').replace('Linux version ', '', 1)
        lib = versions.get('libretro') or {}
        ver = {
            'recalbox': str(versions.get('recalbox') or '').strip(),
            'kernel': kernel,
            'retroarch': (lib.get('retroarch') if isinstance(lib, dict) else None),
        }

    return {
        'online': bool(mqtt_ok or probe_ok or api_online),
        'updatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'mqtt': {
            'ok': mqtt_ok,
            'ageSec': round(mqtt_age_sec, 1) if mqtt_age_sec >= 0 else None,
        },
        'ssh': {  # probe local ocupa el slot "ssh" del contrato PC
            'ok': probe_ok,
            'ageSec': round(probe_age_sec, 1) if probe_age_sec >= 0 else None,
        },
        'temp': temp,
        'cpu': cpu,
        'ram': ram,
        'power': power,
        'uptimeSec': pr.get('uptimeSec') if pr else None,
        'video': video,
        'storage': store,
        'versions': ver,
    }
