import unittest

from htw.checks import evaluate


class TierRuleTest(unittest.TestCase):
    TEXT = "Nexperia is a subsidiary of Wingtech Technology."

    def test_tier_3_never_counts(self):
        # A Wikipedia source fails even when the quote is in its text.
        self.assertEqual(evaluate("a subsidiary of Wingtech", self.TEXT, "3"), (False, "tier"))
        self.assertEqual(evaluate("a subsidiary of Wingtech", self.TEXT, ""), (False, "tier"))

    def test_tier_1_and_2_count_when_the_quote_is_found(self):
        self.assertEqual(evaluate("a subsidiary of Wingtech", self.TEXT, "1"), (True, ""))
        self.assertEqual(evaluate("a subsidiary of Wingtech", self.TEXT, "2"), (True, ""))

    def test_quote_must_be_in_the_text_and_short(self):
        self.assertEqual(evaluate("owned by Bosch", self.TEXT, "1"), (False, "quote not found"))
        self.assertEqual(evaluate("word " * 31, self.TEXT, "1"), (False, "too long"))


if __name__ == "__main__":
    unittest.main()
