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
# ScreenScraper Recalbox: "Game Name <32hex>.ext"
_HASH_NAME = re.compile(r'^(.*)\s+[0-9a-f]{32}(\.[^.]+)$', re.I)


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


def media_title_prefix(filename: str) -> str:
    """'Cabal 408a….png' → 'Cabal'; mismo nombre sin hash."""
    m = _HASH_NAME.match(filename)
    if m:
        return m.group(1)
    return os.path.splitext(filename)[0]


def resolve_media_sibling(
    seed_path: str,
    folder: str,
    *,
    file_ok: Callable[[str], bool],
    list_dir: Callable[[str], list[str]] | None = None,
) -> str | None:
    """Exact same filename in other media/ folder, or same game title with different hash."""
    seed = seed_path.replace('\\', '/')
    exact = _sibling(seed, folder)
    if exact and file_ok(exact):
        return exact

    m = _MEDIA_FILE.match(seed)
    if not m:
        return None
    root = m.group(1)
    prefix = media_title_prefix(m.group(3))
    if not prefix:
        return None
    folder_abs = f'{root}/media/{folder}'
    try:
        names = list_dir(folder_abs) if list_dir is not None else os.listdir(folder_abs)
    except OSError:
        return None

    prefix_l = prefix.lower()
    candidates: list[str] = []
    for fn in names:
        low = fn.lower()
        if low.startswith(prefix_l + ' ') or low.startswith(prefix_l + '.') or low == prefix_l:
            candidates.append(f'{folder_abs}/{fn}'.replace('\\', '/'))
    for path in candidates:
        if file_ok(path):
            return path
    return None


def build_game_art(
    game: dict | None,
    share_root: str | None = None,
    *,
    exists: Callable[[str], bool] | None = None,
    list_dir: Callable[[str], list[str]] | None = None,
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

    def _file_ok(path: str) -> bool:
        if exists is not None:
            return bool(exists(path))
        if share_root:
            return os.path.isfile(path)
        # No disk probe: only trust paths EmulationStation already gave us
        return path in explicit.values()

    candidates: dict[str, str] = dict(explicit)
    probe_disk = exists is not None or bool(share_root)
    if seed and probe_disk:
        for typ, folder in _ART_ORDER:
            if typ in candidates:
                continue
            found = resolve_media_sibling(seed, folder, file_ok=_file_ok, list_dir=list_dir)
            if found:
                candidates[typ] = found

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
