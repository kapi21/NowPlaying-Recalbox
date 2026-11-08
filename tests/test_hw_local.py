import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.hw_local import parse_fb_mode, parse_crt_options, read_local_probe


class TestParseFbMode(unittest.TestCase):
    def test_modes_progressive(self):
        mode, interlaced = parse_fb_mode('U:320x240p-60', None)
        self.assertEqual(mode, '320x240')
        self.assertFalse(interlaced)

    def test_modes_interlaced(self):
        mode, interlaced = parse_fb_mode('U:640x480i-60', None)
        self.assertEqual(mode, '640x480')
        self.assertTrue(interlaced)

    def test_virtual_size_fallback(self):
        mode, interlaced = parse_fb_mode(None, '1920,1080')
        self.assertEqual(mode, '1920x1080')
        self.assertFalse(interlaced)

    def test_empty(self):
        mode, interlaced = parse_fb_mode(None, None)
        self.assertIsNone(mode)
        self.assertFalse(interlaced)


class TestParseCrtOptions(unittest.TestCase):
    def test_screen_and_panel(self):
        text = (
            "# comment\n"
            "options.screen.type=0\n"
            "options.jamma.controls.panel_buttons=6\n"
        )
        st, pb = parse_crt_options(text)
        self.assertEqual(st, 0)
        self.assertEqual(pb, 6)

    def test_missing(self):
        st, pb = parse_crt_options('')
        self.assertIsNone(st)
        self.assertIsNone(pb)

    def test_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'recalbox-crt-options.cfg')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('options.screen.type=3\noptions.jamma.controls.panel_buttons=4\n')
            # read_local_probe uses fixed paths; unit-test helpers via parse only
            with open(path, 'r', encoding='utf-8') as f:
                st, pb = parse_crt_options(f.read())
            self.assertEqual(st, 3)
            self.assertEqual(pb, 4)


class TestReadLocalProbeShape(unittest.TestCase):
    def test_keys_present(self):
        # On Windows (dev) most sysfs paths missing → still returns dict with CRT keys
        p = read_local_probe()
        for k in ('fbMode', 'fbInterlaced', 'screenType', 'panelButtons', 'tempC', 'throttled'):
            self.assertIn(k, p)


if __name__ == '__main__':
    unittest.main()
