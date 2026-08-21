"""Parser for FHIR Zulip (chat.fhir.org) topic exports.

FHIR Zulip is the Link-only source in the per-source license matrix
(`docs/ATTRIBUTION-RENDERING.md`): "Not open-licensed; reference only" — no
message body is ever copied into the corpus, and README.md is explicit that
Zulip content is "linked, never mirrored." Every record this parser emits is
therefore a `LinkRecord`, not a `ParsedRecord`: `LinkRecord` has no field a
body could be assigned to, so "no body copied" holds structurally rather
than by convention.

Zulip organizes discussion into streams and topics rather than discrete
Q&A posts, so the natural mirrorable unit here is one *topic* (a
stream+subject thread), not one message — this parser's input is one row
per topic, not per message, matching how a caller would first fold a raw
Zulip message export (`GET /api/v1/messages`, https://zulip.com/api/get-messages)
down to its topic-starting message before handing rows to `parse_topics`.

Zulip's own "narrow" topic-link hash encoding (stream-id/topic-name
slugification) is an internal, undocumented algorithm — reimplementing it
here would risk emitting a link that silently fails to resolve to the real
topic, which `docs/ATTRIBUTION-RENDERING.md` calls out as a patient-safety
and legal boundary. So, mirroring `biostars.parser`'s approach to its own
`url` field, this parser takes the topic's `url` as already-resolved input
and only validates it (https-only, host must match `site_url`) rather than
constructing it from stream/topic names.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError

from ..license import License
from ..models import Attribution, LinkRecord, SkippedRow


def parse_topics(
    topics_json_path: Path,
    *,
    site_name: str = "FHIR Zulip",
    site_url: str = "https://chat.fhir.org",
) -> Iterator[LinkRecord | SkippedRow]:
    """Parse a FHIR Zulip topic-export JSON array into link-only records.

    `topics_json_path` holds a JSON array of topic-summary objects, each
    shaped like `{id, stream, topic, sender_full_name, timestamp, url}`
    (`id` uniquely identifies the topic at export time, e.g. its anchor
    message id; `timestamp` is Unix seconds). `site_url` is the FHIR Zulip
    realm's origin; each row's `url` must resolve to that same host.
    """
    rows: Any = json.loads(topics_json_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(
            f"expected a top-level JSON array of topics, got {type(rows).__name__}"
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
        row_id = str(data.get("id") or "<unknown>")
        try:
            yield _parse_row(data, site_name=site_name, site_url=site_url)
        except (ValidationError, ValueError) as exc:
            yield SkippedRow(row_id=row_id, reason=str(exc))


def _parse_row(
    data: dict[str, Any],
    *,
    site_name: str,
    site_url: str,
) -> LinkRecord:
    row_id = data.get("id")
    if not row_id:
        raise ValueError("row has no id")
    row_id = str(row_id)

    topic = data.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("row has no topic")

    author = data.get("sender_full_name")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("row has no attributable author")

    timestamp = data.get("timestamp")
    if not isinstance(timestamp, int | float) or isinstance(timestamp, bool):
        raise ValueError("row has no timestamp")
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    url = data.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError("row has no url")
    link = _validate_link(url, site_url=site_url)

    stream = data.get("stream")
    tags = (stream,) if isinstance(stream, str) and stream.strip() else ()

    attribution = Attribution(
        source=site_name,
        author=author,
        license=License.LINK_ONLY,
        date=date,
        link=link,  # type: ignore[arg-type]  # pydantic HttpUrl coerces str
    )

    return LinkRecord(
        record_id=row_id,
        title=topic,
        tags=tags,
        attribution=attribution,
    )


def _validate_link(url: str, *, site_url: str) -> str:
    """Return `url` unchanged once verified safe to render as the source link.

    The Link field is a patient-safety/legal boundary
    (`docs/ATTRIBUTION-RENDERING.md`): it must resolve to the real source
    topic so the next reader can verify provenance. Unlike `biostars.parser`,
    this parser never joins a relative path onto `site_url` — Zulip's narrow
    link encoding is not reimplemented here (see module docstring), so the
    caller must always supply an already-resolved, absolute URL. `https://`
    is required (an `http://` link is refused rather than trusted, since a
    protocol downgrade would let a MITM substitute content under the same
    provenance boundary), and the URL's host must match `site_url`'s host.
    """
    if url.startswith("http://"):
        raise ValueError(f"absolute url must use https, not http ({url!r})")
    if not url.startswith("https://"):
        raise ValueError(f"url must be an absolute https:// URL ({url!r})")
    if urlparse(url).netloc != urlparse(site_url).netloc:
        raise ValueError(
            f"absolute url host does not match site_url ({url!r} vs {site_url!r})"
        )
    return url
