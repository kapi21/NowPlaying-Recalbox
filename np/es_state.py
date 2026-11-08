from __future__ import annotations

from typing import Any


def parse_es_state(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        if not key:
            continue
        # Normalizar a Title Case wiki (Action, SystemId, …)
        canon = ''.join(p[:1].upper() + p[1:] for p in key.replace('-', '_').split('_'))
        # Mantener SystemId, GamePath, ImagePath, ActionData, IsFolder, GenreId…
        special = {
            'systemid': 'SystemId', 'gamepath': 'GamePath', 'imagepath': 'ImagePath',
            'boxpath': 'BoxPath', 'actiondata': 'ActionData', 'isfolder': 'IsFolder',
            'genreid': 'GenreId', 'thumbnailpath': 'ThumbnailPath', 'videopath': 'VideoPath',
        }
        lk = key.lower()
        if lk in special:
            canon = special[lk]
        elif key[:1].isupper():
            canon = key  # ya viene bien del fichero
        out[canon] = val.strip()
    return out


def load_es_state(path: str = '/tmp/es_state.inf') -> dict[str, str] | None:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return None
    d = parse_es_state(text)
    return d if d else None


def _nonempty(d: dict[str, str], key: str) -> str | None:
    v = d.get(key, '')
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def es_state_to_status(d: dict[str, str]) -> dict[str, Any]:
    """Convierte es_state.inf a forma compatible con now_playing_dto."""
    system_id = _nonempty(d, 'SystemId') or ''
    fav_raw = (d.get('Favorite') or '0').strip()
    favorite = fav_raw in ('1', 'true', 'True', 'yes')
    gp = _nonempty(d, 'GamePath')
    is_folder = (d.get('IsFolder') or '0').strip() in ('1', 'true', 'True', 'yes')
    game: dict[str, Any] = {
        'Game': _nonempty(d, 'Game'),
        'GamePath': gp,
        'ImagePath': _nonempty(d, 'ImagePath') or _nonempty(d, 'ThumbnailPath'),
        'BoxPath': _nonempty(d, 'BoxPath'),
        'Developer': _nonempty(d, 'Developer'),
        'Publisher': _nonempty(d, 'Publisher'),
        'Players': _nonempty(d, 'Players'),
        'Region': _nonempty(d, 'Region'),
        'Genre': _nonempty(d, 'Genre'),
        'Favorite': favorite,
        'IsFolder': is_folder,
        'SelectedEmulator': {
            'Emulator': _nonempty(d, 'Emulator'),
            'Core': _nonempty(d, 'Core'),
        },
    }
    action = _nonempty(d, 'Action') or ''
    return {
        'Action': action,
        'Game': game,
        'System': {
            'System': system_id or None,
            'DefaultEmulator': {
                'Emulator': _nonempty(d, 'Emulator'),
                'Core': _nonempty(d, 'Core'),
            },
        },
        '_systemFullName': _nonempty(d, 'System'),
        '_gamePath': gp,
        '_esState': _nonempty(d, 'State'),
    }
