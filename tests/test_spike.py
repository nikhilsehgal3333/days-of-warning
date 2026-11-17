import unittest
from datetime import date, timedelta

from htw.signals import spikes


class SpikeTest(unittest.TestCase):
    def test_one_known_spike(self):
        start = date(2025, 1, 1)
        views = [100] * 40
        views[35] = 600   # 6 x baseline and >= 500: spike for k = 3 and 5, not for k = 10
        views[36] = 450   # 4.5 x baseline but < 500 views: no spike
        rows = spikes([(start + timedelta(days=i), v) for i, v in enumerate(views)])
        self.assertIsNone(rows[27]["baseline"])          # fewer than 28 earlier days
        self.assertEqual(rows[28]["baseline"], 100)
        self.assertTrue(rows[35]["spike_k3"] and rows[35]["spike_k5"])
        self.assertFalse(rows[35]["spike_k10"])
        self.assertFalse(rows[36]["spike_k3"])
        self.assertEqual([r["date"] for r in rows if r["spike_k5"]], ["2025-02-05"])


if __name__ == "__main__":
    unittest.main()
