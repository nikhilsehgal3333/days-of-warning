import unittest

from htw.analysis import connected, group_id


class AnalysisTest(unittest.TestCase):
    # Invented case: VM <- T1 (visible 2024-01-01) <- NEX (visible 2025-06-01).
    LINKS = [
        {"subject": "T1", "object": "VM", "visible_from": "2024-01-01"},
        {"subject": "NEX", "object": "T1", "visible_from": "2025-06-01"},
    ]

    def test_connection_depends_on_the_date(self):
        # On 2025-01-01 only T1 -> VM is visible, so NEX is not reachable from VM.
        self.assertFalse(connected("NEX", self.LINKS, "2025-01-01"))
        self.assertTrue(connected("T1", self.LINKS, "2025-01-01"))
        # On 2025-06-01 both links are visible.
        self.assertTrue(connected("NEX", self.LINKS, "2025-06-01"))
        # Observer B ignores the dates.
        self.assertTrue(connected("NEX", self.LINKS, None))

    def test_vehicle_maker_is_always_connected(self):
        self.assertTrue(connected("VM", [], "2020-01-01"))

    def test_group_id(self):
        self.assertEqual(group_id("E04b"), "E04")
        self.assertEqual(group_id("A01"), "A01")

    def test_lead_time_grid(self):
        # Grid of the study: TTS 14, 28, 42 and TTR 90, 135, 180 days.
        cells = [(tts, ttr) for tts in (14, 28, 42) for ttr in (90, 135, 180)]
        def share(lead):
            return sum(lead >= ttr - tts for tts, ttr in cells) / 9
        self.assertEqual(share(330), 1.0)   # above the longest need of 166 days
        self.assertEqual(share(28), 0.0)    # below the shortest need of 48 days
        self.assertAlmostEqual(share(100), 4 / 9)  # needs 48, 62, 76, 93 are met


if __name__ == "__main__":
    unittest.main()
