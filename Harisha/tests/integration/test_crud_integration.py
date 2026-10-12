import json
import os
import time
import urllib.error
import urllib.request

import pytest

API = os.environ.get("API_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not API, reason="API_URL not set")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
            text = r.read().decode()
            headers = dict(r.headers.items())
    except urllib.error.HTTPError as e:
        status = e.code
        text = e.read().decode()
        headers = dict(e.headers.items())

    elapsed = time.perf_counter() - start
    return status, json.loads(text or "{}"), elapsed, headers


def test_api_crud_cycle_and_dynamodb_latency():
    status, item, _, write_headers = call(
        "POST", "/websites", {"url": "https://example.com"}
    )
    assert status == 201
    wid = item["website_id"]

    try:
        assert "X-DynamoDB-Write-Time-Ms" in write_headers
        assert float(write_headers["X-DynamoDB-Write-Time-Ms"]) >= 0

        status, got, _, read_headers = call("GET", f"/websites/{wid}")
        assert status == 200
        assert got["url"] == "https://example.com"
        assert "X-DynamoDB-Read-Time-Ms" in read_headers
        assert float(read_headers["X-DynamoDB-Read-Time-Ms"]) >= 0

        status, updated, _, _ = call(
            "PUT", f"/websites/{wid}", {"url": "https://example.org"}
        )
        assert status == 200
        assert updated["url"] == "https://example.org"

    finally:
        call("DELETE", f"/websites/{wid}")

    status, _, _, _ = call("GET", f"/websites/{wid}")
    assert status == 404


def test_create_website_without_url_returns_400():
    status, body, _, _ = call("POST", "/websites", {})
    assert status == 400
    assert body["error"] == "url is required"


def test_read_missing_website_returns_404():
    status, body, _, _ = call(
        "GET", "/websites/website-that-does-not-exist-12345"
    )
    assert status == 404
    assert body["error"] == "Website not found"
