"""Tests for the Stack Exchange dump parser (task 3.1.1)."""

from pathlib import Path

import pytest

from medoverflow_ingestion.license import License
from medoverflow_ingestion.models import ParsedRecord
from medoverflow_ingestion.stack_exchange import SkippedRow, parse_posts
from medoverflow_ingestion.stack_exchange.parser import _iter_rows

FIXTURES = Path(__file__).parent / "fixtures"
SITE_NAME = "Health Informatics Stack Exchange"
SITE_URL = "https://healthinformatics.stackexchange.com"


def _parse_fixture() -> list[ParsedRecord | SkippedRow]:
    return list(
        parse_posts(
            FIXTURES / "Posts.xml",
            FIXTURES / "Users.xml",
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
    question = next(r for r in records if r.record_id == "1")

    assert question.kind == "question"
    assert question.title == "How do I validate an HL7 v2 message?"
    assert question.attribution.source == SITE_NAME
    assert question.attribution.author == "Jane Doe"
    assert question.attribution.license == License.CC_BY_SA_4
    assert str(question.attribution.link) == f"{SITE_URL}/questions/1"
    assert question.attribution.date.isoformat().startswith("2016-01-05")

    answer = next(r for r in records if r.record_id == "2")
    assert answer.kind == "answer"
    assert answer.title is None
    assert answer.parent_id == "1"
    assert answer.attribution.author == "John Smith"
    assert answer.attribution.license == License.CC_BY_SA_4
    assert str(answer.attribution.link) == f"{SITE_URL}/a/2"


def test_author_resolves_via_owner_display_name_for_deleted_users() -> None:
    records = _records(_parse_fixture())
    row = next(r for r in records if r.record_id == "3")
    assert row.attribution.author == "anon-user"


def test_legacy_and_modern_tag_encodings_both_parse() -> None:
    records = _records(_parse_fixture())
    legacy = next(r for r in records if r.record_id == "1")
    modern = next(r for r in records if r.record_id == "3")

    assert legacy.tags == ("hl7", "interoperability")
    assert modern.tags == ("fhir", "encounter")


def test_answers_carry_no_tags() -> None:
    records = _records(_parse_fixture())
    answer = next(r for r in records if r.record_id == "2")
    assert answer.tags == ()


@pytest.mark.parametrize(
    ("row_id", "reason_fragment"),
    [
        ("4", "unsupported PostTypeId"),
        ("5", "no Body"),
        ("6", "no attributable author"),
    ],
)
def test_unparseable_rows_become_skipped_rows_not_silent_drops(
    row_id: str, reason_fragment: str
) -> None:
    skipped = {s.row_id: s for s in _skipped(_parse_fixture())}
    assert row_id in skipped
    assert reason_fragment in skipped[row_id].reason


def test_every_emitted_record_carries_cc_by_sa_4_and_full_attribution() -> None:
    for record in _records(_parse_fixture()):
        assert record.attribution.license == License.CC_BY_SA_4
        assert record.attribution.source
        assert record.attribution.author
        assert record.attribution.date is not None
        assert record.attribution.link is not None


def test_total_row_count_accounts_for_every_row() -> None:
    rows = _parse_fixture()
    assert len(rows) == 6
    assert len(_records(rows)) == 3
    assert len(_skipped(rows)) == 3


def test_iter_rows_keeps_document_root_bounded_across_many_rows(
    tmp_path: Path,
) -> None:
    """Regression test: `elem.clear()` alone empties a row but leaves it
    attached to the document root, so the root's child list — and memory
    use — would grow linearly with the file instead of staying bounded.
    `_iter_rows` must clear the root itself once each row is consumed.
    """
    row_count = 500
    rows_xml = "".join(
        f'<row Id="{i}" PostTypeId="1" CreationDate="2020-01-01T00:00:00.000" '
        f'Body="&lt;p&gt;body {i}&lt;/p&gt;" OwnerUserId="1" Title="q{i}" />'
        for i in range(row_count)
    )
    xml_path = tmp_path / "Posts.xml"
    xml_path.write_text(f"<posts>{rows_xml}</posts>")

    gen = _iter_rows(xml_path)
    first = next(gen)
    root = gen.gi_frame.f_locals["root"]  # type: ignore[attr-defined]
    assert first.get("Id") == "0"

    for _ in gen:
        pass

    # An unfixed implementation would leave all `row_count` rows attached.
    assert len(list(root)) < 10
