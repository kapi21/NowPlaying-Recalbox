import os
import re
import struct
import unittest

LOGOS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logos'))
ID_RE = re.compile(r'^[a-z0-9._-]+( [a-z0-9._-]+)*$')


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    return struct.unpack('>II', head[16:24])


@unittest.skipUnless(os.path.isdir(LOGOS), 'pi/logos no generado (python tools/build_logos.py)')
class TestLogos(unittest.TestCase):
    def test_names_are_system_ids(self):
        for name in os.listdir(LOGOS):
            base, ext = os.path.splitext(name)
            self.assertIn(ext, ('.png', '.svg'), name)
            self.assertRegex(base, ID_RE, name)

    def test_png_valid_and_small(self):
        for name in os.listdir(LOGOS):
            p = os.path.join(LOGOS, name)
            if name.endswith('.png'):
                size = png_size(p)
                self.assertIsNotNone(size, name + ' no es PNG')
                self.assertLessEqual(max(size), 640, name)
                self.assertLess(os.path.getsize(p), 800 * 1024, name)

    def test_svg_valid(self):
        for name in os.listdir(LOGOS):
            if name.endswith('.svg'):
                with open(os.path.join(LOGOS, name), encoding='utf-8') as f:
                    self.assertIn('<svg', f.read(2000), name)

    def test_required_logos_present(self):
        for sid in ('recalbox', 'recalboxlogo'):
            self.assertTrue(
                any(os.path.isfile(os.path.join(LOGOS, sid + e)) for e in ('.png', '.svg')), sid)

    def test_no_duplicate_ids_across_formats(self):
        bases = [os.path.splitext(n)[0] for n in os.listdir(LOGOS)]
        self.assertEqual(len(bases), len(set(bases)))


if __name__ == '__main__':
    unittest.main()
