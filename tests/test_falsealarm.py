import unittest

from htw.falsealarm import count


class FalseAlarmTest(unittest.TestCase):
    def test_invented_class(self):
        # Five invented measures: one stop, one borderline case, three without a stop.
        rows = [{"outcome": "stop found", "borderline": False},
                {"outcome": "no stop found", "borderline": True},
                {"outcome": "no stop found", "borderline": False},
                {"outcome": "no stop found", "borderline": False},
                {"outcome": "no stop found", "borderline": False}]
        c = count(rows)
        self.assertEqual((c["n"], c["stops"], c["borderline"]), (5, 1, 1))
        self.assertEqual(c["precision"], 0.2)
        self.assertEqual(c["precision_with_borderline"], 0.4)


if __name__ == "__main__":
    unittest.main()
