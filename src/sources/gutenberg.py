"""
Project Gutenberg Source Text Downloader

Downloads and cleans public domain texts from Project Gutenberg.
Strips Gutenberg headers/footers and produces clean text files.
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Known Gutenberg book IDs for our titles
GUTENBERG_IDS = {
    "last_and_first_men": 17662,
    "maltese_falcon": None,  # Not on Gutenberg (1930 US PD but not uploaded)
    "strong_poison": None,   # Not on Gutenberg
}


class GutenbergSource:
    """Download and clean texts from Project Gutenberg."""

    BASE_URL = "https://www.gutenberg.org"
    MIRROR_URL = "https://www.gutenberg.org/cache/epub"

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or Path.cwd() / "texts" / ".gutenberg_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_text(self, book_id: int, force: bool = False) -> str:
        """
        Download raw text from Project Gutenberg.

        Args:
            book_id: Gutenberg ebook ID number
            force: Re-download even if cached

        Returns:
            Raw text content
        """
        cache_file = self.cache_dir / f"pg{book_id}_raw.txt"

        if cache_file.exists() and not force:
            logger.info(f"Using cached text for PG#{book_id}")
            return cache_file.read_text(encoding="utf-8")

        # Try plain text UTF-8 format first
        urls = [
            f"{self.MIRROR_URL}/{book_id}/pg{book_id}.txt",
            f"{self.BASE_URL}/files/{book_id}/{book_id}-0.txt",
            f"{self.BASE_URL}/files/{book_id}/{book_id}.txt",
        ]

        for url in urls:
            try:
                logger.info(f"Downloading from {url}")
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    text = resp.text
                    cache_file.write_text(text, encoding="utf-8")
                    logger.info(
                        f"Downloaded PG#{book_id}: {len(text):,} characters"
                    )
                    return text
                logger.debug(f"Got {resp.status_code} from {url}")
            except requests.RequestException as e:
                logger.warning(f"Failed to download from {url}: {e}")
                time.sleep(1)

        raise RuntimeError(
            f"Could not download PG#{book_id} from any mirror"
        )

    def strip_gutenberg_header_footer(self, text: str) -> str:
        """
        Remove Project Gutenberg header and footer boilerplate.

        Args:
            text: Raw Gutenberg text

        Returns:
            Clean text with boilerplate removed
        """
        lines = text.split("\n")
        start_idx = 0
        end_idx = len(lines)

        # Find start marker
        start_patterns = [
            r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG",
            r"\*\*\*\s*START OF THE PROJECT",
        ]
        for i, line in enumerate(lines):
            for pattern in start_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    start_idx = i + 1
                    break
            if start_idx > 0:
                break

        # Find end marker
        end_patterns = [
            r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG",
            r"\*\*\*\s*END OF THE PROJECT",
        ]
        for i in range(len(lines) - 1, -1, -1):
            for pattern in end_patterns:
                if re.search(pattern, lines[i], re.IGNORECASE):
                    end_idx = i
                    break
            if end_idx < len(lines):
                break

        # Skip any remaining preamble (title page, ToC lines before actual text)
        clean_lines = lines[start_idx:end_idx]

        # Strip leading/trailing blank lines
        while clean_lines and not clean_lines[0].strip():
            clean_lines.pop(0)
        while clean_lines and not clean_lines[-1].strip():
            clean_lines.pop()

        return "\n".join(clean_lines)

    def download_and_clean(
        self,
        book_id: int,
        output_path: Path,
        force: bool = False,
    ) -> Path:
        """
        Download, clean, and save a Gutenberg text.

        Args:
            book_id: Gutenberg ebook ID
            output_path: Where to save cleaned text
            force: Re-download even if output exists

        Returns:
            Path to cleaned text file
        """
        if output_path.exists() and not force:
            logger.info(f"Clean text already exists at {output_path}")
            return output_path

        raw_text = self.download_text(book_id, force=force)
        clean_text = self.strip_gutenberg_header_footer(raw_text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(clean_text, encoding="utf-8")

        logger.info(
            f"Saved clean text to {output_path} "
            f"({len(clean_text):,} chars)"
        )
        return output_path

    def download_book(
        self,
        book_key: str,
        output_dir: Optional[Path] = None,
        force: bool = False,
    ) -> Path:
        """
        Download a known book by its project key.

        Args:
            book_key: Book identifier (e.g., 'last_and_first_men')
            output_dir: Output directory (defaults to texts/)
            force: Re-download

        Returns:
            Path to cleaned text file
        """
        gutenberg_id = GUTENBERG_IDS.get(book_key)
        if gutenberg_id is None:
            raise ValueError(
                f"No Gutenberg ID for '{book_key}'. "
                f"Available: {[k for k, v in GUTENBERG_IDS.items() if v]}"
            )

        output_dir = output_dir or Path.cwd() / "texts"
        output_path = output_dir / f"{book_key}_clean.txt"

        return self.download_and_clean(gutenberg_id, output_path, force=force)
