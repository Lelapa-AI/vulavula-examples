import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "qualification"))

from wer import word_error_rate  # noqa: E402


def test_identical_strings_have_zero_wer():
    assert word_error_rate("the quick brown fox", "the quick brown fox") == 0.0


def test_completely_different_strings_have_high_wer():
    assert word_error_rate("the quick brown fox", "a lazy sleepy dog") == 1.0


def test_partial_match_wer():
    # 1 substitution ("quick" -> "slow") out of 4 reference words.
    assert word_error_rate("the quick brown fox", "the slow brown fox") == 0.25


def test_empty_reference_and_hypothesis():
    assert word_error_rate("", "") == 0.0


def test_empty_reference_with_nonempty_hypothesis():
    assert word_error_rate("", "hello") == 1.0
