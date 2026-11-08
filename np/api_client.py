from __future__ import annotations

import json
from urllib.request import Request, urlopen


def get_json(url: str, timeout: float = 2.0):
    try:
        req = Request(url, headers={'User-Agent': 'NowPlayingPi/1.0', 'Accept': 'application/json'})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return None
