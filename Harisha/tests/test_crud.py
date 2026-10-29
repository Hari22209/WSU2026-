import json
from unittest.mock import patch, MagicMock

import boto3
import pytest
from moto import mock_aws

import crud_lambda


def event(method, body=None, website_id=None):
    return {
        "httpMethod": method,
        "pathParameters": {"website_id": website_id} if website_id else None,
        "body": json.dumps(body) if body is not None else None,
    }


#  UNIT tests (mock: test only my Python logic)

def test_create_website_returns_201_and_saves_item():
    fake = MagicMock()
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(
            event("POST", {"url": "https://example.com"}), None)
    assert resp["statusCode"] == 201
    saved = fake.put_item.call_args.kwargs["Item"]
    assert saved["url"] == "https://example.com"
    assert saved["website_id"]


def test_create_website_without_url_returns_400():
    fake = MagicMock()
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(event("POST", {}), None)
    assert resp["statusCode"] == 400
    fake.put_item.assert_not_called()


def test_create_website_returns_dynamodb_write_time_header():
    fake = MagicMock()
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(
            event("POST", {"url": "https://example.com"}), None)
    assert resp["statusCode"] == 201
    assert "X-DynamoDB-Write-Time-Ms" in resp["headers"]
    assert float(resp["headers"]["X-DynamoDB-Write-Time-Ms"]) >= 0


def test_get_website_returns_dynamodb_read_time_header():
    fake = MagicMock()
    fake.get_item.return_value = {
        "Item": {"website_id": "test-123", "url": "https://example.com"}
    }
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(
            event("GET", website_id="test-123"), None)
    assert resp["statusCode"] == 200
    assert "X-DynamoDB-Read-Time-Ms" in resp["headers"]
    assert float(resp["headers"]["X-DynamoDB-Read-Time-Ms"]) >= 0


#  FUNCTIONAL test (moto = behaves like real DynamoDB) 

@pytest.fixture
def dynamodb_table(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        table = boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="test-table",
            KeySchema=[{"AttributeName": "website_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "website_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        monkeypatch.setattr(crud_lambda, "table", table)
        yield table


def test_crud_lifecycle_with_dynamodb(dynamodb_table):
    h = crud_lambda.lambda_handler

    # CREATE -> really stored in the table
    created = h(event("POST", {"url": "https://a.com"}), None)
    assert created["statusCode"] == 201
    wid = json.loads(created["body"])["website_id"]
    assert dynamodb_table.get_item(Key={"website_id": wid})["Item"]["url"] == "https://a.com"

    # READ one and READ all
    got = h(event("GET", website_id=wid), None)
    assert got["statusCode"] == 200
    assert json.loads(got["body"])["url"] == "https://a.com"
    listing = json.loads(h(event("GET"), None)["body"])
    assert len(listing["websites"]) == 1

    # UPDATE -> table has the new url
    updated = h(event("PUT", {"url": "https://b.com"}, website_id=wid), None)
    assert updated["statusCode"] == 200
    assert dynamodb_table.get_item(Key={"website_id": wid})["Item"]["url"] == "https://b.com"

    # DELETE -> gone from the table
    assert h(event("DELETE", website_id=wid), None)["statusCode"] == 200
    assert "Item" not in dynamodb_table.get_item(Key={"website_id": wid})
    assert h(event("GET", website_id=wid), None)["statusCode"] == 404

    # website that does not exist -> 404
    assert h(event("PUT", {"url": "https://c.com"}, website_id="nope"), None)["statusCode"] == 404
    assert h(event("DELETE", website_id="nope"), None)["statusCode"] == 404