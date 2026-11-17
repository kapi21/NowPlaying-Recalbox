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
            list_dir=lambda _d: [],
        )
        self.assertEqual([a['type'] for a in art], ['box'])

    def test_wheel_different_hash_same_title(self):
        # Recalbox scrap: boxes/images/wheels usan hashes distintos del mismo juego
        game = {
            'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/Cabal 408a05c07ba0cd6d40e53d8bd16cc860.png',
            'ImagePath': '/recalbox/share/roms/fbneo/media/images/Cabal f712ea10fe21474be95a034a6098d8f1.png',
        }
        wheel = '/recalbox/share/roms/fbneo/media/wheels/Cabal 4893754ffdd51c1715490c2f76ce91be.png'
        ok = {
            game['BoxPath'],
            game['ImagePath'],
            wheel,
        }

        def listdir(d: str):
            if d.endswith('/wheels'):
                return ['Cabal 4893754ffdd51c1715490c2f76ce91be.png']
            return []

        art = build_game_art(game, exists=lambda p: p in ok, list_dir=listdir)
        self.assertEqual([a['type'] for a in art], ['box', 'image', 'wheel'])
        self.assertIn('4893754ffdd51c1715490c2f76ce91be', art[2]['url'])

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
