import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.release_year import parse_release_year


class TestParseReleaseYear(unittest.TestCase):
    def test_unix_timestamp_int(self):
        # Golden Axe / Streets of Rage era (API Recalbox)
        self.assertEqual(parse_release_year(633830400), 1990)
        self.assertEqual(parse_release_year(686275200), 1991)
        # TMNT Shredder's Re-Revenge (was wrongly shown as 1676)
        self.assertEqual(parse_release_year(1676937600), 2023)
        self.assertEqual(parse_release_year('1676937600'), 2023)

    def test_gamelist_string(self):
        self.assertEqual(parse_release_year('19900201T000000'), 1990)
        self.assertEqual(parse_release_year('20230221T000000'), 2023)
        self.assertEqual(parse_release_year('1991-09-18'), 1991)

    def test_plain_year(self):
        self.assertEqual(parse_release_year(1996), 1996)
        self.assertEqual(parse_release_year('1989'), 1989)

    def test_rejects_garbage(self):
        self.assertIsNone(parse_release_year(None))
        self.assertIsNone(parse_release_year(''))
        self.assertIsNone(parse_release_year(0))
        self.assertIsNone(parse_release_year(123))  # not a year, not a timestamp
        self.assertIsNone(parse_release_year(1676))  # absurd bare year from old bug
        self.assertIsNone(parse_release_year(6338))


if __name__ == '__main__':
    unittest.main()
