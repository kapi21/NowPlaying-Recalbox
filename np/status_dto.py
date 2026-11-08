from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from np.game_art import build_game_art
from np.paths import media_url, system_logo_url


def _g(obj: Any, *keys: str) -> Any:
    cur = obj
    for k in keys:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            cur = getattr(cur, k, None)
    return cur


def _str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def now_playing_dto(
    status: dict | None,
    online: bool,
    detail: dict | None = None,
    share_root: str | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    detail_nulls = {
        'rating': None, 'playCount': None, 'lastPlayed': None, 'releaseYear': None,
        'crc32': None, 'synopsis': None, 'systemFullName': None, 'systemType': None,
        'systemManufacturer': None,
    }
    if not online or status is None:
        return {
            'online': False, 'action': None, 'state': 'offline',
            'game': None, 'system': None, 'systemId': None,
            'emulator': None, 'core': None, 'favorite': False,
            'gamePath': None, 'imageUrl': None, 'updatedAt': now,
            'boxUrl': None, 'developer': None, 'publisher': None,
            'players': None, 'region': None, 'genre': None,
            'art': [],
            **detail_nulls,
        }

    action = (_str(_g(status, 'Action')) or '').lower()
    # Solo jugando con Action explícita (evita flash del último juego en menú
    # cuando State aún dice playing tras endgame).
    is_playing = action in ('rungame', 'rundemo')
    is_gamelist = action == 'gamelistbrowsing'
    is_system_browse = action == 'systembrowsing'
    if is_playing:
        state = 'playing'
    elif is_gamelist:
        state = 'gamelist'
    elif is_system_browse:
        state = 'system'
    else:
        state = 'menu'

    game = _g(status, 'Game')
    sys = _g(status, 'System')
    emu = _str(_g(game, 'SelectedEmulator', 'Emulator')) or _str(_g(sys, 'DefaultEmulator', 'Emulator'))
    core = _str(_g(game, 'SelectedEmulator', 'Core')) or _str(_g(sys, 'DefaultEmulator', 'Core'))
    is_folder = bool(_g(game, 'IsFolder')) if game is not None else False

    # Arte/meta: jugando o juego resaltado en lista (no carpetas / no endgame)
    show_game = (is_playing or is_gamelist) and game and not is_folder

    image_url = None
    box_url = None
    art: list = []
    if show_game and isinstance(game, dict):
        art = build_game_art(game, share_root=share_root)
        img = _str(_g(game, 'ImagePath')) or _str(_g(game, 'BoxPath'))
        image_url = media_url(img) if img else None
        box = _str(_g(game, 'BoxPath'))
        box_url = media_url(box) if box else None
        if art:
            # Prefer box as primary; else first available art
            box_from_art = next((a['url'] for a in art if a.get('type') == 'box'), None)
            box_url = box_from_art or art[0]['url']
            img_from_art = next((a['url'] for a in art if a.get('type') == 'image'), None)
            if img_from_art:
                image_url = img_from_art

    developer = publisher = players = region = genre = None
    if show_game:
        developer = _str(_g(game, 'Developer'))
        publisher = _str(_g(game, 'Publisher'))
        players = _str(_g(game, 'Players'))
        region = _str(_g(game, 'Region'))
        genre = _str(_g(game, 'Genre'))

    detail_fields = dict(detail_nulls)
    if is_playing and detail:
        for k in detail_nulls:
            if k in detail and detail[k] is not None:
                detail_fields[k] = detail[k]

    system_name = _str(_g(sys, 'System'))
    system_id = _str(_g(sys, 'SystemId')) or system_name
    game_path = _str(_g(game, 'GamePath')) or _str(_g(status, '_gamePath'))
    fav = bool(_g(game, 'Favorite')) if game is not None else False
    game_name = _str(_g(game, 'Game')) if game else None

    # En carrusel de sistemas no arrastrar juego anterior del es_state
    if is_system_browse or state == 'menu':
        if not is_gamelist and not is_playing:
            game_name = None
            game_path = None
            image_url = None
            box_url = None
            art = []
            developer = publisher = players = region = genre = None
            fav = False

    out = {
        'online': True,
        'action': action or None,
        'state': state,
        'game': game_name,
        'system': system_name,
        'systemId': system_id,
        'emulator': emu,
        'core': core,
        'favorite': fav,
        'isFolder': is_folder,
        'gamePath': game_path,
        'imageUrl': image_url,
        'updatedAt': now,
        'boxUrl': box_url,
        'developer': developer,
        'publisher': publisher,
        'players': players,
        'region': region,
        'genre': genre,
        'art': art,
        **detail_fields,
    }
    if not out.get('systemFullName') and _g(status, '_systemFullName'):
        out['systemFullName'] = _str(_g(status, '_systemFullName'))
    if state == 'system':
        out['boxUrl'] = system_logo_url(system_id)
        out['imageUrl'] = None
        out['art'] = []
    return out
