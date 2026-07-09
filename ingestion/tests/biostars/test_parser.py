"""Tests for the Biostars import adapter (task 3.1.2)."""

from pathlib import Path

import pytest

from medoverflow_ingestion.biostars import SkippedRow, parse_posts
from medoverflow_ingestion.license import License
from medoverflow_ingestion.models import ParsedRecord

FIXTURES = Path(__file__).parent / "fixtures"
SITE_NAME = "Biostars"
SITE_URL = "https://www.biostars.org"


def _parse_fixture() -> list[ParsedRecord | SkippedRow]:
    return list(
        parse_posts(
            FIXTURES / "posts.json",
            site_name=SITE_NAME,
            site_url=SITE_URL,
        )
    )


def _records(rows: list[ParsedRecord | SkippedRow]) -> list[ParsedRecord]:
    return [r for r in rows if isinstance(r, ParsedRecord)]


def _skipped(rows: list[ParsedRecord | SkippedRow]) -> list[SkippedRow]:
    return [r for r in rows if isinstance(r, SkippedRow)]


def test_parses_question_and_answer_with_full_attribution() -> None:
    records = _records(_parse_fixture())

    question = next(r for r in records if r.record_id == "100")
    assert question.kind == "question"
    assert question.title == "How do I validate an HL7 v2 message?"
    assert question.tags == ("hl7", "interoperability")
    assert question.attribution.source == SITE_NAME
    assert question.attribution.author == "Jane Doe"
    assert question.attribution.license == License.CC_BY_4
    assert str(question.attribution.link) == f"{SITE_URL}/p/100/"
    assert question.attribution.date.isoformat() == "2016-01-05T14:16:20.240000+00:00"

    answer = next(r for r in records if r.record_id == "101")
    assert answer.kind == "answer"
    assert answer.title is None
    assert answer.parent_id == "100"
    assert answer.attribution.author == "John Smith"
    assert answer.attribution.license == License.CC_BY_4


def test_answer_title_prefix_is_dropped_not_passed_through() -> None:
    # The real Biostars API returns "A: <question title>" as an answer's raw
    # title; ParsedRecord forbids a title on an answer, so the parser must
    # discard it rather than passing the raw field through.
    records = _records(_parse_fixture())
    answer = next(r for r in records if r.record_id == "101")
    assert answer.title is None


def test_answer_parent_id_uses_root_id_not_immediate_parent_id() -> None:
    # root_id always resolves to the top-level question even for replies
    # nested under a comment; parent_id would not for such rows.
    records = _records(_parse_fixture())
    answer = next(r for r in records if r.record_id == "101")
    assert answer.parent_id == "100"


@pytest.mark.parametrize(
    ("row_id", "reason_fragment"),
    [
        ("103", "unsupported post type"),
        ("104", "no xhtml body"),
        ("105", "no attributable author"),
    ],
)
def test_unparseable_rows_become_skipped_rows_not_silent_drops(
    row_id: str, reason_fragment: str
) -> None:
    skipped = {s.row_id: s for s in _skipped(_parse_fixture())}
    assert row_id in skipped
    assert reason_fragment in skipped[row_id].reason


def test_every_emitted_record_carries_cc_by_4_and_full_attribution() -> None:
    for record in _records(_parse_fixture()):
        assert record.attribution.license == License.CC_BY_4
        assert record.attribution.source
        assert record.attribution.author
        assert record.attribution.date is not None
        assert record.attribution.link is not None


def test_total_row_count_accounts_for_every_row() -> None:
    rows = _parse_fixture()
    assert len(rows) == 6
    assert len(_records(rows)) == 3
    assert len(_skipped(rows)) == 3


def test_question_tags_are_split_and_stripped() -> None:
    # Record 102's tag_val is "fhir, encounter" (space after the comma), so
    # this proves the per-tag .strip() in _parse_tags is exercised.
    records = _records(_parse_fixture())
    question = next(r for r in records if r.record_id == "102")
    assert question.tags == ("fhir", "encounter")


def _parse_inline(tmp_path: Path, payload: str) -> list[ParsedRecord | SkippedRow]:
    posts_path = tmp_path / "posts.json"
    posts_path.write_text(payload)
    return list(parse_posts(posts_path, site_name=SITE_NAME, site_url=SITE_URL))


def test_non_object_row_becomes_skipped_row_not_crash(tmp_path: Path) -> None:
    # A single malformed (non-object) element must not abort the whole run.
    rows = _parse_inline(
        tmp_path,
        """
        [
          "not an object",
          {
            "id": 300, "title": "ok", "type": "Question", "author": "A",
            "creation_date": "2020-01-01T00:00:00+00:00", "xhtml": "<p>b</p>",
            "tag_val": "", "root_id": 300, "url": "/p/300/"
          }
        ]
        """,
    )
    assert len(_records(rows)) == 1
    skipped = _skipped(rows)
    assert len(skipped) == 1
    assert "not a JSON object" in skipped[0].reason


def test_top_level_non_array_raises_valueerror(tmp_path: Path) -> None:
    posts_path = tmp_path / "posts.json"
    posts_path.write_text('{"id": 1}')
    with pytest.raises(ValueError, match="top-level JSON array"):
        list(parse_posts(posts_path, site_name=SITE_NAME, site_url=SITE_URL))


def test_wrong_typed_fields_become_skipped_rows_not_crash(tmp_path: Path) -> None:
    # Non-string creation_date / tag_val (valid JSON, wrong types) must be
    # reported as SkippedRow rather than raising TypeError/AttributeError.
    rows = _parse_inline(
        tmp_path,
        """
        [
          {
            "id": 301, "title": "bad date", "type": "Question", "author": "A",
            "creation_date": 12345, "xhtml": "<p>b</p>", "root_id": 301,
            "url": "/p/301/"
          }
        ]
        """,
    )
    assert _records(rows) == []
    assert "creation_date" in _skipped(rows)[0].reason


def test_offsite_absolute_url_is_rejected(tmp_path: Path) -> None:
    rows = _parse_inline(
        tmp_path,
        """
        [
          {
            "id": 302, "title": "spoofed", "type": "Question", "author": "A",
            "creation_date": "2020-01-01T00:00:00+00:00", "xhtml": "<p>b</p>",
            "tag_val": "", "root_id": 302, "url": "https://evil.example.com/p/302/"
          }
        ]
        """,
    )
    assert _records(rows) == []
    assert "host does not match" in _skipped(rows)[0].reason


def test_relative_url_is_joined_with_site_url(tmp_path: Path) -> None:
    posts_path = tmp_path / "posts.json"
    posts_path.write_text(
        """
        [
          {
            "id": 200,
            "title": "Relative URL question",
            "type": "Question",
            "author": "Jane Doe",
            "creation_date": "2020-01-01T00:00:00+00:00",
            "xhtml": "<p>body</p>",
            "tag_val": "",
            "root_id": 200,
            "url": "/p/200/"
          }
        ]
        """
    )
    records = _records(
        list(parse_posts(posts_path, site_name=SITE_NAME, site_url=SITE_URL))
    )
    assert str(records[0].attribution.link) == f"{SITE_URL}/p/200/"
