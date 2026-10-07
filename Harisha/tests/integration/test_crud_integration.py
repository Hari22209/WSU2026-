import json
import os
import time
import urllib.error
import urllib.request
import uuid

import pytest

API = os.environ.get("API_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not API, reason="API_URL not set")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status, text = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    return status, json.loads(text or "{}"), time.time() - start


def test_api_create_read_delete_and_dynamodb_latency():
    wid = "it-" + uuid.uuid4().hex[:8]
    try:
        status, _, write_time = call("POST", "/websites",
                                     {"website_id": wid, "url": "https://example.com"})
        assert status == 201
        status, item, read_time = call("GET", f"/websites/{wid}")
        assert status == 200 and item["url"] == "https://example.com"
        assert write_time < 3 and read_time < 3   # DynamoDB read/write round trip
    finally:
        call("DELETE", f"/websites/{wid}")
    assert call("GET", f"/websites/{wid}")[0] == 404
