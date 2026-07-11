"""Biostars import adapter (CC BY 4.0 source, per docs/ATTRIBUTION-RENDERING.md).

`client` fetches posts live from the Biostars API; `parser` parses a JSON
array of post payloads (whether pulled live via `client` or supplied as a
pre-fetched file) into attributed records.
"""

from ..models import SkippedRow
from .client import (
    DEFAULT_BASE_URL,
    BiostarsApiError,
    fetch_post_uids_for_tag,
    fetch_posts_to_json,
)
from .parser import parse_posts

__all__ = [
    "DEFAULT_BASE_URL",
    "BiostarsApiError",
    "SkippedRow",
    "fetch_post_uids_for_tag",
    "fetch_posts_to_json",
    "parse_posts",
]
