from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


def read_ra_credentials(path: str) -> dict[str, str] | None:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except OSError:
        return None
    m: dict[str, str] = {}
    for line in lines:
        mm = re.match(r'^\s*([A-Za-z]+)\s*=\s*(.*?)\s*$', line)
        if mm:
            m[mm.group(1).lower()] = mm.group(2)
    if not m.get('user') or not m.get('apikey'):
        return None
    return {'user': m['user'], 'apikey': m['apikey']}


def _get_json(url: str, timeout: float = 10.0) -> Any:
    req = Request(url, headers={'User-Agent': 'NowPlayingPi/1.0'})
    with urlopen(req, timeout=timeout) as resp:
        import json
        return json.loads(resp.read().decode('utf-8'))


def fetch_summary(creds: dict[str, str], timeout: float = 10.0) -> dict | None:
    u = quote(creds['user'], safe='')
    k = quote(creds['apikey'], safe='')
    url = f'https://retroachievements.org/API/API_GetUserSummary.php?z={u}&y={k}&u={u}&g=2&a=5'
    try:
        data = _get_json(url, timeout)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def fetch_progress(creds: dict[str, str], game_id: int, timeout: float = 10.0) -> dict | None:
    u = quote(creds['user'], safe='')
    k = quote(creds['apikey'], safe='')
    g = quote(str(game_id), safe='')
    url = f'https://retroachievements.org/API/API_GetGameInfoAndUserProgress.php?z={u}&y={k}&u={u}&g={g}'
    try:
        data = _get_json(url, timeout)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def fetch_ra_img(path: str, timeout: float = 10.0) -> bytes | None:
    if not re.match(r'^/(Images|Badge)/[A-Za-z0-9_.-]+\.png\Z', path) or '..' in path:
        return None
    try:
        req = Request(
            'https://media.retroachievements.org' + path,
            headers={'User-Agent': 'NowPlayingPi/1.0'},
        )
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None
