"""License marker shared by every source-specific parser.

Mirrors `qa_core::domain::license::License` (Rust) field-for-field so a
parsed record's `license.value` round-trips through `License::new()` on the
Rust side without a translation table. Parse-Don't-Validate: only these four
canonical strings are constructible; an unrecognized source license must
never reach a `ParsedRecord`.
"""

from enum import Enum


class License(str, Enum):
    """A license marker for content provenance (mirrors qa-core's `License`)."""

    CC_BY_SA_4 = "cc-by-sa-4.0"
    CC_BY_4 = "cc-by-4.0"
    NATIVE = "native"
    LINK_ONLY = "link-only"
