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
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["website_id"]] = dict(Item)

    def get_item(self, Key):
        item = self.items.get(Key["website_id"])
        return {"Item": item} if item else {}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames,
                    ExpressionAttributeValues, ReturnValues=None, **kw):
        item = self.items[Key["website_id"]]
        item["url"] = ExpressionAttributeValues[":url"]
        return {"Attributes": dict(item)}

    def delete_item(self, Key, **kw):
        old = self.items.pop(Key["website_id"], None)
        return {"Attributes": old} if old else {}

    def scan(self, **kw):
        return {"Items": list(self.items.values())}


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


def test_crud_lifecycle():
    fake = FakeTable()
    with patch.object(crud_lambda, "table", fake):
        h = crud_lambda.lambda_handler
        created = h(event("POST", {"url": "https://a.com"}), None)
        assert created["statusCode"] == 201
        wid = json.loads(created["body"])["website_id"]

        got = h(event("GET", website_id=wid), None)
        assert got["statusCode"] == 200
        assert json.loads(got["body"])["url"] == "https://a.com"

        listing = json.loads(h(event("GET"), None)["body"])
        assert len(listing["websites"]) == 1

        updated = h(event("PUT", {"url": "https://b.com"}, website_id=wid), None)
        assert updated["statusCode"] == 200
        assert json.loads(updated["body"])["url"] == "https://b.com"

        assert h(event("DELETE", website_id=wid), None)["statusCode"] in (200, 204)
        assert h(event("GET", website_id=wid), None)["statusCode"] == 404
