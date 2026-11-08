import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from np.hw_dto import temp_level, throttled_flags, hw_dto


class TestHwDto(unittest.TestCase):
    def test_temp(self):
        self.assertEqual(temp_level(50), 'ok')
        self.assertEqual(temp_level(65), 'warn')
        self.assertEqual(temp_level(80), 'hot')

    def test_flags(self):
        self.assertEqual(throttled_flags('0x0'), [])
        self.assertEqual(
            throttled_flags('0x50005'),
            ['undervoltage', 'throttled', 'undervoltage_past', 'throttled_past'],
        )

    def test_hw_basic(self):
        si = {
            'cpus': {
                '3': {'consumption': [26.26]},
                '2': {'consumption': [19.00]},
                '1': {'consumption': [20.41]},
                '0': {'consumption': [2.47]},
            },
            'memory': {'total': 2105786368, 'available': [1823588352]},
            'temperature': {'unit': 'C', 'temperatures': [39.70]},
        }
        probe = {
            'tempC': 38.05, 'load1': 4.12, 'uptimeSec': 6885, 'freqMHz': 2400,
            'throttled': '0x0', 'voltCore': 0.8466, 'fbMode': '320x240',
            'fbInterlaced': False, 'screenType': 0, 'panelButtons': 6,
        }
        d = hw_dto(si, probe, None, None, mqtt_age_sec=0.5, probe_age_sec=2, api_online=True)
        self.assertTrue(d['mqtt']['ok'])
        self.assertEqual(d['temp']['c'], 39.7)
        self.assertEqual(d['cpu']['cores'], ['2.5', '20.4', '19', '26.3'])


if __name__ == '__main__':
    unittest.main()
