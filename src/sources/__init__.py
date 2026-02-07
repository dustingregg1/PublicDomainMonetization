"""Source text acquisition and processing modules."""

from .gutenberg import GutenbergSource
from .text_parser import TextParser, Chapter

__all__ = ["GutenbergSource", "TextParser", "Chapter"]
