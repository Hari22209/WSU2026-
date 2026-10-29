# WebHealth Websites API

This document describes the HTTP interface of the WebHealth project. Users call it to add, view, change or remove the websites in the monitoring list. API Gateway passes each call to the CRUD Lambda (`lambda/crud_lambda.py`), and the list itself lives in the DynamoDB table **TargetWebsiteTable**.

## Finding the API address

Every stage has its own address. Print the Prod one with this command (change `Prod` to `Alpha`, `Beta` or `Gamma` for the others):

```bash
aws cloudformation describe-stacks --stack-name Prod-HarishaStack --region ap-southeast-2 \
  --query "Stacks[0].Outputs[?OutputKey=='WebHealthApiUrl'].OutputValue" --output text
```

Prod address used in the examples below:

```bash
API=https://wnq06hjc72.execute-api.ap-southeast-2.amazonaws.com/prod
```

- Public: anyone with the address can call it.
- Bodies are JSON in both directions.
- `website_id` (the DynamoDB partition key) picks out one website.

## Quick reference

1. `GET /websites` – see the whole monitoring list
2. `POST /websites` – put a new website on the list
3. `GET /websites/{website_id}` – look at one website
4. `PUT /websites/{website_id}` – point an existing entry at a new URL
5. `DELETE /websites/{website_id}` – take a website off the list

---

## 1. `GET /websites`

- **Body:** none
- **Success:** `200`
- **DynamoDB call:** `scan`
- **Checked by:** `test_crud_lifecycle_with_dynamodb`, smoke tests

```bash
curl $API/websites
```

```json
{
  "websites": [
    {"website_id": "1", "url": "https://www.westernsydney.edu.au/"},
    {"website_id": "2", "url": "https://www.google.com/"},
    {"website_id": "3", "url": "https://www.amazon.com/"}
  ]
}
```

## 2. `POST /websites`

- **Body:** `{"url": "<address>"}` – `url` is required
- **Success:** `201` – returns the new item with its generated `website_id`
- **Extra header:** `X-DynamoDB-Write-Time-Ms` – duration of the `put_item` call
- **DynamoDB calls:** `scan` (duplicate check), then `put_item`
- **Fails with:** `400` if the body is not JSON, has no `url` or the URL is badly formed; `409` if that URL is already in the list
- **Checked by:** `test_create_website_returns_201_and_saves_item`, `test_create_rejects_invalid_url`, `test_duplicate_website_returns_409`, `test_api_crud_cycle_and_dynamodb_latency`

```bash
curl -i -X POST $API/websites -d '{"url": "https://www.python.org/"}'
```

```json
{"website_id": "5f0c2b6e-8a51-4d0e-9c1a-2f3b7d9e1a44", "url": "https://www.python.org/"}
```

Because the crawler reads the table every 30 minutes, the new site is included from the following run onwards.

## 3. `GET /websites/{website_id}`

- **Body:** none
- **Success:** `200` – returns the item
- **Extra header:** `X-DynamoDB-Read-Time-Ms` – duration of the `get_item` call
- **DynamoDB call:** `get_item`
- **Fails with:** `404` if no item has that ID
- **Checked by:** `test_get_website_returns_dynamodb_read_time_header`, `test_read_missing_website_returns_404`

```bash
curl -i $API/websites/2
```

```json
{"website_id": "2", "url": "https://www.google.com/"}
```

## 4. `PUT /websites/{website_id}`

- **Body:** `{"url": "<new address>"}` – `url` is required
- **Success:** `200` – returns the updated item (same `website_id`)
- **DynamoDB calls:** `scan` (duplicate check), `get_item` to confirm it exists, then `update_item`
- **Fails with:** `400` (bad JSON / no `url` / badly formed URL), `404` (unknown ID), `409` (another entry already has that URL)
- **Checked by:** `test_crud_lifecycle_with_dynamodb`, `test_update_rejects_invalid_url`, `test_update_to_existing_url_returns_409`

```bash
curl -X PUT $API/websites/<website_id> -d '{"url": "https://docs.python.org/"}'
```

```json
{"website_id": "<website_id>", "url": "https://docs.python.org/"}
```

## 5. `DELETE /websites/{website_id}`

- **Body:** none
- **Success:** `200` – returns the item that was removed
- **DynamoDB call:** `delete_item` with `ReturnValues="ALL_OLD"` – if nothing comes back, the ID did not exist
- **Fails with:** `404` if no item has that ID
- **Checked by:** `test_crud_lifecycle_with_dynamodb`, `test_api_crud_cycle_and_dynamodb_latency`

```bash
curl -X DELETE $API/websites/<website_id>
```

```json
{
  "message": "Website deleted",
  "website": {"website_id": "<website_id>", "url": "https://docs.python.org/"}
}
```

---

## Status codes used

When something goes wrong, the body contains a single `error` field explaining the problem, for example `{"error": "Website not found"}`.

- `200` (GET, PUT, DELETE) – done
- `201` (POST) – new website stored
- `400` (POST, PUT, DELETE) – `Invalid JSON`, `url is required`, `Invalid website URL` or `website_id is required`
- `404` (GET one, PUT, DELETE) – `Website not found`
- `409` (POST, PUT) – `Website URL already exists`
- `405` (anything else) – `Method not allowed`

## Good to know

- Each URL can appear only once: the CRUD Lambda scans the table first and answers `409` if the address is already stored.
- Accepted addresses use the `http` or `https` scheme, have a host name containing at least one dot, and contain no whitespace anywhere.
- Sites added here are crawled and get metrics, but only the sites in `lambda/targets.json` have their own CloudWatch alarms (see *Known limitations* in the README).
- To try PUT or DELETE safely, first POST a test site and use the `website_id` it returns, so the three starting websites stay in the table.
