"""Case 1 (Nexperia) must keep the v0.1 results: the map value and every lead time.

The fixtures are the v0.1 files (commit 7b648fe), before the source rule. The comparison reads the
values, so line endings do not matter.
"""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "nexperia_v0.1"


def rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def current(name: str) -> Path:
    # After the refactor to several cases the results sit in results/nexperia/.
    nested = ROOT / "results" / "nexperia" / name
    return nested if nested.exists() else ROOT / "results" / name


class NexperiaRegressionTest(unittest.TestCase):
    def test_map_value_unchanged(self):
        self.assertEqual(rows(current("map_value.csv")), rows(FIXTURES / "map_value.csv"))

    def test_lead_times_unchanged(self):
        self.assertEqual(rows(current("lead_times.csv")), rows(FIXTURES / "lead_times.csv"))


if __name__ == "__main__":
    unittest.main()
