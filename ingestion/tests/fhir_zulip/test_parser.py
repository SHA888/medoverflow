"""Tests for the FHIR Zulip link-only adapter (task 3.1.3)."""

from pathlib import Path

import pytest

from medoverflow_ingestion.fhir_zulip import SkippedRow, parse_topics
from medoverflow_ingestion.license import License
from medoverflow_ingestion.models import LinkRecord

FIXTURES = Path(__file__).parent / "fixtures"
SITE_NAME = "FHIR Zulip"
SITE_URL = "https://chat.fhir.org"


def _parse_fixture() -> list[LinkRecord | SkippedRow]:
    return list(
        parse_topics(
            FIXTURES / "topics.json",
            site_name=SITE_NAME,
            site_url=SITE_URL,
        )
    )


def _records(rows: list[LinkRecord | SkippedRow]) -> list[LinkRecord]:
    return [r for r in rows if isinstance(r, LinkRecord)]


def _skipped(rows: list[LinkRecord | SkippedRow]) -> list[SkippedRow]:
    return [r for r in rows if isinstance(r, SkippedRow)]


def test_parses_topic_as_link_record_with_full_attribution() -> None:
    records = _records(_parse_fixture())

    topic = next(r for r in records if r.record_id == "5001")
    assert topic.title == "SNOMED CT mapping for lab panels"
    assert topic.tags == ("terminology",)
    assert topic.attribution.source == SITE_NAME
    assert topic.attribution.author == "Amara Chen"
    assert topic.attribution.license == License.LINK_ONLY
    assert (
        str(topic.attribution.link)
        == f"{SITE_URL}/#narrow/stream/179-terminology/topic/SNOMED.20CT.20mapping.20for.20lab.20panels"
    )
    assert topic.attribution.date.isoformat() == "2024-01-01T00:00:00+00:00"


def test_every_emitted_record_carries_link_only_license_no_body() -> None:
    for record in _records(_parse_fixture()):
        assert record.attribution.license == License.LINK_ONLY
        assert record.attribution.source
        assert record.attribution.author
        assert record.attribution.link is not None
        assert not any("body" in name for name in type(record).model_fields)


def test_total_row_count_accounts_for_every_row() -> None:
    rows = _parse_fixture()
    assert len(rows) == 8
    assert len(_records(rows)) == 2
    assert len(_skipped(rows)) == 6


@pytest.mark.parametrize(
    ("row_id", "reason_fragment"),
    [
        ("5003", "no topic"),
        ("5004", "no attributable author"),
        ("5005", "no timestamp"),
    ],
)
def test_unparseable_rows_become_skipped_rows_not_silent_drops(
    row_id: str, reason_fragment: str
) -> None:
    skipped = {s.row_id: s for s in _skipped(_parse_fixture())}
    assert row_id in skipped
    assert reason_fragment in skipped[row_id].reason


def test_row_with_empty_id_is_skipped_under_unknown_marker() -> None:
    skipped = _skipped(_parse_fixture())
    assert any("no id" in s.reason for s in skipped)


def test_offsite_absolute_url_is_rejected() -> None:
    skipped = {s.row_id: s for s in _skipped(_parse_fixture())}
    assert "host does not match" in skipped["5006"].reason


def test_http_absolute_url_is_rejected_as_protocol_downgrade() -> None:
    skipped = {s.row_id: s for s in _skipped(_parse_fixture())}
    assert "must use https" in skipped["5007"].reason


def _parse_inline(tmp_path: Path, payload: str) -> list[LinkRecord | SkippedRow]:
    topics_path = tmp_path / "topics.json"
    topics_path.write_text(payload)
    return list(parse_topics(topics_path, site_name=SITE_NAME, site_url=SITE_URL))


def test_non_object_row_becomes_skipped_row_not_crash(tmp_path: Path) -> None:
    rows = _parse_inline(
        tmp_path,
        """
        [
          "not an object",
          {
            "id": "1", "stream": "general", "topic": "ok",
            "sender_full_name": "A", "timestamp": 1704067200,
            "url": "https://chat.fhir.org/#narrow/stream/1-general/topic/ok"
          }
        ]
        """,
    )
    assert len(_records(rows)) == 1
    skipped = _skipped(rows)
    assert len(skipped) == 1
    assert "not a JSON object" in skipped[0].reason


def test_top_level_non_array_raises_valueerror(tmp_path: Path) -> None:
    topics_path = tmp_path / "topics.json"
    topics_path.write_text('{"id": 1}')
    with pytest.raises(ValueError, match="top-level JSON array"):
        list(parse_topics(topics_path, site_name=SITE_NAME, site_url=SITE_URL))


def test_missing_stream_yields_no_tags(tmp_path: Path) -> None:
    rows = _parse_inline(
        tmp_path,
        """
        [
          {
            "id": "1", "topic": "no stream field",
            "sender_full_name": "A", "timestamp": 1704067200,
            "url": "https://chat.fhir.org/#narrow/stream/1-general/topic/x"
          }
        ]
        """,
    )
    records = _records(rows)
    assert len(records) == 1
    assert records[0].tags == ()
