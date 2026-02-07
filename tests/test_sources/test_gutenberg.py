"""Tests for Gutenberg source text downloader."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.sources.gutenberg import GutenbergSource, GUTENBERG_IDS


class TestGutenbergSource:
    """Tests for GutenbergSource class."""

    def test_known_book_ids(self) -> None:
        """Verify known Gutenberg IDs are configured."""
        assert GUTENBERG_IDS["last_and_first_men"] == 17662
        assert GUTENBERG_IDS["maltese_falcon"] is None
        assert GUTENBERG_IDS["strong_poison"] is None

    def test_strip_gutenberg_header_footer(self, tmp_path: Path) -> None:
        """Test header/footer stripping."""
        source = GutenbergSource(cache_dir=tmp_path)

        raw_text = """The Project Gutenberg eBook of Test Book

Produced by Someone

*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

Chapter I

This is the actual book content.
It spans multiple lines.

Chapter II

More content here.

*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

End of the Project Gutenberg EBook of Test Book
"""
        cleaned = source.strip_gutenberg_header_footer(raw_text)

        assert "*** START" not in cleaned
        assert "*** END" not in cleaned
        assert "Project Gutenberg" not in cleaned
        assert "Chapter I" in cleaned
        assert "actual book content" in cleaned
        assert "More content here" in cleaned

    def test_strip_no_markers(self, tmp_path: Path) -> None:
        """Test stripping when no Gutenberg markers exist."""
        source = GutenbergSource(cache_dir=tmp_path)
        text = "Just plain text\nwith no markers.\n"
        cleaned = source.strip_gutenberg_header_footer(text)
        assert "Just plain text" in cleaned

    def test_download_book_invalid_key(self, tmp_path: Path) -> None:
        """Test error for unknown book key."""
        source = GutenbergSource(cache_dir=tmp_path)
        with pytest.raises(ValueError, match="No Gutenberg ID"):
            source.download_book("nonexistent_book")

    def test_download_book_no_gutenberg_id(self, tmp_path: Path) -> None:
        """Test error for book without Gutenberg ID."""
        source = GutenbergSource(cache_dir=tmp_path)
        with pytest.raises(ValueError, match="No Gutenberg ID"):
            source.download_book("maltese_falcon")

    def test_cached_download(self, tmp_path: Path) -> None:
        """Test that cached files are reused."""
        source = GutenbergSource(cache_dir=tmp_path)
        cache_file = tmp_path / "pg12345_raw.txt"
        cache_file.write_text("cached content", encoding="utf-8")

        result = source.download_text(12345)
        assert result == "cached content"

    def test_download_and_clean_existing(self, tmp_path: Path) -> None:
        """Test skipping download when output already exists."""
        source = GutenbergSource(cache_dir=tmp_path)
        output = tmp_path / "existing.txt"
        output.write_text("already here", encoding="utf-8")

        result = source.download_and_clean(12345, output)
        assert result == output
