import unittest

from slug import slugify


class HiddenSlug(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(slugify("What is new in 2026?"), "what-is-new-in-2026")
        self.assertEqual(slugify("a___b"), "a-b")
        self.assertEqual(slugify("Already-slugged"), "already-slugged")
