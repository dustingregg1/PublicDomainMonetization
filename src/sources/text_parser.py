"""
Text Parser for Audiobook Production

Parses cleaned source texts into chapter structures suitable for
TTS synthesis. Handles various chapter/section formats.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """A parsed chapter with text content."""
    chapter_id: str
    chapter_num: int
    title: str
    text: str
    word_count: int = 0
    part: Optional[str] = None

    def __post_init__(self) -> None:
        if self.word_count == 0:
            self.word_count = len(self.text.split())


# Chapter heading patterns for various books
CHAPTER_PATTERNS = [
    # "CHAPTER I", "CHAPTER 1", "CHAPTER ONE"
    r"^CHAPTER\s+([IVXLCDM]+|\d+|[A-Z]+)\b",
    # "Chapter I.", "Chapter 1."
    r"^Chapter\s+([IVXLCDM]+|\d+)\b",
    # "I.", "II.", "III." at start of line (Roman numeral sections)
    r"^([IVXLCDM]{1,6})\.\s*$",
    # "1.", "2." etc. at start of line
    r"^(\d{1,3})\.\s+[A-Z]",
]

# Part/section heading patterns
PART_PATTERNS = [
    r"^PART\s+([IVXLCDM]+|\d+|ONE|TWO|THREE|FOUR|FIVE)",
    r"^Part\s+([IVXLCDM]+|\d+)",
    r"^BOOK\s+([IVXLCDM]+|\d+)",
]

ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
}


def roman_to_int(s: str) -> int:
    """Convert roman numeral string to integer."""
    s = s.upper().strip()
    if s in ROMAN_MAP:
        return ROMAN_MAP[s]
    # Fallback calculation
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    for i, c in enumerate(s):
        if c not in values:
            return 0
        if i + 1 < len(s) and values.get(c, 0) < values.get(s[i + 1], 0):
            result -= values[c]
        else:
            result += values[c]
    return result


class TextParser:
    """Parse source texts into chapter structures for TTS processing."""

    def __init__(
        self,
        min_chapter_words: int = 500,
        max_chapter_words: int = 15000,
    ) -> None:
        """
        Args:
            min_chapter_words: Minimum words to consider a valid chapter
            max_chapter_words: Maximum words before splitting a chapter
        """
        self.min_chapter_words = min_chapter_words
        self.max_chapter_words = max_chapter_words

    def parse_file(self, file_path: Path) -> List[Chapter]:
        """
        Parse a text file into chapters.

        Args:
            file_path: Path to cleaned text file

        Returns:
            List of Chapter objects
        """
        text = file_path.read_text(encoding="utf-8")
        return self.parse_text(text)

    def parse_text(self, text: str) -> List[Chapter]:
        """
        Parse raw text into chapters.

        Uses heuristics to detect chapter boundaries.

        Args:
            text: Full book text

        Returns:
            List of Chapter objects
        """
        lines = text.split("\n")

        # Detect chapter boundaries
        boundaries = self._find_chapter_boundaries(lines)

        if not boundaries:
            logger.warning("No chapter boundaries found, treating as single chapter")
            return [
                Chapter(
                    chapter_id="ch_1",
                    chapter_num=1,
                    title="Full Text",
                    text=text.strip(),
                )
            ]

        # Extract chapters from boundaries
        chapters = self._extract_chapters(lines, boundaries)

        # Validate and clean
        chapters = self._validate_chapters(chapters)

        logger.info(
            f"Parsed {len(chapters)} chapters, "
            f"total {sum(c.word_count for c in chapters):,} words"
        )

        return chapters

    def _find_chapter_boundaries(
        self, lines: List[str]
    ) -> List[dict]:
        """Find line indices where chapters begin."""
        boundaries = []
        current_part = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for part/book headings
            for pattern in PART_PATTERNS:
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    current_part = match.group(0).strip()
                    break

            # Check for chapter headings
            for pattern in CHAPTER_PATTERNS:
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    # Get chapter number
                    num_str = match.group(1)
                    try:
                        num = int(num_str)
                    except ValueError:
                        num = roman_to_int(num_str)

                    if num == 0:
                        continue

                    # Get title (might be on same line or next non-blank line)
                    title = self._extract_chapter_title(lines, i, stripped)

                    boundaries.append({
                        "line": i,
                        "num": num,
                        "title": title,
                        "part": current_part,
                    })
                    break

        return boundaries

    def _extract_chapter_title(
        self, lines: List[str], heading_line: int, heading_text: str
    ) -> str:
        """Extract chapter title from heading and nearby lines."""
        # Check if title is on the same line after chapter number
        # e.g., "CHAPTER I: Balkan Europe"
        colon_match = re.search(r"[:\.\-—]\s*(.+)$", heading_text)
        if colon_match:
            return colon_match.group(1).strip()

        # Check if title is after chapter number on same line
        # e.g., "CHAPTER I  Balkan Europe"
        title_match = re.match(
            r"^(?:CHAPTER|Chapter)\s+(?:[IVXLCDM]+|\d+)\s{2,}(.+)$",
            heading_text,
        )
        if title_match:
            return title_match.group(1).strip()

        # Check next non-blank line for title
        for j in range(heading_line + 1, min(heading_line + 4, len(lines))):
            next_line = lines[j].strip()
            if next_line:
                # If it looks like a title (short, capitalized, no period at end)
                if (
                    len(next_line) < 80
                    and not next_line.endswith(".")
                    and next_line[0].isupper()
                ):
                    return next_line
                break

        return heading_text.strip()

    def _extract_chapters(
        self, lines: List[str], boundaries: List[dict]
    ) -> List[Chapter]:
        """Extract chapter text between boundaries."""
        chapters = []

        for i, boundary in enumerate(boundaries):
            start = boundary["line"]

            # End is start of next chapter, or end of text
            if i + 1 < len(boundaries):
                end = boundaries[i + 1]["line"]
            else:
                end = len(lines)

            # Skip heading lines (chapter title etc.)
            text_start = start
            # Skip blank lines after heading
            for j in range(start, min(start + 5, end)):
                if lines[j].strip() and not re.match(
                    r"^(CHAPTER|Chapter|PART|Part|BOOK|Book|\d+\.|[IVXLCDM]+\.)",
                    lines[j].strip(),
                ):
                    text_start = j
                    break
                text_start = j + 1

            chapter_text = "\n".join(lines[text_start:end]).strip()

            # Clean up excessive whitespace
            chapter_text = re.sub(r"\n{3,}", "\n\n", chapter_text)

            chapter = Chapter(
                chapter_id=f"ch_{boundary['num']}",
                chapter_num=boundary["num"],
                title=boundary["title"],
                text=chapter_text,
                part=boundary.get("part"),
            )
            chapters.append(chapter)

        return chapters

    def _validate_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        """Validate and clean chapter list."""
        valid = []

        for ch in chapters:
            if ch.word_count < self.min_chapter_words:
                logger.warning(
                    f"Chapter {ch.chapter_num} '{ch.title}' too short "
                    f"({ch.word_count} words), merging with next"
                )
                # Merge short chapters with the next one
                if valid:
                    valid[-1].text += "\n\n" + ch.text
                    valid[-1].word_count = len(valid[-1].text.split())
                continue

            if ch.word_count > self.max_chapter_words:
                logger.info(
                    f"Chapter {ch.chapter_num} '{ch.title}' is long "
                    f"({ch.word_count} words), keeping as-is"
                )

            valid.append(ch)

        # Renumber if needed
        for i, ch in enumerate(valid):
            ch.chapter_num = i + 1
            ch.chapter_id = f"ch_{i + 1}"

        return valid

    def get_chapter_summary(self, chapters: List[Chapter]) -> str:
        """Generate a summary of parsed chapters."""
        lines = [f"Parsed {len(chapters)} chapters:\n"]
        total_words = 0

        for ch in chapters:
            part_str = f" [{ch.part}]" if ch.part else ""
            lines.append(
                f"  Ch {ch.chapter_num:2d}: {ch.title:<40s} "
                f"{ch.word_count:>6,} words{part_str}"
            )
            total_words += ch.word_count

        lines.append(f"\nTotal: {total_words:,} words")
        est_hours = (total_words / 150) / 60  # ~150 wpm narration
        lines.append(f"Estimated audio duration: {est_hours:.1f} hours")

        return "\n".join(lines)
