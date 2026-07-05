"""Shared parsed-record shapes for source-specific dump parsers.

Parse-Don't-Validate boundary: a `ParsedRecord` cannot be constructed without
a complete, non-empty `Attribution` (source, author, license, date, link) per
`docs/ATTRIBUTION-RENDERING.md`'s non-strippability contract, and a
question/answer cannot be constructed with the other kind's shape (e.g. an
answer carrying a title). Rows that fail these checks are never coerced or
defaulted into a record; the parser turns them into a `SkippedRow` instead.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator, model_validator

from .license import License


class Attribution(BaseModel):
    """The five non-strippable fields required to render mirrored content."""

    source: str
    author: str
    license: License
    date: datetime
    link: HttpUrl

    @field_validator("source", "author")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("attribution field must not be empty")
        return v


class ParsedRecord(BaseModel):
    """A single imported question or answer, attributed to its source."""

    record_id: str
    kind: Literal["question", "answer"]
    title: str | None = None
    body_html: str
    tags: tuple[str, ...] = ()
    parent_id: str | None = None
    attribution: Attribution

    @field_validator("record_id", "body_html")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be empty")
        return v

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
