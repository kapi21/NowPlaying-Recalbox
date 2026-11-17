from __future__ import annotations

import os
import time
from typing import Any

SUPPORTED = frozenset({'es', 'en'})
DEFAULT_CONF = '/recalbox/share/system/recalbox.conf'

_cache_lang: str | None = None
_cache_at: float = 0.0


def reset_lang_cache() -> None:
    global _cache_lang, _cache_at
    _cache_lang = None
    _cache_at = 0.0


def normalize_lang(raw: Any) -> str:
    if raw is None:
        return 'en'
    s = str(raw).strip()
    if not s:
        return 'en'
    # es_ES / en_US → primary subtag
    primary = s.split('_', 1)[0].split('-', 1)[0].lower()
    if primary in SUPPORTED:
        return primary
    return 'en'


def read_system_language(conf_path: str) -> str | None:
    if not conf_path:
        return None
    try:
        with open(conf_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, _, val = line.partition('=')
                if key.strip() == 'system.language':
                    v = val.strip()
                    return v or None
    except OSError:
        return None
    return None


def resolve_lang(
    conf_path: str | None = None,
    cache_ttl: float = 60.0,
    environ: dict[str, str] | None = None,
) -> str:
    """Return 'es' or 'en'. NP_LANG overrides recalbox.conf. Cached for cache_ttl seconds."""
    global _cache_lang, _cache_at
    env = environ if environ is not None else os.environ
    now = time.monotonic()
    if _cache_lang is not None and (now - _cache_at) < cache_ttl:
        return _cache_lang

    override = env.get('NP_LANG')
    if override is not None and str(override).strip():
        lang = normalize_lang(override)
    else:
        path = conf_path if conf_path is not None else env.get('NP_RECALBOX_CONF', DEFAULT_CONF)
        lang = normalize_lang(read_system_language(path))

    _cache_lang = lang
    _cache_at = now
    return lang
