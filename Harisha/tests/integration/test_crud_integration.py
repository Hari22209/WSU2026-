import json
import os
import time
import urllib.error
import urllib.request

import boto3
import pytest

API = os.environ.get("API_URL", "").rstrip("/")
TABLE = os.environ.get("TARGET_TABLE_NAME")   # name of the REAL DynamoDB table
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
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


def real_table_item(website_id):
    """Read straight from the REAL DynamoDB table (not through the API)."""
    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)
    start = time.perf_counter()
    item = table.get_item(Key={"website_id": website_id}, ConsistentRead=True).get("Item")
    read_ms = (time.perf_counter() - start) * 1000
    return item, read_ms


def test_api_crud_cycle_and_dynamodb_latency():
    status, item, _, write_headers = call("POST", "/websites", {"url": "https://www.python.org/"})
    assert status == 201
    wid = item["website_id"]

    try:
        assert float(write_headers["X-DynamoDB-Write-Time-Ms"]) >= 0

        # prove the API really saved it in the REAL DynamoDB table
        if TABLE:
            saved, read_ms = real_table_item(wid)
            assert saved["url"] == "https://www.python.org/"
            assert read_ms < 1000

        status, got, _, read_headers = call("GET", f"/websites/{wid}")
        assert status == 200
        assert got["url"] == "https://www.python.org/"
        assert float(read_headers["X-DynamoDB-Read-Time-Ms"]) >= 0

        status, updated, _, _ = call("PUT", f"/websites/{wid}", {"url": "https://docs.python.org/"})
        assert status == 200
        assert updated["url"] == "https://docs.python.org/"

        if TABLE:
            assert real_table_item(wid)[0]["url"] == "https://docs.python.org/"
    finally:
        call("DELETE", f"/websites/{wid}")

    status, _, _, _ = call("GET", f"/websites/{wid}")
    assert status == 404
    if TABLE:
        assert real_table_item(wid)[0] is None


def test_create_website_without_url_returns_400():
    status, body, _, _ = call("POST", "/websites", {})
    assert status == 400
    assert body["error"] == "url is required"


def test_read_missing_website_returns_404():
    status, body, _, _ = call("GET", "/websites/website-that-does-not-exist-12345")
    assert status == 404
    assert body["error"] == "Website not found"