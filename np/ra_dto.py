from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote


def ra_title_key(title: str | None) -> str:
    if not title:
        return ''
    t = title.lower()
    t = re.sub(r'\([^)]*\)', ' ', t)
    t = re.sub(r'\[[^\]]*\]', ' ', t)
    t = re.sub(r'~[^~]*~', ' ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return t.strip()


def ra_title_match(ra_title: str | None, game_name: str | None) -> bool:
    a, b = ra_title_key(ra_title), ra_title_key(game_name)
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
        return True
    return False


def _ra_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def ra_img_url(path: str | None, kind: str = 'Images') -> str | None:
    if not path:
        return None
    p = path
    if kind == 'Badge' and not p.startswith('/'):
        p = f'/Badge/{p}.png'
    if not re.match(r'^/(Images|Badge)/[A-Za-z0-9_.-]+\.png\Z', p):
        return None
    if '..' in p:
        return None
    return '/ra-img?p=' + p


def ra_dto(summary: dict | None, progress: dict | None = None, current_game_name: str = '') -> dict:
    empty = {
        'ok': False, 'user': None, 'rank': None, 'totalPoints': None, 'softcorePoints': None,
        'truePoints': None, 'motto': None, 'richPresence': None, 'richPresenceAgeSec': None,
        'currentGame': None, 'pending': [], 'completed': False, 'progressOk': False,
        'recent': [], 'matchesCurrent': False,
    }
    if not summary or not str(summary.get('User') or '').strip():
        return empty

    rp = summary.get('RichPresenceMsg')
    rp = str(rp).strip() if rp else None
    if rp == '':
        rp = None
    age = None
    rp_date = summary.get('RichPresenceMsgDate')
    if rp_date:
        try:
            # RA dates often UTC-ish
            dt = datetime.fromisoformat(str(rp_date).replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = max(0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()))
        except ValueError:
            age = None

    gid = str(summary.get('LastGameID') or '')
    game = None
    if gid and gid != '0':
        rec = None
        for g in summary.get('RecentlyPlayed') or []:
            if g and str(g.get('GameID')) == gid:
                rec = g
                break
        awarded = (summary.get('Awarded') or {}).get(gid) or {}
        if rec or awarded:
            total = _ra_int(awarded.get('NumPossibleAchievements'))
            if total == 0 and rec:
                total = _ra_int(rec.get('AchievementsTotal'))
            game = {
                'id': _ra_int(gid),
                'title': str((rec or {}).get('Title') or ''),
                'console': str((rec or {}).get('ConsoleName') or ''),
                'achieved': _ra_int(awarded.get('NumAchieved')),
                'total': total,
                'score': _ra_int(awarded.get('ScoreAchieved')),
                'possibleScore': _ra_int(awarded.get('PossibleScore')),
                'iconUrl': ra_img_url((rec or {}).get('ImageIcon')),
                'boxUrl': ra_img_url((rec or {}).get('ImageBoxArt')),
            }

    pending: list[dict] = []
    completed = False
    progress_ok = False
    progress_to_use = None
    if progress is not None:
        summary_gid = _ra_int(summary.get('LastGameID'))
        progress_gid = _ra_int(progress.get('ID'))
        if summary_gid > 0 and progress_gid == summary_gid:
            progress_to_use = progress

    if progress_to_use is not None:
        achs = progress_to_use.get('Achievements') or {}
        if isinstance(achs, dict):
            progress_ok = True
            num = 0
            for a in achs.values():
                if not a:
                    continue
                num += 1
                hc = a.get('DateEarnedHardcore')
                if hc is not None and str(hc).strip():
                    continue
                badge = str(a.get('BadgeName') or '')
                typ = a.get('type')
                if typ is None:
                    typ = a.get('Type')
                pending.append({
                    'title': str(a.get('Title') or ''),
                    'description': str(a.get('Description') or ''),
                    'points': _ra_int(a.get('Points')),
                    'badgeUrl': ra_img_url(badge, 'Badge') if re.match(r'^[A-Za-z0-9_.-]+$', badge) else None,
                    'type': None if typ is None or str(typ) == '' else str(typ),
                    'displayOrder': _ra_int(a.get('DisplayOrder')),
                })
            pending.sort(key=lambda x: (x['displayOrder'], -x['points'], x['title']))
            completed = num > 0 and len(pending) == 0

    recent: list[dict] = []
    ra_map = summary.get('RecentAchievements') or {}
    if isinstance(ra_map, dict):
        raw_recent: list[tuple[str, dict]] = []
        for game_achs in ra_map.values():
            if not isinstance(game_achs, dict):
                continue
            for aid, a in game_achs.items():
                if not a or not isinstance(a, dict):
                    continue
                raw_recent.append((str(a.get('DateAwarded') or ''), {
                    'id': _ra_int(a.get('ID') or aid),
                    'title': str(a.get('Title') or ''),
                    'description': str(a.get('Description') or ''),
                    'points': _ra_int(a.get('Points')),
                    'badgeUrl': ra_img_url(str(a.get('BadgeName') or ''), 'Badge')
                    if re.match(r'^[A-Za-z0-9_.-]+$', str(a.get('BadgeName') or '')) else None,
                    'hardcore': _ra_int(a.get('HardcoreAchieved')) == 1,
                    'gameTitle': str(a.get('GameTitle') or ''),
                    'dateAwarded': str(a.get('DateAwarded') or ''),
                }))
        raw_recent.sort(key=lambda x: x[0], reverse=True)
        recent = [item for _, item in raw_recent[:8]]

    motto = str(summary.get('Motto') or '').strip() or None
    rank = summary.get('Rank')
    return {
        'ok': True,
        'user': str(summary.get('User')),
        'rank': _ra_int(rank) if rank is not None and str(rank) != '' else None,
        'totalPoints': _ra_int(summary.get('TotalPoints')),
        'softcorePoints': _ra_int(summary.get('TotalSoftcorePoints')),
        'truePoints': _ra_int(summary.get('TotalTruePoints')),
        'motto': motto,
        'richPresence': rp,
        'richPresenceAgeSec': age,
        'currentGame': game,
        'pending': pending,
        'completed': completed,
        'progressOk': progress_ok,
        'recent': recent,
        'matchesCurrent': ra_title_match(game['title'] if game else None, current_game_name) if game else False,
    }
