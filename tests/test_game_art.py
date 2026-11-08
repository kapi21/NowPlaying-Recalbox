import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.game_art import build_game_art


class TestGameArt(unittest.TestCase):
    def test_explicit_box_and_image(self):
        game = {
            'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/ms.png',
            'ImagePath': '/recalbox/share/roms/fbneo/media/images/ms.png',
        }
        art = build_game_art(game)
        self.assertEqual([a['type'] for a in art], ['box', 'image'])
        self.assertTrue(art[0]['url'].startswith('/media?path='))

    def test_siblings_when_exists(self):
        game = {
            'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/ms.png',
            'ImagePath': '/recalbox/share/roms/fbneo/media/images/ms.png',
        }
        ok = {
            '/recalbox/share/roms/fbneo/media/boxes/ms.png',
            '/recalbox/share/roms/fbneo/media/images/ms.png',
            '/recalbox/share/roms/fbneo/media/wheels/ms.png',
        }
        art = build_game_art(game, exists=lambda p: p in ok)
        self.assertEqual([a['type'] for a in art], ['box', 'image', 'wheel'])

    def test_skips_missing_siblings(self):
        game = {'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/ms.png'}
        art = build_game_art(
            game,
            exists=lambda p: p.endswith('/boxes/ms.png'),
        )
        self.assertEqual([a['type'] for a in art], ['box'])

    def test_dedupe_same_url(self):
        game = {
            'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/ms.png',
            'ImagePath': '/recalbox/share/roms/fbneo/media/boxes/ms.png',
        }
        art = build_game_art(game)
        self.assertEqual(len(art), 1)
        self.assertEqual(art[0]['type'], 'box')


if __name__ == '__main__':
    unittest.main()
