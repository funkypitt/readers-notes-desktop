"""The tag rule: the same as the phone's Tags.kt (TagsTest).

    python3 -m pytest tests/        (or: python3 tests/test_tags.py)
"""
import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import readers_notes as rn  # noqa: E402


class TagsTest(unittest.TestCase):
    def test_tags_are_words_with_a_hash_once_each_lower_case(self):
        self.assertEqual(["work", "idée", "to-do"], rn.tags_of("Plan #Work\n#idée and #work again, #to-do."))

    def test_numbers_addresses_and_words_with_a_hash_inside_are_not_tags(self):
        self.assertEqual([], rn.tags_of("room #12, see https://x.ch/#top and C#"))

    def test_a_tag_at_the_very_start(self):
        self.assertEqual(["a"], rn.tags_of("#a b"))

    def test_clean_makes_a_tag_out_of_what_was_typed(self):
        self.assertEqual("deux-mots", rn.tag_clean(" #Deux mots "))
        self.assertIsNone(rn.tag_clean("#2026"))
        self.assertIsNone(rn.tag_clean(""))

    def test_add_puts_the_tag_on_its_own_line_at_the_end(self):
        self.assertEqual("Milk\nand eggs\n\n#shop", rn.tag_add("Milk\nand eggs\n", "shop"))

    def test_add_joins_a_line_that_holds_only_tags(self):
        self.assertEqual("Milk\n\n#shop #week", rn.tag_add("Milk\n\n#shop", "#Week"))

    def test_add_on_an_empty_note_and_twice(self):
        self.assertEqual("#a", rn.tag_add("", "a"))
        self.assertEqual("Milk #a", rn.tag_add("Milk #a", "A"))

    def test_remove_takes_the_tag_and_the_space_before_it(self):
        self.assertEqual("Milk\n\n#shop", rn.tag_remove("Milk\n\n#shop #week", "week"))
        self.assertEqual("Milk\n\n#week", rn.tag_remove("Milk\n\n#shop #week", "shop"))
        self.assertEqual("Milk", rn.tag_remove("Milk\n\n#shop", "shop"))
        self.assertEqual("Milk and eggs", rn.tag_remove("Milk #shop and eggs", "shop"))
        self.assertEqual("Milk", rn.tag_remove("#shop\nMilk", "shop"))

    def test_remove_leaves_a_tag_of_another_name(self):
        self.assertEqual("Milk #shopping", rn.tag_remove("Milk #shopping", "shop"))

    def test_count_most_used_first(self):
        self.assertEqual([("a", 2), ("b", 1), ("c", 1)], rn.tags_count(["#b #a", "#c #a"]))

    def test_label(self):
        self.assertEqual("#work #idée", rn.tags_label(["work", "idée"]))

    def test_preview_skips_a_line_of_tags(self):
        store = rn.Store(tempfile.mkdtemp(prefix="notes-test-"))
        a = store.create("Milk\n#shop #week\nand eggs")
        b = store.create("Milk\n\n#shop")
        self.assertEqual("and eggs", store.preview(a))
        self.assertEqual("", store.preview(b))


if __name__ == "__main__":
    unittest.main()
