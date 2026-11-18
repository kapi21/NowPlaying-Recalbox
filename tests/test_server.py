import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

os.environ['NP_WORKERS'] = '0'
os.environ.setdefault('NP_ES_STATE', os.path.join(tempfile.gettempdir(), 'np_test_es_state.inf'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import server  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00'
       b'\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82')


def get(url, headers=None, follow_redirects=True):
    req = urllib.request.Request(url, headers=headers or {})
    if follow_redirects:
        opener = urllib.request.build_opener()
    else:
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


class TestServerLogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        with open(os.path.join(cls.tmp.name, 'abc.png'), 'wb') as f:
            f.write(PNG)
        with open(os.path.join(cls.tmp.name, 'vec.svg'), 'w', encoding='utf-8') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg"/>')
        cls._old = (server.CUSTOM_LOGO_ROOT, server.SYSTEM_LOGO_ROOT)
        server.CUSTOM_LOGO_ROOT = cls.tmp.name
        server.SYSTEM_LOGO_ROOT = os.path.join(cls.tmp.name, 'no-theme')
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.base = 'http://127.0.0.1:%d' % cls.httpd.server_address[1]
        cls.th = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.th.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        server.CUSTOM_LOGO_ROOT, server.SYSTEM_LOGO_ROOT = cls._old
        cls.tmp.cleanup()

    def test_png_ok_with_etag(self):
        code, h, body = get(self.base + '/system-logo?id=abc')
        self.assertEqual(code, 200)
        self.assertEqual(h['Content-Type'], 'image/png')
        self.assertEqual(h['Cache-Control'], 'no-cache')
        self.assertTrue(h['ETag'])
        self.assertEqual(body, PNG)

    def test_etag_304(self):
        _, h, _ = get(self.base + '/system-logo?id=abc')
        code, _, body = get(self.base + '/system-logo?id=abc', {'If-None-Match': h['ETag']})
        self.assertEqual(code, 304)
        self.assertEqual(body, b'')

    def test_svg_content_type(self):
        code, h, _ = get(self.base + '/system-logo?id=vec')
        self.assertEqual(code, 200)
        self.assertEqual(h['Content-Type'], 'image/svg+xml')

    def test_case_insensitive_id(self):
        code, _, _ = get(self.base + '/system-logo?id=ABC')
        self.assertEqual(code, 200)

    def test_missing_is_404_short_cache(self):
        code, h, _ = get(self.base + '/system-logo?id=nope')
        self.assertEqual(code, 404)
        self.assertEqual(h['Cache-Control'], 'max-age=60')

    def test_invalid_id_400(self):
        for bad in ('..%2Fx', '', 'a%2Fb', 'a%20%20b'):
            code, _, _ = get(self.base + '/system-logo?id=' + bad)
            self.assertEqual(code, 400, bad)

    def test_api_now_json(self):
        code, h, body = get(self.base + '/api/now')
        self.assertEqual(code, 200)
        data = json.loads(body.decode('utf-8'))
        self.assertIn('state', data)
        self.assertIn(data.get('lang'), ('es', 'en', 'fr'))
        self.assertEqual(data.get('hostname'), server.HOSTNAME)
        self.assertTrue(data.get('hostname'))

    def test_qr_lib_served(self):
        code, _, body = get(self.base + '/vendor/qrcode.js')
        self.assertEqual(code, 200)
        self.assertIn(b'createSvgTag', body)

    def test_minira_served(self):
        code, _, body = get(self.base + '/minira')
        self.assertEqual(code, 200)
        self.assertIn(b'art-img', body)
        self.assertIn(b'MiniRA', body)

    def test_marquee_redirects_to_minira(self):
        code, h, _ = get(self.base + '/marquee?fs=1', follow_redirects=False)
        self.assertEqual(code, 302)
        self.assertEqual(h.get('Location'), '/minira?fs=1')

    def test_unknown_404(self):
        code, _, _ = get(self.base + '/nada-aqui')
        self.assertEqual(code, 404)


if __name__ == '__main__':
    unittest.main()
