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
"""

from __future__ import annotations

import httpx

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
