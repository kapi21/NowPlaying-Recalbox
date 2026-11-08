from __future__ import annotations

import os
import re
from typing import Any, Callable

from np.paths import media_url

# type → scrap folder under …/media/
_ART_ORDER: list[tuple[str, str]] = [
    ('box', 'boxes'),
    ('image', 'images'),
    ('wheel', 'wheels'),
    ('titleshot', 'titleshots'),
    ('mix', 'mixes'),
    ('thumbnail', 'thumbnails'),
    ('marquee', 'marquees'),
    ('fanart', 'fanarts'),
    ('map', 'maps'),
    ('cartridge', 'cartridges'),
    ('boxback', 'boxbacks'),
]

_PATH_KEYS: dict[str, tuple[str, ...]] = {
    'box': ('BoxPath',),
    'image': ('ImagePath',),
    'wheel': ('WheelPath',),
    'titleshot': ('TitleShotPath', 'TitleshotPath'),
    'mix': ('MixPath',),
    'thumbnail': ('ThumbnailPath',),
    'marquee': ('MarqueePath',),
    'fanart': ('FanArtPath', 'FanartPath'),
    'map': ('MapPath',),
    'cartridge': ('CartridgePath',),
    'boxback': ('BoxBackPath', 'BoxbackPath'),
}

_MEDIA_FILE = re.compile(r'^(.*)/media/([^/]+)/([^/]+)$', re.I)


def _str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _sibling(path: str, folder: str) -> str | None:
    m = _MEDIA_FILE.match(path.replace('\\', '/'))
    if not m:
        return None
    return f'{m.group(1)}/media/{folder}/{m.group(3)}'


def build_game_art(
    game: dict | None,
    share_root: str | None = None,
    *,
    exists: Callable[[str], bool] | None = None,
) -> list[dict[str, str]]:
    """Ordered art list for marquee cycle (images only)."""
    if not isinstance(game, dict):
        return []

    explicit: dict[str, str] = {}
    for typ, keys in _PATH_KEYS.items():
        for k in keys:
            p = _str(game.get(k))
            if p:
                explicit[typ] = p.replace('\\', '/')
                break

    seed = (
        explicit.get('box')
        or explicit.get('image')
        or explicit.get('thumbnail')
        or next(iter(explicit.values()), None)
    )

    candidates: dict[str, str] = dict(explicit)
    probe_disk = exists is not None or bool(share_root)
    if seed and probe_disk:
        for typ, folder in _ART_ORDER:
            if typ in candidates:
                continue
            sib = _sibling(seed, folder)
            if sib:
                candidates[typ] = sib

    def _file_ok(path: str) -> bool:
        if exists is not None:
            return bool(exists(path))
        if share_root:
            return os.path.isfile(path)
        # No disk probe: only trust paths EmulationStation already gave us
        return path in explicit.values()

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for typ, _folder in _ART_ORDER:
        path = candidates.get(typ)
        if not path or not _file_ok(path):
            continue
        url = media_url(path)
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({'type': typ, 'url': url})
    return out
