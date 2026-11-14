#!/usr/bin/env python3
from __future__ import annotations

import json
import mimetypes
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from np.paths import is_safe_relative, resolve_share_file, is_safe_system_id, resolve_system_logo, resolve_custom_logo  # noqa: E402
from np.ra_fetch import fetch_ra_img  # noqa: E402
from np.state import NowPlayingState  # noqa: E402

WWW = os.path.join(ROOT, 'www')
PORT = int(os.environ.get('NP_PORT', '8787'))
API_BASE = os.environ.get('NP_API_BASE', 'http://127.0.0.1:81')
SHARE_ROOT = os.environ.get('NP_SHARE_ROOT', '/recalbox/share')
SYSTEM_LOGO_ROOT = os.environ.get(
    'NP_SYSTEM_LOGO_ROOT',
    '/recalbox/share_init/system/.emulationstation/themes/recalbox-next/data/arts/systems_logos',
)
CUSTOM_LOGO_ROOT = os.environ.get('NP_CUSTOM_LOGO_ROOT', os.path.join(ROOT, 'logos'))
ES_STATE = os.environ.get('NP_ES_STATE', '/tmp/es_state.inf')
RA_CREDS = os.environ.get('NP_RA_CREDS', os.path.join(ROOT, 'ra.local.txt'))

STATE = NowPlayingState(
    api_base=API_BASE,
    share_root=SHARE_ROOT,
    es_state_path=ES_STATE,
    ra_creds_path=RA_CREDS,
    enable_workers=True,
)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WWW, **kwargs)

    def log_message(self, fmt, *args):
        # No registrar el polling de la API (miles de peticiones) ni 304
        line = args[0] if args else ''
        if isinstance(line, str) and (' /api/' in line or ' /ra-img' in line):
            return
        if len(args) > 1 and str(args[1]) == '304':
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str, headers: dict | None = None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        else:
            self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, content_type: str | None = None, cache: str | None = None):
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError:
            self._send(404, b'Not found', 'text/plain; charset=utf-8')
            return
        ctype = content_type or mimetypes.guess_type(path)[0] or 'application/octet-stream'
        headers = {'Cache-Control': cache} if cache else None
        self._send(200, data, ctype, headers)

    def _send_logo(self, path: str):
        """Logo con ETag (mtime+size): revalida y devuelve 304 si no cambió."""
        try:
            st = os.stat(path)
        except OSError:
            self._send(404, b'Not found', 'text/plain; charset=utf-8')
            return
        etag = '"%x-%x"' % (int(st.st_mtime), st.st_size)
        if self.headers.get('If-None-Match') == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            return
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError:
            self._send(404, b'Not found', 'text/plain; charset=utf-8')
            return
        ctype = 'image/svg+xml' if path.endswith('.svg') else 'image/png'
        self._send(200, data, ctype, {'ETag': etag, 'Cache-Control': 'no-cache'})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path or '/'

        if path == '/api/now':
            dto = STATE.build_now()
            body = json.dumps(dto, ensure_ascii=False).encode('utf-8')
            self._send(200, body, 'application/json; charset=utf-8')
            return

        if path == '/api/hw':
            body = json.dumps(STATE.build_hw(), ensure_ascii=False).encode('utf-8')
            self._send(200, body, 'application/json; charset=utf-8', {'Cache-Control': 'no-store'})
            return

        if path == '/api/ra':
            now = STATE.build_now()
            body = json.dumps(
                STATE.build_ra(current_game_name=now.get('game') or ''),
                ensure_ascii=False,
            ).encode('utf-8')
            self._send(200, body, 'application/json; charset=utf-8', {'Cache-Control': 'no-store'})
            return

        if path == '/ra-img':
            qs = parse_qs(parsed.query)
            p = unquote((qs.get('p') or [''])[0])
            data = fetch_ra_img(p)
            if not data:
                self._send(404, b'Not found', 'text/plain; charset=utf-8')
                return
            self._send(200, data, 'image/png', {'Cache-Control': 'public, max-age=3600'})
            return

        if path == '/system-logo':
            qs = parse_qs(parsed.query)
            sid = unquote((qs.get('id') or [''])[0]).strip()
            if not is_safe_system_id(sid):
                self._send(400, b'Invalid id', 'text/plain; charset=utf-8')
                return
            full = resolve_custom_logo(CUSTOM_LOGO_ROOT, sid) or resolve_system_logo(SYSTEM_LOGO_ROOT, sid)
            if not full:
                self._send(404, b'Not found', 'text/plain; charset=utf-8', {'Cache-Control': 'max-age=60'})
                return
            self._send_logo(full)
            return

        if path == '/media':
            qs = parse_qs(parsed.query)
            rel = unquote((qs.get('path') or [''])[0])
            if not rel or not is_safe_relative(rel):
                self._send(400, b'Invalid path', 'text/plain; charset=utf-8')
                return
            full = resolve_share_file(SHARE_ROOT, rel)
            if not full or not os.path.isfile(full):
                self._send(404, b'Not found', 'text/plain; charset=utf-8')
                return
            ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
            self._send_file(full, ctype, cache='public, max-age=3600')
            return

        aliases = {
            '/': 'index.html',
            '/index.html': 'index.html',
            '/marquee': 'marquee.html',
            '/marquee.html': 'marquee.html',
        }
        if path in aliases:
            self._send_file(os.path.join(WWW, aliases[path]), 'text/html; charset=utf-8')
            return

        if path.startswith('/fonts/'):
            name = os.path.basename(path)
            fp = os.path.join(WWW, 'fonts', name)
            self._send_file(fp, 'font/ttf', cache='public, max-age=86400')
            return

        if path.startswith('/'):
            rel = path.lstrip('/').replace('/', os.sep)
            fp = os.path.join(WWW, rel)
            if os.path.isfile(fp):
                self._send_file(fp)
                return

        self._send(404, b'Not found', 'text/plain; charset=utf-8')


def main():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Now Playing Pi -> http://0.0.0.0:{PORT}/  API={API_BASE}', flush=True)
    print(f'  es_state={ES_STATE}  ra={"on" if os.path.isfile(RA_CREDS) else "off"}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        STATE.stop()
        print('stop', flush=True)


if __name__ == '__main__':
    main()
