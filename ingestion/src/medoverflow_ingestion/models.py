"""Shared parsed-record shapes for source-specific import adapters.

Parse-Don't-Validate boundary: a `ParsedRecord` cannot be constructed without
a complete, non-empty `Attribution` (source, author, license, date, link) per
`docs/ATTRIBUTION-RENDERING.md`'s non-strippability contract, and a
question/answer cannot be constructed with the other kind's shape (e.g. an
answer carrying a title). Rows that fail these checks are never coerced or
defaulted into a record; the parser turns them into a `SkippedRow` instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, HttpUrl, model_validator

from .license import License


def _non_empty(v: str) -> str:
    if not v.strip():
        raise ValueError("field must not be empty")
    return v


NonEmptyStr = Annotated[str, AfterValidator(_non_empty)]


@dataclass(frozen=True)
class SkippedRow:
    """A source row/payload that could not be parsed into a `ParsedRecord`.

    Kept as explicit data — never raised past the caller and never silently
    dropped — so a full ingestion run can report every unparsed row instead
    of aborting on the first bad one.
    """

    row_id: str
    reason: str


class Attribution(BaseModel):
    """The five non-strippable fields required to render mirrored content."""

    source: NonEmptyStr
    author: NonEmptyStr
    license: License
    date: datetime
    link: HttpUrl


class ParsedRecord(BaseModel):
    """A single imported question or answer, attributed to its source."""

    record_id: NonEmptyStr
    kind: Literal["question", "answer"]
    title: str | None = None
    body_html: NonEmptyStr
    tags: tuple[str, ...] = ()
    parent_id: str | None = None
    attribution: Attribution

    @model_validator(mode="after")
    def _check_kind_shape(self) -> "ParsedRecord":
        if self.kind == "question":
            if not self.title or not self.title.strip():
                raise ValueError("a question record must have a non-empty title")
            if self.parent_id is not None:
                raise ValueError("a question record must not have a parent_id")
        else:
            if self.title is not None:
                raise ValueError("an answer record must not have a title")
            if not self.parent_id or not self.parent_id.strip():
                raise ValueError(
                    "an answer record must have a parent_id (its question's id)"
                )
        return self


class LinkRecord(BaseModel):
    """A link-only reference to external content that is never copied.

    Unlike `ParsedRecord`, this has no body field at all: for a
    `License.LINK_ONLY` source (task 3.1.3's FHIR Zulip adapter), "the body
    is never copied" is a structural guarantee — there is no field a body
    could be assigned to — rather than a runtime check that a future edit
    could accidentally bypass. `extra="forbid"` makes that guarantee hold
    against a caller too: without it, pydantic's default behavior would
    silently drop an accidental `body_html=...` kwarg instead of rejecting
    it, masking exactly the mistake this model exists to make impossible.
    """

    model_config = ConfigDict(extra="forbid")

    record_id: NonEmptyStr
    title: NonEmptyStr
    tags: tuple[str, ...] = ()
    attribution: Attribution

    @model_validator(mode="after")
    def _check_link_only_license(self) -> "LinkRecord":
        if self.attribution.license != License.LINK_ONLY:
            raise ValueError(
                "a LinkRecord must carry License.LINK_ONLY attribution, got "
                f"{self.attribution.license!r}"
            )
        return self
