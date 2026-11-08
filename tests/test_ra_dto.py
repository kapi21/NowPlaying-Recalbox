import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.ra_dto import ra_dto, ra_title_match


class TestRaDto(unittest.TestCase):
    def test_match(self):
        self.assertTrue(ra_title_match('Metal Slug (World)', 'Metal Slug'))
        self.assertFalse(ra_title_match('Toki', 'Metal Slug'))

    def test_guard_gameid(self):
        summary = {
            'User': 'tester', 'LastGameID': '100', 'TotalPoints': 10,
            'RecentlyPlayed': [{'GameID': '100', 'Title': 'A', 'ConsoleName': 'Arcade',
                                'AchievementsTotal': 2, 'ImageIcon': '/Images/a.png', 'ImageBoxArt': '/Images/b.png'}],
            'Awarded': {'100': {'NumPossibleAchievements': 2, 'NumAchieved': 0,
                                'ScoreAchieved': 0, 'PossibleScore': 20}},
        }
        wrong = {
            'ID': 999,
            'Achievements': {
                '1': {'Title': 'X', 'Description': 'd', 'Points': 5, 'BadgeName': 'b1',
                      'DateEarnedHardcore': '', 'DisplayOrder': 1},
            },
        }
        d = ra_dto(summary, wrong)
        self.assertTrue(d['ok'])
        self.assertFalse(d['progressOk'])
        self.assertEqual(d['pending'], [])

    def test_pending_hardcore(self):
        summary = {
            'User': 'tester', 'LastGameID': '5', 'TotalPoints': 1,
            'RecentlyPlayed': [{'GameID': '5', 'Title': 'G', 'ConsoleName': 'Arcade',
                                'AchievementsTotal': 2}],
            'Awarded': {'5': {'NumPossibleAchievements': 2, 'NumAchieved': 1,
                             'ScoreAchieved': 5, 'PossibleScore': 10}},
        }
        progress = {
            'ID': 5,
            'Achievements': {
                '1': {'Title': 'Done', 'Description': '', 'Points': 5, 'BadgeName': 'a',
                      'DateEarnedHardcore': '2024-01-01', 'DisplayOrder': 1},
                '2': {'Title': 'Todo', 'Description': 'do', 'Points': 5, 'BadgeName': 'b',
                      'DateEarnedHardcore': '', 'DisplayOrder': 2, 'type': 'progression'},
            },
        }
        d = ra_dto(summary, progress)
        self.assertTrue(d['progressOk'])
        self.assertEqual(len(d['pending']), 1)
        self.assertEqual(d['pending'][0]['title'], 'Todo')
        self.assertFalse(d['completed'])

    def test_recent(self):
        summary = {
            'User': 'tester', 'LastGameID': '10', 'TotalPoints': 1,
            'RecentlyPlayed': [{'GameID': '10', 'Title': 'Sonic', 'ConsoleName': 'MD'}],
            'Awarded': {'10': {'NumPossibleAchievements': 2, 'NumAchieved': 1,
                              'ScoreAchieved': 5, 'PossibleScore': 10}},
            'RecentAchievements': {
                '10': {
                    '1': {'ID': 1, 'Title': 'A', 'Description': 'd', 'Points': 5,
                          'BadgeName': '694305', 'DateAwarded': '2026-11-04 17:00:00',
                          'HardcoreAchieved': 1, 'GameTitle': 'Sonic'},
                    '2': {'ID': 2, 'Title': 'B', 'Points': 10, 'BadgeName': '694306',
                          'DateAwarded': '2026-11-04 18:00:00', 'HardcoreAchieved': 1,
                          'GameTitle': 'Sonic'},
                }
            },
        }
        d = ra_dto(summary, None, 'Sonic')
        self.assertEqual(len(d['recent']), 2)
        self.assertEqual(d['recent'][0]['title'], 'B')
        self.assertTrue(d['recent'][0]['badgeUrl'].endswith('/Badge/694306.png')
                        or '694306' in d['recent'][0]['badgeUrl'])


if __name__ == '__main__':
    unittest.main()
