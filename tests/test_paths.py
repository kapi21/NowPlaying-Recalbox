import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.paths import (
    share_relative, is_safe_relative, media_url, resolve_share_file,
    is_safe_system_id, system_logo_url, resolve_system_logo,
)


class TestPaths(unittest.TestCase):
    def test_share_relative(self):
        self.assertEqual(share_relative('/recalbox/share/roms/fbneo/x.png'), 'roms/fbneo/x.png')
        self.assertIsNone(share_relative('/etc/passwd'))
        self.assertIsNone(share_relative(''))

    def test_safe_relative(self):
        self.assertTrue(is_safe_relative('roms/fbneo/a.png'))
        self.assertFalse(is_safe_relative('../etc/passwd'))
        self.assertFalse(is_safe_relative('/abs'))

    def test_media_url(self):
        u = media_url('/recalbox/share/roms/fbneo/media/images/a.png')
        self.assertTrue(u.startswith('/media?path='))
        self.assertIn('roms', u)

    def test_resolve(self):
        p = resolve_share_file('/recalbox/share', 'roms/fbneo/a.zip')
        self.assertIsNotNone(p)
        norm = p.replace('\\', '/')
        self.assertTrue(norm.endswith('/recalbox/share/roms/fbneo/a.zip'), norm)
        self.assertIsNone(resolve_share_file('/recalbox/share', '../x'))


class TestSystemLogoPaths(unittest.TestCase):
    def test_safe_system_id(self):
        self.assertTrue(is_safe_system_id('fbneo'))
        self.assertTrue(is_safe_system_id('mame2003-plus'))
        self.assertTrue(is_safe_system_id('auto-arcade-capcom.cps2'))
        self.assertFalse(is_safe_system_id(''))
        self.assertFalse(is_safe_system_id('../fbneo'))
        self.assertTrue(is_safe_system_id('data east'))
        self.assertFalse(is_safe_system_id('fb  neo'))
        self.assertFalse(is_safe_system_id('fb/neo'))

    def test_system_logo_url(self):
        self.assertEqual(system_logo_url('fbneo'), '/system-logo?id=fbneo')
        self.assertIsNone(system_logo_url('../x'))
        self.assertIsNone(system_logo_url(''))

    def test_resolve_system_logo(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, 'fbneo.png'), 'wb') as f:
                f.write(b'PNG')
            p = resolve_system_logo(td, 'fbneo')
            self.assertIsNotNone(p)
            self.assertTrue(p.endswith('fbneo.png'))
            self.assertIsNone(resolve_system_logo(td, 'missing'))
            self.assertIsNone(resolve_system_logo(td, '../fbneo'))


if __name__ == '__main__':
    unittest.main()
