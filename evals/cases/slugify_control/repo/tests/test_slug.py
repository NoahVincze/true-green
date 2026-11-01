import unittest

from slug import slugify


class SlugTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_edges(self):
        self.assertEqual(slugify("  -- Tips & Tricks --  "), "tips-tricks")
