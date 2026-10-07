import json
from unittest.mock import patch, MagicMock

import crud_lambda


def event(method, body=None, website_id=None):
    return {
        "httpMethod": method,
        "pathParameters": {"website_id": website_id} if website_id else None,
        "body": json.dumps(body) if body is not None else None,
    }


class FakeTable:
    """In-memory stand-in for the DynamoDB table."""

    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["website_id"]] = Item

    def get_item(self, Key):
        item = self.items.get(Key["website_id"])
        return {"Item": item} if item else {}

    def delete_item(self, Key, ReturnValues=None):
        old = self.items.pop(Key["website_id"], None)
        return {"Attributes": old} if old else {}

    def scan(self):
        return {"Items": list(self.items.values())}


# ---- 2 unit tests ----
def test_create_target_returns_201_and_saves_item():
    fake = MagicMock()
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(
            event("POST", {"website_id": "1", "url": "https://example.com"}), None
        )
    assert resp["statusCode"] == 201
    fake.put_item.assert_called_once_with(
        Item={"website_id": "1", "url": "https://example.com"}
    )


def test_create_target_without_website_returns_400():
    fake = MagicMock()
    with patch.object(crud_lambda, "table", fake):
        resp = crud_lambda.lambda_handler(event("POST", {"website_id": "1"}), None)
    assert resp["statusCode"] == 400
    fake.put_item.assert_not_called()


# ---- 1 functional test: full create/read/list/delete cycle ----
def test_crud_lifecycle():
    fake = FakeTable()
    with patch.object(crud_lambda, "table", fake):
        h = crud_lambda.lambda_handler
        assert h(event("POST", {"website_id": "9", "url": "https://a.com"}), None)["statusCode"] == 201

        got = h(event("GET", website_id="9"), None)
        assert got["statusCode"] == 200
        assert json.loads(got["body"])["url"] == "https://a.com"

        listing = json.loads(h(event("GET"), None)["body"])
        assert len(listing["websites"]) == 1

        assert h(event("DELETE", website_id="9"), None)["statusCode"] == 200
        assert h(event("GET", website_id="9"), None)["statusCode"] == 404
