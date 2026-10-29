"""Smoke tests for the Alpha stage.

A smoke test is a quick check that the newly deployed stage is alive before
the slower integration tests run in Beta and Gamma.
"""
import json
import os
import urllib.request
from pathlib import Path

import pytest

API = os.environ.get("API_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not API, reason="API_URL not set")


def get(path):
    with urllib.request.urlopen(API + path, timeout=10) as response:
        return response.status, json.loads(response.read().decode() or "{}")


def test_api_is_reachable():
    status, body = get("/websites")
    assert status == 200
    assert "websites" in body


def test_target_list_was_seeded_into_dynamodb():
    targets_file = Path(__file__).resolve().parents[2] / "lambda" / "targets.json"
    target_websites = json.loads(targets_file.read_text())

    _, body = get("/websites")
    stored_urls = {item["url"] for item in body["websites"]}
    for site in target_websites:
        assert site["url"] in stored_urls
