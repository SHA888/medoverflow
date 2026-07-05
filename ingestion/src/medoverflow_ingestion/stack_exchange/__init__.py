"""Stack Exchange dump parser (CC BY-SA 4.0 source, per docs/ATTRIBUTION-RENDERING.md)."""

from .parser import SkippedRow, parse_posts

__all__ = ["SkippedRow", "parse_posts"]
