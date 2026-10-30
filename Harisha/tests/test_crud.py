"""Tests for the CRUD Lambda (lambda/crud_lambda.py).

UNIT tests use MagicMock in place of the DynamoDB table, so they check only
my Python logic (status codes, headers, which DynamoDB call is made).

FUNCTIONAL tests use moto, which behaves like the real DynamoDB API. They
create a real-shaped table and run the CRUD calls against it, before
anything is deployed. The real table is tested later by the integration
tests in tests/integration.
"""
import json
from unittest.mock import patch, MagicMock

import boto3
import pytest
from moto import mock_aws

import crud_lambda

WSU = "https://www.westernsydney.edu.au/"
PYTHON = "https://www.python.org/"
PYTHON_DOCS = "https://docs.python.org/"


def event(method, body=None, website_id=None):
    return {
        "httpMethod": method,
        "pathParameters": {"website_id": website_id} if website_id else None,
        "body": json.dumps(body) if body is not None else None,
    }


# UNIT tests (MagicMock: test only my Python logic)

def test_create_website_returns_201_and_saves_item():
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(event("POST", {"url": WSU}), None)
    assert resp["statusCode"] == 201
    saved = mock_table.put_item.call_args.kwargs["Item"]
    assert saved["url"] == WSU
    assert saved["website_id"]


def test_create_website_without_url_returns_400():
    mock_table = MagicMock()
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(event("POST", {}), None)
    assert resp["statusCode"] == 400
    mock_table.put_item.assert_not_called()


def test_create_website_returns_dynamodb_write_time_header():
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(event("POST", {"url": WSU}), None)
    assert resp["statusCode"] == 201
    assert "X-DynamoDB-Write-Time-Ms" in resp["headers"]
    assert float(resp["headers"]["X-DynamoDB-Write-Time-Ms"]) >= 0


def test_get_website_returns_dynamodb_read_time_header():
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {"website_id": "1", "url": WSU}}
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(event("GET", website_id="1"), None)
    assert resp["statusCode"] == 200
    assert "X-DynamoDB-Read-Time-Ms" in resp["headers"]
    assert float(resp["headers"]["X-DynamoDB-Read-Time-Ms"]) >= 0


def test_create_rejects_invalid_url():
    mock_table = MagicMock()
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(event("POST", {"url": "not a website"}), None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "Invalid website URL"
    mock_table.put_item.assert_not_called()


def test_update_rejects_invalid_url():
    mock_table = MagicMock()
    with patch.object(crud_lambda, "table", mock_table):
        resp = crud_lambda.lambda_handler(
            event("PUT", {"url": "westernsydney"}, website_id="1"), None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "Invalid website URL"
    mock_table.update_item.assert_not_called()


# FUNCTIONAL tests (moto: behaves like real DynamoDB)

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
    created = h(event("POST", {"url": PYTHON}), None)
    assert created["statusCode"] == 201
    assert float(created["headers"]["X-DynamoDB-Write-Time-Ms"]) >= 0
    wid = json.loads(created["body"])["website_id"]
    assert dynamodb_table.get_item(Key={"website_id": wid})["Item"]["url"] == PYTHON

    # READ one and READ all
    got = h(event("GET", website_id=wid), None)
    assert got["statusCode"] == 200
    assert float(got["headers"]["X-DynamoDB-Read-Time-Ms"]) >= 0
    assert json.loads(got["body"])["url"] == PYTHON
    listing = json.loads(h(event("GET"), None)["body"])
    assert len(listing["websites"]) == 1

    # UPDATE -> table has the new url
    updated = h(event("PUT", {"url": PYTHON_DOCS}, website_id=wid), None)
    assert updated["statusCode"] == 200
    assert float(updated["headers"]["X-DynamoDB-Write-Time-Ms"]) >= 0
    assert dynamodb_table.get_item(Key={"website_id": wid})["Item"]["url"] == PYTHON_DOCS

    # DELETE -> gone from the table
    deleted = h(event("DELETE", website_id=wid), None)
    assert deleted["statusCode"] == 200
    assert float(deleted["headers"]["X-DynamoDB-Write-Time-Ms"]) >= 0
    assert "Item" not in dynamodb_table.get_item(Key={"website_id": wid})
    assert h(event("GET", website_id=wid), None)["statusCode"] == 404

    # website that does not exist -> 404
    assert h(event("PUT", {"url": WSU}, website_id="99"), None)["statusCode"] == 404
    assert h(event("DELETE", website_id="99"), None)["statusCode"] == 404


def test_duplicate_website_returns_409(dynamodb_table):
    h = crud_lambda.lambda_handler

    first = h(event("POST", {"url": WSU}), None)
    second = h(event("POST", {"url": WSU}), None)

    assert first["statusCode"] == 201
    assert second["statusCode"] == 409
    assert len(dynamodb_table.scan()["Items"]) == 1


def test_update_to_existing_url_returns_409(dynamodb_table):
    h = crud_lambda.lambda_handler

    h(event("POST", {"url": WSU}), None)
    second = h(event("POST", {"url": PYTHON}), None)
    second_id = json.loads(second["body"])["website_id"]

    result = h(event("PUT", {"url": WSU}, website_id=second_id), None)

    assert result["statusCode"] == 409
    assert dynamodb_table.get_item(Key={"website_id": second_id})["Item"]["url"] == PYTHON
