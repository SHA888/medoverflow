"""Parse-Don't-Validate invariant tests for the shared record/attribution models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from medoverflow_ingestion.license import License
from medoverflow_ingestion.models import Attribution, ParsedRecord


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
