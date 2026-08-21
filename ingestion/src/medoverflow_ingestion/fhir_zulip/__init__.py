"""FHIR Zulip link-only adapter (License.LINK_ONLY, per docs/ATTRIBUTION-RENDERING.md).

`parser` reads a topic-export JSON array and emits `LinkRecord`s — never
`ParsedRecord`s — so no message body is ever copied into the corpus.
"""

from ..models import SkippedRow
from .parser import parse_topics

__all__ = ["SkippedRow", "parse_topics"]
