import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.es_state import parse_es_state, es_state_to_status

SAMPLE = """Action=rungame
ActionData=/recalbox/share/roms/fbneo/mslug.zip
State=playing
System=FinalBurn Neo
SystemId=fbneo
Game=Metal Slug
GamePath=/recalbox/share/roms/fbneo/mslug.zip
ImagePath=/recalbox/share/roms/fbneo/media/images/mslug.png
BoxPath=/recalbox/share/roms/fbneo/media/boxes/mslug-box.png
Emulator=libretro
Core=fbneo
Developer=SNK
Players=1-2
Region=WR
Genre=Run and gun
Favorite=1
"""


class TestEsState(unittest.TestCase):
    def test_parse(self):
        d = parse_es_state(SAMPLE)
        self.assertEqual(d['Action'], 'rungame')
        self.assertEqual(d['State'], 'playing')
        self.assertEqual(d['SystemId'], 'fbneo')

    def test_to_status(self):
        st = es_state_to_status(parse_es_state(SAMPLE))
        self.assertEqual(st['Action'], 'rungame')
        self.assertEqual(st['Game']['Game'], 'Metal Slug')
        self.assertEqual(st['System']['System'], 'fbneo')
        self.assertEqual(st['Game']['ImagePath'], '/recalbox/share/roms/fbneo/media/images/mslug.png')
        self.assertEqual(st['Game']['BoxPath'], '/recalbox/share/roms/fbneo/media/boxes/mslug-box.png')
        self.assertEqual(st['Game']['Developer'], 'SNK')
        self.assertTrue(st['Game']['Favorite'])


if __name__ == '__main__':
    unittest.main()
