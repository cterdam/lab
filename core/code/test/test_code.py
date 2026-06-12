import unittest

from core.code.src import code


class TestTokens(unittest.TestCase):
    def test_splits_and_uppercases(self):
        self.assertEqual(code.tokens("Sally Ma"), ["SALLY", "MA"])

    def test_hyphen_and_punct_separate(self):
        # Every non-letter — hyphen, apostrophe, space — ends a token.
        self.assertEqual(code.tokens("Jean-Luc O'Brien"), ["JEAN", "LUC", "O", "BRIEN"])

    def test_accents_folded_without_splitting(self):
        self.assertEqual(code.tokens("Renée Lévesque"), ["RENEE", "LEVESQUE"])

    def test_non_ascii_letters_drop_but_separate(self):
        # Cyrillic contributes nothing but does not glue neighbors together.
        self.assertEqual(code.tokens("Lex Борисов Jr"), ["LEX", "JR"])

    def test_empty(self):
        self.assertEqual(code.tokens("   "), [])
        self.assertEqual(code.tokens("良澤"), [])


class TestSkeleton(unittest.TestCase):
    def test_drops_inner_vowels_keeps_head(self):
        self.assertEqual(code.skeleton("Cheng"), "CHNG")
        self.assertEqual(code.skeleton("Saxena"), "SXN")
        self.assertEqual(code.skeleton("Ma"), "M")

    def test_leading_vowel_kept(self):
        self.assertEqual(code.skeleton("Apple"), "APPL")


class TestCandidates(unittest.TestCase):
    def test_initials_first(self):
        # Given the syllables as separate tokens, initials reproduce LLZ.
        self.assertEqual(next(code.candidates("Li Liang Ze")), "LLZ")

    def test_two_token_initials(self):
        self.assertEqual(next(code.candidates("Sally Ma")), "SM")

    def test_lengthens_from_first_token_when_last_is_exhausted(self):
        seq = list(code.candidates("Cheng Wei"))
        self.assertEqual(seq[0], "CW")
        self.assertIn("CHW", seq)
        self.assertTrue(all(c.startswith("C") for c in seq))

    def test_never_yields_single_letter(self):
        self.assertTrue(all(len(c) >= 2 for c in code.candidates("Cher")))
        self.assertEqual(next(code.candidates("Cher")), "CH")

    def test_org_single_word_grows_skeleton(self):
        seq = list(code.candidates("Apple", org=True))
        self.assertEqual(seq[0], "AP")
        self.assertIn("APPL", seq)

    def test_org_acronym_skips_stopwords(self):
        # Corp is a stopword, so the acronym is of Acme + Robotics.
        self.assertEqual(next(code.candidates("Acme Robotics Corp", org=True)), "AR")

    def test_no_letters_yields_nothing(self):
        self.assertEqual(list(code.candidates("良澤")), [])


class TestPropose(unittest.TestCase):
    def test_shortest_free_code(self):
        self.assertEqual(code.propose("Li Liang Ze", set()), "LLZ")

    def test_lengthens_past_a_taken_code(self):
        self.assertEqual(code.propose("Cheng Wei", {"CW"}), "CHW")

    def test_real_ppl_collisions(self):
        taken = {"LLZ", "MXY", "LVB", "NKSX", "BRR", "CHWE", "YSD", "ZXD", "CZY"}
        out = code.propose("Wei Cheng", taken)
        self.assertNotIn(out, taken)
        self.assertTrue(out.isupper() and out.isalpha())

    def test_lengthens_via_a_richer_skeleton(self):
        # "Liang" has consonants past its initial (LNG), so a taken LLZ still
        # has a longer letter form to fall to before any digit.
        self.assertEqual(code.propose("Li Liang Ze", {"LLZ"}), "LLNZ")

    def test_digit_fallback_when_letters_exhausted(self):
        # Every skeleton is a single letter, so ABC is the only letter form; a
        # collision forces the digit tail.
        self.assertEqual(code.propose("A B C", {"ABC"}), "ABC2")

    def test_raises_without_letters(self):
        with self.assertRaises(ValueError):
            code.propose("良澤", set())


if __name__ == "__main__":
    unittest.main()
