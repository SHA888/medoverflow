"""Thin HTTP client for the Biostars forum API (biostars.org).

Biostars exposes no bulk post-listing endpoint; discovery goes through
`GET /api/tag/{tag}/`, which returns the post uids for a tag, and each post's
full record is then fetched individually via `GET /api/post/{uid}/`
(`docs.biostars.org` forum API, `biostar/forum/api.py` upstream). An
`httpx.Client` is passed in rather than constructed here so tests can inject
an `httpx.MockTransport` instead of making real network calls.

Callers construct their `httpx.Client` with `base_url=DEFAULT_BASE_URL` (or a
staging/mirror host); requests below use paths relative to that base rather
than re-threading a separate `base_url` argument, so the client's configured
host is always the one actually used.

`fetch_posts_to_json` is the "fetches" half of task 3.1.2's "fetches/parses"
adapter: it pulls posts live and writes them in the JSON-array shape
`biostars.parser.parse_posts` reads, so the two modules compose into one
live-fetch-and-parse pipeline while `parse_posts` itself stays file-based
(consistent with the Stack Exchange dump parser it mirrors).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from ..models import SkippedRow

DEFAULT_BASE_URL = "https://www.biostars.org"


class BiostarsApiError(RuntimeError):
    """Raised when the Biostars API has no data for a requested tag or post."""


def fetch_post_uids_for_tag(client: httpx.Client, tag: str) -> list[str]:
    """Return the post uids tagged with `tag`, per `GET /api/tag/{tag}/`."""
    response = client.get(f"/api/tag/{tag}/")
    response.raise_for_status()
    uids = response.json()
    return [str(uid) for uid in uids]


def fetch_post(client: httpx.Client, uid: str) -> dict[str, object]:
    """Return the raw JSON payload for one post, per `GET /api/post/{uid}/`.

    `post_details` (upstream `biostar/forum/api.py`) returns an empty object
    for an unknown uid rather than a 404 status; that shape is treated as a
    fetch failure here rather than propagated as a valid-but-empty payload.
    """
    response = client.get(f"/api/post/{uid}/")
    response.raise_for_status()
    payload = response.json()
    if not payload:
        raise BiostarsApiError(f"no post found for uid {uid!r}")
    return payload


def fetch_posts(
    client: httpx.Client, uids: Iterable[str], *, max_workers: int = 8
) -> tuple[list[dict[str, object]], list[SkippedRow]]:
    """Fetch each uid's post payload concurrently.

    Each uid is one independent blocking HTTP round trip (Biostars has no
    bulk post-fetch endpoint), so fetches run across up to `max_workers`
    threads; `httpx.Client` is documented safe for concurrent use across
    threads. A uid that fails to fetch (network error, or no post for that
    uid) becomes a `SkippedRow` rather than aborting the batch, mirroring
    `biostars.parser.parse_posts`'s own no-silent-drop contract.
    """
    uid_list = list(uids)
    payloads: list[dict[str, object]] = []
    skipped: list[SkippedRow] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fetched = executor.map(lambda uid: _fetch(client, uid), uid_list)
        for uid, result in zip(uid_list, fetched, strict=True):
            if isinstance(result, Exception):
                skipped.append(SkippedRow(row_id=uid, reason=str(result)))
            else:
                payloads.append(result)
    return payloads, skipped


def fetch_posts_to_json(
    client: httpx.Client,
    uids: Iterable[str],
    destination: Path,
    *,
    max_workers: int = 8,
) -> list[SkippedRow]:
    """Fetch each uid's post concurrently and write the payloads as a JSON
    array to `destination`, in the shape `biostars.parser.parse_posts` reads.

    Returns a `SkippedRow` for each uid that failed to fetch; `destination`
    only ever contains successfully-fetched payloads, so a caller who
    discards the returned list still gets a file `parse_posts` can read.
    """
    payloads, skipped = fetch_posts(client, uids, max_workers=max_workers)
    destination.write_text(json.dumps(payloads), encoding="utf-8")
    return skipped


def _fetch(client: httpx.Client, uid: str) -> dict[str, object] | Exception:
    """Fetch one post, returning the exception instead of raising it.

    Keeps fetch failures as data so `ThreadPoolExecutor.map` (which
    propagates a worker exception from the *caller's* `next()` call) doesn't
    abort the whole batch on the first network/API error.
    """
    try:
        return fetch_post(client, uid)
    except (BiostarsApiError, httpx.HTTPError) as exc:
        return exc
