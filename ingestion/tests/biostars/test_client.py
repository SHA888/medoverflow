"""Tests for the Biostars forum API client (task 3.1.2)."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import httpx
import pytest

from medoverflow_ingestion.biostars.client import (
    BiostarsApiError,
    fetch_post,
    fetch_post_uids_for_tag,
    fetch_posts,
    fetch_posts_to_json,
)

BASE_URL = "https://www.biostars.org"


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, base_url=BASE_URL)


def test_fetch_post_uids_for_tag_returns_uid_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tag/clinical-informatics/"
        return httpx.Response(200, json=["9a1b", "9a1c"])

    with _client(httpx.MockTransport(handler)) as client:
        uids = fetch_post_uids_for_tag(client, "clinical-informatics")

    assert uids == ["9a1b", "9a1c"]


def test_fetch_post_uids_for_tag_empty_when_no_matches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    with _client(httpx.MockTransport(handler)) as client:
        uids = fetch_post_uids_for_tag(client, "no-such-tag")

    assert uids == []


def test_fetch_post_returns_payload_for_known_uid() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/post/9a1b/"
        return httpx.Response(200, json={"id": 25, "uid": "9a1b", "type": "Question"})

    with _client(httpx.MockTransport(handler)) as client:
        payload = fetch_post(client, "9a1b")

    assert payload["id"] == 25


def test_fetch_post_raises_on_empty_payload_for_unknown_uid() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with (
        _client(httpx.MockTransport(handler)) as client,
        pytest.raises(BiostarsApiError),
    ):
        fetch_post(client, "no-such-uid")


def test_fetch_post_raises_on_http_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with (
        _client(httpx.MockTransport(handler)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        fetch_post(client, "9a1b")


def test_requests_go_to_the_clients_own_base_url_not_a_hardcoded_default() -> None:
    """Regression: a mirror/staging client's base_url must actually be used.

    `fetch_post`/`fetch_post_uids_for_tag` used to rebuild the request URL
    from a separately-threaded `base_url` kwarg, leaving `httpx.Client`'s own
    `base_url` dead — a client pointed at a non-default host without also
    passing a matching kwarg would silently hit `DEFAULT_BASE_URL` instead.
    There is no `base_url` kwarg to (mis)pass now; the client's own
    `base_url` is the only source of truth.
    """
    seen_hosts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_hosts.append(request.url.host)
        return httpx.Response(200, json={"id": 1, "uid": "u1", "type": "Question"})

    mirror_url = "https://mirror.example.org"
    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url=mirror_url
    ) as client:
        fetch_post(client, "u1")
        fetch_post_uids_for_tag(client, "some-tag")

    assert seen_hosts == ["mirror.example.org", "mirror.example.org"]


def test_fetch_posts_returns_payloads_and_skips_failures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        uid = request.url.path.rsplit("/", 2)[-2]
        if uid == "missing":
            return httpx.Response(200, json={})
        return httpx.Response(200, json={"id": uid, "uid": uid, "type": "Question"})

    with _client(httpx.MockTransport(handler)) as client:
        payloads, skipped = fetch_posts(client, ["u1", "missing", "u2"])

    assert {p["id"] for p in payloads} == {"u1", "u2"}
    assert [s.row_id for s in skipped] == ["missing"]


def test_fetch_posts_is_concurrent_not_sequential() -> None:
    """Regression: fetches must overlap, not run one-at-a-time.

    Each handler invocation records how many other invocations are in
    flight at the same moment; a purely sequential fetch loop would never
    see more than one in flight at once.
    """
    lock = threading.Lock()
    in_flight = 0
    max_in_flight = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, max_in_flight
        with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        time.sleep(0.05)
        with lock:
            in_flight -= 1
        return httpx.Response(200, json={"id": 1, "uid": "u", "type": "Question"})

    uids = [f"uid-{i}" for i in range(6)]
    with _client(httpx.MockTransport(handler)) as client:
        payloads, skipped = fetch_posts(client, uids, max_workers=6)

    assert len(payloads) == 6
    assert skipped == []
    assert max_in_flight >= 2


def test_fetch_posts_to_json_writes_only_successful_payloads(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        uid = request.url.path.rsplit("/", 2)[-2]
        if uid == "missing":
            return httpx.Response(200, json={})
        return httpx.Response(200, json={"id": uid, "uid": uid, "type": "Question"})

    destination = tmp_path / "posts.json"
    with _client(httpx.MockTransport(handler)) as client:
        skipped = fetch_posts_to_json(client, ["u1", "missing", "u2"], destination)

    written = json.loads(destination.read_text())
    assert {p["id"] for p in written} == {"u1", "u2"}
    assert [s.row_id for s in skipped] == ["missing"]
