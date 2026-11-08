import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.status_dto import now_playing_dto


class TestStatusDto(unittest.TestCase):
    def test_offline(self):
        d = now_playing_dto(None, False)
        self.assertFalse(d['online'])
        self.assertEqual(d['state'], 'offline')
        self.assertIsNone(d['game'])

    def test_playing(self):
        status = {
            'Action': 'rungame',
            'Game': {
                'Game': 'Metal Slug',
                'GamePath': '/recalbox/share/roms/fbneo/mslug.zip',
                'ImagePath': '/recalbox/share/roms/fbneo/media/images/ms.png',
                'BoxPath': '/recalbox/share/roms/fbneo/media/boxart/ms.png',
                'Developer': 'SNK', 'Players': '1-2', 'Region': 'WR', 'Genre': 'Run and gun',
                'Favorite': True,
                'SelectedEmulator': {'Emulator': 'libretro', 'Core': 'fbneo'},
            },
            'System': {
                'System': 'fbneo',
                'SystemId': 'fbneo',
                'DefaultEmulator': {'Emulator': 'libretro', 'Core': 'fbneo'},
            },
        }
        d = now_playing_dto(status, True, {'releaseYear': 1996, 'synopsis': 'x'})
        self.assertTrue(d['online'])
        self.assertEqual(d['state'], 'playing')
        self.assertEqual(d['game'], 'Metal Slug')
        self.assertTrue(d['imageUrl'].startswith('/media?path='))
        self.assertEqual(d['releaseYear'], 1996)
        self.assertEqual(d['developer'], 'SNK')

    def test_gamelist_browsing(self):
        status = {
            'Action': 'gamelistbrowsing',
            'Game': {
                'Game': 'Pang',
                'GamePath': '/recalbox/share/roms/fbneo/bbros.zip',
                'ImagePath': '/recalbox/share/roms/fbneo/media/images/p.png',
                'BoxPath': '/recalbox/share/roms/fbneo/media/boxes/p.png',
                'Genre': 'Shooter', 'Players': '1-2', 'IsFolder': False,
            },
            'System': {'System': 'fbneo', 'SystemId': 'fbneo'},
            '_systemFullName': 'FinalBurn Neo',
        }
        d = now_playing_dto(status, True)
        self.assertEqual(d['state'], 'gamelist')
        self.assertEqual(d['game'], 'Pang')
        self.assertTrue(d['boxUrl'].startswith('/media?path='))
        self.assertEqual(d['systemFullName'], 'FinalBurn Neo')

    def test_system_browsing_clears_game(self):
        status = {
            'Action': 'systembrowsing',
            'Game': {'Game': 'Stale', 'BoxPath': '/recalbox/share/roms/x/b.png'},
            'System': {'System': 'nes', 'SystemId': 'nes'},
            '_systemFullName': 'Nintendo Entertainment System',
        }
        d = now_playing_dto(status, True)
        self.assertEqual(d['state'], 'system')
        self.assertIsNone(d['game'])
        self.assertEqual(d['boxUrl'], '/system-logo?id=nes')
        self.assertIsNone(d['imageUrl'])
        self.assertEqual(d['systemFullName'], 'Nintendo Entertainment System')

    def test_system_browsing_bad_id_no_logo(self):
        status = {
            'Action': 'systembrowsing',
            'System': {'System': 'x', 'SystemId': '../evil'},
        }
        d = now_playing_dto(status, True)
        self.assertEqual(d['state'], 'system')
        self.assertIsNone(d['boxUrl'])

    def test_endgame_is_menu(self):
        status = {
            'Action': 'endgame',
            'Game': {'Game': 'Just Quit', 'BoxPath': '/recalbox/share/roms/x/b.png'},
            'System': {'System': 'fbneo'},
        }
        d = now_playing_dto(status, True)
        self.assertEqual(d['state'], 'menu')
        self.assertIsNone(d['game'])


if __name__ == '__main__':
    unittest.main()
