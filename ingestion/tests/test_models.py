"""Parse-Don't-Validate invariant tests for the shared record/attribution models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from medoverflow_ingestion.license import License
from medoverflow_ingestion.models import Attribution, LinkRecord, ParsedRecord


def _attribution(**overrides: object) -> Attribution:
    defaults: dict[str, object] = {
        "source": "Stack Exchange",
        "author": "Jane Doe",
        "license": License.CC_BY_SA_4,
        "date": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "link": "https://example.stackexchange.com/questions/1",
    }
    defaults.update(overrides)
    return Attribution.model_validate(defaults)


def test_attribution_rejects_empty_author() -> None:
    with pytest.raises(ValidationError):
        _attribution(author="")


def test_attribution_rejects_empty_source() -> None:
    with pytest.raises(ValidationError):
        _attribution(source="   ")


def test_attribution_rejects_unknown_license() -> None:
    with pytest.raises(ValidationError):
        Attribution.model_validate(
            {
                "source": "Stack Exchange",
                "author": "Jane Doe",
                "license": "wtfpl",
                "date": datetime(2020, 1, 1, tzinfo=timezone.utc),
                "link": "https://example.stackexchange.com/questions/1",
            }
        )


def test_question_record_requires_title_and_forbids_parent_id() -> None:
    with pytest.raises(ValidationError):
        ParsedRecord(
            record_id="1",
            kind="question",
            title=None,
            body_html="<p>body</p>",
            attribution=_attribution(),
        )

    with pytest.raises(ValidationError):
        ParsedRecord(
            record_id="1",
            kind="question",
            title="A title",
            body_html="<p>body</p>",
            parent_id="99",
            attribution=_attribution(),
        )


def test_answer_record_requires_parent_id_and_forbids_title() -> None:
    with pytest.raises(ValidationError):
        ParsedRecord(
            record_id="2",
            kind="answer",
            title=None,
            body_html="<p>body</p>",
            parent_id=None,
            attribution=_attribution(),
        )

    with pytest.raises(ValidationError):
        ParsedRecord(
            record_id="2",
            kind="answer",
            title="Should not have one",
            body_html="<p>body</p>",
            parent_id="1",
            attribution=_attribution(),
        )


def test_well_formed_question_and_answer_construct_cleanly() -> None:
    question = ParsedRecord(
        record_id="1",
        kind="question",
        title="A title",
        body_html="<p>body</p>",
        attribution=_attribution(),
    )
    assert question.parent_id is None

    answer = ParsedRecord(
        record_id="2",
        kind="answer",
        body_html="<p>body</p>",
        parent_id="1",
        attribution=_attribution(),
    )
    assert answer.title is None


def _link_attribution(**overrides: object) -> Attribution:
    return _attribution(
        source="FHIR Zulip",
        license=License.LINK_ONLY,
        link="https://chat.fhir.org/#narrow/stream/1-general/topic/hi",
        **overrides,
    )


def test_link_record_has_no_body_field() -> None:
    # "no body copied" (task 3.1.3's DoD) is asserted structurally: there is
    # no field a body could ever be assigned to, not a runtime check.
    assert not any("body" in name for name in LinkRecord.model_fields)


def test_link_record_rejects_non_link_only_license() -> None:
    with pytest.raises(ValidationError):
        LinkRecord(
            record_id="1",
            title="A topic",
            attribution=_attribution(),  # defaults to CC_BY_SA_4
        )


def test_link_record_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        LinkRecord(record_id="1", title="  ", attribution=_link_attribution())


def test_link_record_rejects_extra_body_field() -> None:
    # Guards the structural "no body copied" guarantee against a caller
    # mistake: pydantic's default extra-field handling would otherwise
    # silently drop an accidental body_html= kwarg instead of rejecting it.
    with pytest.raises(ValidationError):
        LinkRecord(
            record_id="1",
            title="A topic",
            attribution=_link_attribution(),
            body_html="<p>should never be accepted</p>",  # type: ignore[call-arg]
        )


def test_well_formed_link_record_constructs_cleanly() -> None:
    record = LinkRecord(
        record_id="1",
        title="A topic",
        tags=("general",),
        attribution=_link_attribution(),
    )
    assert record.attribution.license == License.LINK_ONLY
    assert record.tags == ("general",)
