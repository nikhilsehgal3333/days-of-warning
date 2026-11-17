import unittest

from htw.textnorm import quote_in_text, squeeze


class TextNormTest(unittest.TestCase):
    def test_white_space_and_case(self):
        self.assertEqual(squeeze("  A\n\tB   c "), "a b c")
        self.assertTrue(quote_in_text("only a FEW weeks", "Stocks last\n only a few   weeks now."))

    def test_typographic_quotes(self):
        self.assertTrue(quote_in_text("the firm’s supply chain", "the firm's supply chain"))
        self.assertTrue(quote_in_text('"several months"', "“several months”"))

    def test_negative(self):
        self.assertFalse(quote_in_text("several years", "would take several months"))
        self.assertFalse(quote_in_text("", "any text"))


if __name__ == "__main__":
    unittest.main()
