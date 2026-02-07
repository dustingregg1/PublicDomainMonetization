"""Tests for text parser module."""

import pytest
from pathlib import Path

from src.sources.text_parser import TextParser, Chapter, roman_to_int


class TestRomanNumerals:
    """Tests for roman numeral conversion."""

    def test_basic_numerals(self) -> None:
        assert roman_to_int("I") == 1
        assert roman_to_int("V") == 5
        assert roman_to_int("X") == 10
        assert roman_to_int("XVI") == 16

    def test_subtractive_forms(self) -> None:
        assert roman_to_int("IV") == 4
        assert roman_to_int("IX") == 9
        assert roman_to_int("XIV") == 14

    def test_case_insensitive(self) -> None:
        assert roman_to_int("xvi") == 16
        assert roman_to_int("Iv") == 4

    def test_invalid_returns_zero(self) -> None:
        assert roman_to_int("ABC") == 0


class TestTextParser:
    """Tests for TextParser class."""

    def test_parse_simple_chapters(self) -> None:
        """Test parsing text with CHAPTER headings."""
        text = """
CHAPTER I

This is the first chapter. It contains enough words to pass
the minimum threshold for a valid chapter. We need at least
five hundred words so let me keep writing more content here
to make this a proper test case for our parser module.
""" + " word" * 500 + """

CHAPTER II

This is the second chapter with more content to parse.
""" + " word" * 500

        parser = TextParser(min_chapter_words=100)
        chapters = parser.parse_text(text)

        assert len(chapters) >= 2
        assert chapters[0].chapter_num == 1
        assert chapters[1].chapter_num == 2

    def test_parse_roman_numeral_chapters(self) -> None:
        """Test parsing with roman numeral chapter headings."""
        text = """
Chapter I: The Beginning

This is the beginning of the story with many words.
""" + " word" * 500 + """

Chapter II: The Middle

This is the middle of the story with many words.
""" + " word" * 500 + """

Chapter III: The End

This is the end of the story with many words.
""" + " word" * 500

        parser = TextParser(min_chapter_words=100)
        chapters = parser.parse_text(text)

        assert len(chapters) == 3
        assert "Beginning" in chapters[0].title

    def test_parse_no_chapters(self) -> None:
        """Test parsing text with no chapter markers."""
        text = "Just a plain text with no chapter markers.\n" * 100

        parser = TextParser(min_chapter_words=10)
        chapters = parser.parse_text(text)

        assert len(chapters) == 1
        assert chapters[0].title == "Full Text"

    def test_word_count(self) -> None:
        """Test that word counts are calculated."""
        text = "CHAPTER I\n\n" + "word " * 1000 + "\nCHAPTER II\n\n" + "word " * 500

        parser = TextParser(min_chapter_words=100)
        chapters = parser.parse_text(text)

        assert len(chapters) >= 1
        assert chapters[0].word_count > 0

    def test_chapter_dataclass(self) -> None:
        """Test Chapter dataclass initialization."""
        ch = Chapter(
            chapter_id="ch_1",
            chapter_num=1,
            title="Test Chapter",
            text="one two three four five",
        )
        assert ch.word_count == 5
        assert ch.chapter_id == "ch_1"

    def test_short_chapter_merging(self) -> None:
        """Test that short chapters are merged."""
        text = """
CHAPTER I

Very short.

CHAPTER II

This is a proper length chapter with enough content.
""" + " word" * 500

        parser = TextParser(min_chapter_words=100)
        chapters = parser.parse_text(text)

        # Short chapter should be merged
        assert len(chapters) == 1

    def test_parse_file(self, tmp_path: Path) -> None:
        """Test parsing from file."""
        text = "CHAPTER I\n\n" + "word " * 600 + "\nCHAPTER II\n\n" + "word " * 600
        test_file = tmp_path / "test.txt"
        test_file.write_text(text, encoding="utf-8")

        parser = TextParser(min_chapter_words=100)
        chapters = parser.parse_file(test_file)

        assert len(chapters) >= 1

    def test_chapter_summary(self) -> None:
        """Test summary generation."""
        chapters = [
            Chapter("ch_1", 1, "First", "word " * 1000),
            Chapter("ch_2", 2, "Second", "word " * 500),
        ]

        parser = TextParser()
        summary = parser.get_chapter_summary(chapters)

        assert "2 chapters" in summary
        assert "1,500" in summary  # total words
