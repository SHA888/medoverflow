"""Parser for the Biostars API's post JSON schema (`/api/post/{id}/`).

Biostars (biostars.org) is the CC BY 4.0 source in the per-source license
matrix (`docs/ATTRIBUTION-RENDERING.md`); every record this parser emits
carries `License.CC_BY_4` and a fully populated `Attribution`. Only
``Question`` and ``Answer`` post types are imported — other types (Comment,
Discussion, ...) are out of scope for the Q&A corpus and are skipped.

Field names below match the documented Biostars API response shape
(https://www.biostars.org/info/api/, `GET /api/post/{id}/`): ``xhtml`` is the
HTML body, ``tag_val`` is a comma-separated tag string, and ``root_id`` is
the id of the top-level question — used here (not the immediate
``parent_id``) as an answer's parent, since ``root_id`` still resolves to
the question even for a reply nested under a comment.

Unlike the Stack Exchange dump (a single multi-gigabyte XML export requiring
streaming), a Biostars pull is expected to be a much smaller, pre-filtered
JSON array (see task 3.2.3's topic filter), so this parser loads it whole.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError

from ..license import License
from ..models import Attribution, ParsedRecord

_POST_TYPE_QUESTION = "Question"
_POST_TYPE_ANSWER = "Answer"


@dataclass(frozen=True)
class SkippedRow:
    """A dump row that could not be parsed into a `ParsedRecord`.

    Kept as explicit data — never raised past the caller and never silently
    dropped — so a full ingestion run can report every unparsed row instead
    of aborting on the first bad one.
    """

    row_id: str
    reason: str


def parse_posts(
    posts_json_path: Path,
    *,
    site_name: str = "Biostars",
    site_url: str = "https://www.biostars.org",
) -> Iterator[ParsedRecord | SkippedRow]:
    """Parse a Biostars post-JSON export into attributed records.

    `posts_json_path` holds a JSON array of post objects shaped like the
    Biostars API's `/api/post/{id}/` response. `site_url` is used to
    resolve any post whose `url` field is a relative path rather than
    already-absolute.
    """
    rows: Any = json.loads(posts_json_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(
            f"expected a top-level JSON array of posts, got {type(rows).__name__}"
        )

    for data in rows:
        # An externally-sourced feed can contain anything; a non-object row
        # must become a SkippedRow, never crash the whole run. `.get("id")`
        # is only safe once we know `data` is a dict, so derive row_id after
        # the type guard.
        if not isinstance(data, dict):
            yield SkippedRow(
                row_id="<unknown>",
                reason=f"row is not a JSON object (got {type(data).__name__})",
            )
            continue
        row_id = str(data.get("id", "<unknown>"))
        try:
            yield _parse_row(data, site_name=site_name, site_url=site_url)
        except (ValidationError, ValueError) as exc:
            yield SkippedRow(row_id=row_id, reason=str(exc))


def _parse_row(
    data: dict[str, Any],
    *,
    site_name: str,
    site_url: str,
) -> ParsedRecord:
    row_id = data.get("id")
    if row_id is None:
        raise ValueError("row is missing its id field")
    row_id = str(row_id)

    post_type = data.get("type")
    if post_type == _POST_TYPE_QUESTION:
        kind: str = "question"
        title = data.get("title")
        parent_id = None
    elif post_type == _POST_TYPE_ANSWER:
        kind = "answer"
        # The real API returns "A: <question title>" as an answer's raw
        # title; ParsedRecord forbids a title on an answer, so it is
        # discarded rather than passed through.
        title = None
        root_id = data.get("root_id")
        if root_id is None:
            raise ValueError("answer row has no root_id")
        parent_id = str(root_id)
    else:
        raise ValueError(
            f"unsupported post type {post_type!r}; only Question/Answer are imported"
        )

    author = data.get("author")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("row has no attributable author")

    body_html = data.get("xhtml")
    if not isinstance(body_html, str) or not body_html.strip():
        raise ValueError("row has no xhtml body")

    creation_date_raw = data.get("creation_date")
    if not isinstance(creation_date_raw, str) or not creation_date_raw:
        raise ValueError("row has no creation_date")
    try:
        creation_date: datetime = datetime.fromisoformat(creation_date_raw)
    except ValueError as exc:
        raise ValueError(f"unparseable creation_date {creation_date_raw!r}") from exc

    tags = _parse_tags(data.get("tag_val")) if kind == "question" else ()

    url = data.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError("row has no url")
    link = _resolve_link(url, site_url=site_url)

    attribution = Attribution(
        source=site_name,
        author=author,
        license=License.CC_BY_4,
        date=creation_date,
        link=link,  # type: ignore[arg-type]  # pydantic HttpUrl coerces str
    )

    return ParsedRecord(
        record_id=row_id,
        kind=kind,  # type: ignore[arg-type]  # narrowed to the Literal above
        title=title,
        body_html=body_html,
        tags=tags,
        parent_id=parent_id,
        attribution=attribution,
    )


def _resolve_link(url: str, *, site_url: str) -> str:
    """Return an absolute post URL, trusting an absolute `url` only if its
    host matches `site_url`.

    The Link field is a patient-safety/legal boundary
    (`docs/ATTRIBUTION-RENDERING.md`): it must resolve to the real source
    post so the next reader can verify provenance. A relative `url` is
    joined onto `site_url`; an absolute `url` is accepted only when it is
    `https://` *and* points at `site_url`'s own host, otherwise it is
    rejected. A spoofed or off-site absolute URL must not be rendered under
    the "Biostars" label, and an `http://` link is refused rather than
    trusted (a protocol downgrade would let a MITM substitute content under
    the same provenance boundary).
    """
    if not url.startswith(("http://", "https://")):
        return f"{site_url}/{url.lstrip('/')}"
    if url.startswith("http://"):
        raise ValueError(f"absolute url must use https, not http ({url!r})")
    if urlparse(url).netloc != urlparse(site_url).netloc:
        raise ValueError(
            f"absolute url host does not match site_url ({url!r} vs {site_url!r})"
        )
    return url


def _parse_tags(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw:
        return ()
    return tuple(t.strip() for t in raw.split(",") if t.strip())
