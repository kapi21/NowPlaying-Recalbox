# Design: UI i18n from Recalbox language + menu Recalbox logo

_Date: 2026-11-17_  
_Status: approved in chat; awaiting spec review_

## Goal

1. Align **Now Playing** (`/`) and **MiniRA** (`/minira`) UI strings with Recalbox `system.language`.
2. Ship **English install docs** alongside Spanish (`INSTALL.en.md` + cross-links).
3. When `/` is in **menu** state (“En el menú” / “In the menu”), show the **Recalbox system logo** in the art column the same way MiniRA uses `/system-logo?id=recalbox` as placeholder — not the generic SVG “Sin arte”.

## Non-goals (v1)

- Full translation of every Recalbox locale (only **es** + **en**; other `system.language` values fall back to **en**).
- Translating game metadata from scrapers / RA (titles, synopses, achievement names stay as provided by APIs).
- Per-browser override UI (no language picker in v1).
- Duplicating HTML per language.

## Source of truth for language

| Source | Path / key | Notes |
| --- | --- | --- |
| Recalbox | `/recalbox/share/system/recalbox.conf` → `system.language` | Values like `es_ES`, `en_US`, `fr_FR`, … |
| Override (optional) | env `NP_LANG` | If set (`es` / `en`), wins over conf (useful for tests) |
| Fallback | `en` | Missing file, bad value, or unsupported language |

Mapping: take the part before `_` and lower-case (`es_ES` → `es`). Supported catalogs: `es`, `en`. Anything else → `en`.

## Architecture

```text
recalbox.conf / NP_LANG
        │
        ▼
np/locale.py  →  resolve_lang() → "es" | "en"
        │
        ├── /api/now (and/or /api/hw) includes "lang"
        └── GET /i18n/{lang}.json  (static files under www/i18n/)
                │
                ▼
index.html / minira.html
  fetch lang → fetch catalog → apply data-i18n keys + JS string map
```

### Server

- New module `np/locale.py`:
  - `read_system_language(conf_path) -> str | None`
  - `normalize_lang(raw) -> "es" | "en"`
  - `resolve_lang(...) -> "es" | "en"`
- Include `"lang"` on `/api/now` payload (always present when handler runs). Reusing `/api/now` avoids an extra poll; clients already poll it.
- Serve static `www/i18n/es.json` and `www/i18n/en.json` via existing static file rules (path `/i18n/...`).
- Tests: conf parsing, normalize, fallback, `lang` present in `/api/now`.

### Catalogs (`www/i18n/{lang}.json`)

Flat JSON of UI keys, e.g.:

```json
{
  "status.menu": "En el menú",
  "status.playing": "Jugando",
  "status.offline": "Offline",
  "game.section": "Juego",
  "art.image": "Imagen",
  "art.empty": "Sin arte",
  "menu.title": "En el menú",
  "minira.menu": "En el menu",
  "minira.select_game": "Selecciona un juego",
  "minira.rotate": "Gira la tablet",
  "minira.fullscreen": "Pantalla completa"
}
```

Cover all user-visible labels currently hardcoded in Spanish in `index.html` and `minira.html` (headers, kv labels, status pills, placeholders, PWA hint, toast “Logro conseguido”, etc.). Keep keys stable; English file mirrors the same keys.

### Client apply strategy

1. On load (and when `/api/now` reports a different `lang`), fetch `/i18n/{lang}.json` (cache in memory).
2. Elements with `data-i18n="key"` get `textContent` from the catalog.
3. Dynamic JS strings (status, resetGame titles, MiniRA `setText('title', …)`) use a small `t(key)` helper.
4. `document.documentElement.lang` set to `es` or `en`.
5. Date/number formatting: `es-ES` vs `en-US` from resolved lang.

If catalog fetch fails: keep currently rendered Spanish HTML defaults (or last good catalog); do not blank the UI.

## Menu logo on `/` (index)

**Current:** `state === 'menu'` → `resetGame('En el menú', …)` → `clearArt()` → empty cover SVG.

**Target:** same state shows Recalbox logo in the art column:

- Prefer a dedicated menu placeholder: e.g. show `#cover-empty` (or a new `#cover-menu`) with CSS/background or `<img src="/system-logo?id=recalbox">`, hide the SVG “play” icon, hide image/box/wheel slots.
- Visual intent: same asset MiniRA uses (`.right .ph` → `/system-logo?id=recalbox`), opacity/size tuned for the cover column (readable, not a tiny watermark only).
- When leaving menu for gamelist/playing/system with art, restore normal art rendering.
- Offline can keep current empty/offline behavior (no requirement to show Recalbox logo when offline).

MiniRA already shows the logo via empty art + `.ph`; no change required there unless logo is missing when `boxUrl` is set incorrectly — out of scope unless a bug appears.

## Docs

- Add `INSTALL.en.md` (English translation of `INSTALL.md`), update URLs to `/minira`.
- Cross-link at top of `INSTALL.md` ↔ `INSTALL.en.md`.
- Point `README.en.md` “Full install” to `INSTALL.en.md`.
- Spanish `README.md` / `INSTALL.md` stay canonical for ES users.

## Testing

- Unit: `np/locale.py` (conf lines, comments, missing file, `NP_LANG`, unsupported → `en`).
- Server: `/api/now` JSON includes `"lang"`.
- Manual: set `NP_LANG=en`, reload `/` and `/minira`, labels switch; menu state on `/` shows Recalbox logo.

## Risks

- Share path to `recalbox.conf` may differ in tests → inject path / env.
- Large string surface in HTML → miss a few labels; acceptable to fix in follow-up if discovered.
- `system.language` change requires Recalbox restart historically; we re-read conf on each resolve or cache with short TTL (e.g. 60s) so a rare mid-session change is eventual. **Decision: cache lang 60s in process** to avoid disk hit every `/api/now`.

## Implementation order (for plan)

1. `np/locale.py` + tests + `lang` on `/api/now`
2. `www/i18n/es.json` + `en.json`
3. Wire `index.html` + `minira.html` (`t()`, `data-i18n`, menu logo)
4. `INSTALL.en.md` + cross-links + README.en pointer
5. Deploy / publish as usual
