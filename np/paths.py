from __future__ import annotations

import os
import re
from urllib.parse import quote

PREFIX = '/recalbox/share/'


def share_relative(recalbox_path: str) -> str | None:
    if not recalbox_path or not str(recalbox_path).strip():
        return None
    n = str(recalbox_path).replace('\\', '/')
    if not n.lower().startswith(PREFIX):
        return None
    return n[len(PREFIX):].lstrip('/')


def is_safe_relative(rel: str) -> bool:
    if not rel or not str(rel).strip():
        return False
    n = str(rel).replace('\\', '/').strip()
    if n.startswith('/') or (len(n) >= 2 and n[1] == ':'):
        return False
    for part in n.split('/'):
        if part in ('.', '..'):
            return False
    return True


def media_url(recalbox_path: str) -> str | None:
    rel = share_relative(recalbox_path)
    if not rel or not is_safe_relative(rel):
        return None
    enc = '/'.join(quote(p, safe='') for p in rel.split('/'))
    return '/media?path=' + enc


def resolve_share_file(share_root: str, rel: str) -> str | None:
    if not is_safe_relative(rel):
        return None
    root = os.path.abspath(share_root)
    full = os.path.abspath(os.path.join(root, rel.replace('/', os.sep)))
    if full != root and not full.startswith(root + os.sep):
        return None
    return full


# Permite espacios internos simples (p. ej. coleccion 'arcade-manufacturer-data east')
_SYSTEM_ID_RE = re.compile(r'^[a-zA-Z0-9._-]+( [a-zA-Z0-9._-]+)*$')


def is_safe_system_id(system_id: str) -> bool:
    if not system_id or not str(system_id).strip():
        return False
    return bool(_SYSTEM_ID_RE.match(str(system_id).strip()))


def system_logo_url(system_id: str) -> str | None:
    if not is_safe_system_id(system_id):
        return None
    return '/system-logo?id=' + quote(str(system_id).strip(), safe='')


def resolve_custom_logo(custom_root: str, system_id: str) -> str | None:
    """Logo propio: <custom_root>/<system_id>.png (ids Recalbox, minúsculas)."""
    if not custom_root or not is_safe_system_id(system_id):
        return None
    base = os.path.join(os.path.abspath(custom_root), str(system_id).strip().lower())
    for ext in ('.png', '.svg'):
        if os.path.isfile(base + ext):
            return base + ext
    return None


def resolve_system_logo(logo_root: str, system_id: str) -> str | None:
    if not is_safe_system_id(system_id):
        return None
    if not logo_root:
        return None
    root = os.path.abspath(logo_root)
    full = os.path.abspath(os.path.join(root, str(system_id).strip() + '.png'))
    if full != root and not full.startswith(root + os.sep):
        return None
    if not os.path.isfile(full):
        return None
    return full
