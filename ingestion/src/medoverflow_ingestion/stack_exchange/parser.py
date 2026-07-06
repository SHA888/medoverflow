"""Parser for the Stack Exchange data-dump XML format (`Posts.xml`/`Users.xml`).

Stack Exchange dumps (archive.org) are the CC BY-SA 4.0 source in the
per-source license matrix (`docs/ATTRIBUTION-RENDERING.md`); every record
this parser emits carries `License.CC_BY_SA_4` and a fully populated
`Attribution`. Only questions (`PostTypeId="1"`) and answers
(`PostTypeId="2"`) are imported — other post types (tag wikis, moderator
notices, ...) are out of scope for the Q&A corpus and are skipped.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET
from pydantic import ValidationError

from ..license import License
from ..models import Attribution, ParsedRecord

_POST_TYPE_QUESTION = "1"
_POST_TYPE_ANSWER = "2"


@dataclass(frozen=True)
class SkippedRow:
    """A dump row that could not be parsed into a `ParsedRecord`.

    Kept as explicit data — never raised past the caller and never silently
    dropped — so a full ingestion run can report every unparsed row instead
    of aborting the whole dump on the first bad one.
    """

    row_id: str
    reason: str


def parse_posts(
    posts_xml_path: Path,
    users_xml_path: Path,
    *,
    site_name: str,
    site_url: str,
) -> Iterator[ParsedRecord | SkippedRow]:
    """Parse a Stack Exchange `Posts.xml` dump into attributed records.

    `site_url` is the site's base URL (no trailing slash), used to build each
    record's attribution link following Stack Exchange's own URL scheme:
    questions as `{site_url}/questions/{id}`, answers as `{site_url}/a/{id}`.
    """
    display_names = _load_display_names(users_xml_path)

    for elem in _iter_rows(posts_xml_path):
        row_id = elem.get("Id", "<unknown>")
        try:
            yield _parse_row(
                elem, display_names, site_name=site_name, site_url=site_url
            )
        except (ValidationError, ValueError) as exc:
            yield SkippedRow(row_id=row_id, reason=str(exc))


def _load_display_names(users_xml_path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    for elem in _iter_rows(users_xml_path):
        user_id = elem.get("Id")
        display_name = elem.get("DisplayName")
        if user_id is not None and display_name:
            names[user_id] = display_name
    return names


def _iter_rows(xml_path: Path) -> Iterator[Element]:
    """Stream `<row>` elements from an SE dump file with bounded memory use.

    `elem.clear()` alone only empties the row element itself; it stays
    attached to the document root, so the root's child list — and thus
    memory use — would otherwise grow linearly with the file instead of
    staying bounded. Clearing the root once each row has been consumed (not
    just the row element) keeps memory bounded regardless of dump size.
    """
    context = iter(ET.iterparse(xml_path, events=("start", "end")))
    _, root = next(context)  # the first event is always the root's start
    for event, elem in context:
        if event != "end" or elem.tag != "row":
            continue
        yield elem
        root.clear()


def _parse_row(
    elem: Element,
    display_names: dict[str, str],
    *,
    site_name: str,
    site_url: str,
) -> ParsedRecord:
    row_id = elem.get("Id")
    if not row_id:
        raise ValueError("row is missing its Id attribute")

    post_type = elem.get("PostTypeId")
    if post_type == _POST_TYPE_QUESTION:
        kind: str = "question"
        link = f"{site_url}/questions/{row_id}"
    elif post_type == _POST_TYPE_ANSWER:
        kind = "answer"
        link = f"{site_url}/a/{row_id}"
    else:
        raise ValueError(
            f"unsupported PostTypeId {post_type!r}; only questions/answers are imported"
        )

    author = elem.get("OwnerDisplayName")
    if not author:
        owner_id = elem.get("OwnerUserId")
        author = display_names.get(owner_id) if owner_id else None
    if not author:
        raise ValueError(
            "no attributable author (OwnerUserId and OwnerDisplayName both missing)"
        )

    body_html = elem.get("Body")
    if not body_html:
        raise ValueError("row has no Body")

    creation_date_raw = elem.get("CreationDate")
    if not creation_date_raw:
        raise ValueError("row has no CreationDate")
    creation_date: datetime = datetime.fromisoformat(creation_date_raw)

    title = elem.get("Title") if kind == "question" else None
    parent_id = elem.get("ParentId") if kind == "answer" else None
    tags = _parse_tags(elem.get("Tags")) if kind == "question" else ()

    attribution = Attribution(
        source=site_name,
        author=author,
        license=License.CC_BY_SA_4,
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


def _parse_tags(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    if raw.startswith("<"):
        # Legacy dump encoding: "<tag1><tag2>" rather than space-separated.
        return tuple(t for t in raw.strip("<>").split("><") if t)
    return tuple(raw.split())
