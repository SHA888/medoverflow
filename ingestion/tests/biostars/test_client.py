"""Tests for the Biostars forum API client (task 3.1.2)."""

from __future__ import annotations

import httpx
import pytest

from medoverflow_ingestion.biostars.client import (
    BiostarsApiError,
    fetch_post,
    fetch_post_uids_for_tag,
)

BASE_URL = "https://www.biostars.org"


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, base_url=BASE_URL)


def test_fetch_post_uids_for_tag_returns_uid_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tag/clinical-informatics/"
        return httpx.Response(200, json=["9a1b", "9a1c"])

    with _client(httpx.MockTransport(handler)) as client:
        uids = fetch_post_uids_for_tag(
            client, "clinical-informatics", base_url=BASE_URL
        )

    assert uids == ["9a1b", "9a1c"]


def test_fetch_post_uids_for_tag_empty_when_no_matches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    with _client(httpx.MockTransport(handler)) as client:
        uids = fetch_post_uids_for_tag(client, "no-such-tag", base_url=BASE_URL)

    assert uids == []


def test_fetch_post_returns_payload_for_known_uid() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/post/9a1b/"
        return httpx.Response(200, json={"id": 25, "uid": "9a1b", "type": "Question"})

    with _client(httpx.MockTransport(handler)) as client:
        payload = fetch_post(client, "9a1b", base_url=BASE_URL)

    assert payload["id"] == 25


def test_fetch_post_raises_on_empty_payload_for_unknown_uid() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with (
        _client(httpx.MockTransport(handler)) as client,
        pytest.raises(BiostarsApiError),
    ):
        fetch_post(client, "no-such-uid", base_url=BASE_URL)


def test_fetch_post_raises_on_http_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with (
        _client(httpx.MockTransport(handler)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        fetch_post(client, "9a1b", base_url=BASE_URL)
