import json
import os
import time
import urllib.request

import boto3
import pytest

FUNCTION = os.environ.get("WEBHEALTH_FUNCTION_NAME")
API = os.environ.get("API_URL", "").rstrip("/")

pytestmark = pytest.mark.skipif(
    not (FUNCTION and API),
    reason="WEBHEALTH_FUNCTION_NAME and API_URL must be set",
)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

SITES = [
    "https://www.westernsydney.edu.au/",
    "https://www.google.com/",
    "https://www.amazon.com/",
]


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode() or "{}")


@pytest.fixture
def seeded_sites():
    ids = [api("POST", "/websites", {"url": u})["website_id"] for u in SITES]
    yield SITES
    for i in ids:
        api("DELETE", f"/websites/{i}")


def invoke():
    response = boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=FUNCTION
    )
    assert response["StatusCode"] == 200
    assert "FunctionError" not in response
    return json.loads(response["Payload"].read())


def test_deployed_lambda_checks_all_sites(seeded_sites):
    payload = invoke()
    assert payload["statusCode"] == 200
    checked = {r["website"] for r in payload["results"]}
    assert set(seeded_sites) <= checked


def test_metrics_reach_cloudwatch(seeded_sites):
    invoke()
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    for _ in range(12):
        metrics = cloudwatch.list_metrics(
            Namespace="WebHealth",
            MetricName="Availability",
            Dimensions=[{"Name": "Website", "Value": "https://www.google.com/"}],
        )["Metrics"]
        if metrics:
            return
        time.sleep(15)
    pytest.fail("Availability metric not found in CloudWatch")
