# Website Target Management API

## Overview

The Website Target Management API allows users to create, read, update and delete website targets for the WebHealth monitoring project.

The API uses Amazon API Gateway, AWS Lambda with Python, and Amazon DynamoDB.

## Base URL

Use the deployed API Gateway invoke URL for your environment (for example, Beta).

```text
https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/YOUR_STAGE
```

Replace the example URL with the actual API Gateway invoke URL.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/websites` | Create a website target |
| GET | `/websites` | List website targets |
| GET | `/websites/{website_id}` | Get one website target |
| PUT | `/websites/{website_id}` | Update a website target |
| DELETE | `/websites/{website_id}` | Delete a website target |

## Create a website

**Request**

```http
POST /websites
Content-Type: application/json
```

```json
{
  "url": "https://example.com"
}
```

**Success:** `201 Created`

```json
{
  "website_id": "generated-uuid",
  "url": "https://example.com"
}
```

The response includes the `X-DynamoDB-Write-Time-Ms` header, which measures the time around the DynamoDB write call in milliseconds.

Possible errors include `400 Bad Request` when the JSON is invalid or `url` is missing.

## List websites

**Request**

```http
GET /websites
```

**Success:** `200 OK`

```json
{
  "websites": [
    {
      "website_id": "generated-uuid",
      "url": "https://example.com"
    }
  ]
}
```

An empty list is returned if there are no saved website targets.

## Get one website

**Request**

```http
GET /websites/{website_id}
```

**Success:** `200 OK`

Returns the website ID and URL. The response includes `X-DynamoDB-Read-Time-Ms`, measuring the time around the DynamoDB read call in milliseconds.

**Not found:** `404 Not Found`

```json
{
  "error": "Website not found"
}
```

## Update a website

**Request**

```http
PUT /websites/{website_id}
Content-Type: application/json
```

```json
{
  "url": "https://updated-example.com"
}
```

**Success:** `200 OK`

Returns the updated website ID and URL.

Possible errors include `400 Bad Request` for invalid JSON, a missing URL or missing website ID, and `404 Not Found` if the website does not exist.

## Delete a website

**Request**

```http
DELETE /websites/{website_id}
```

**Success:** `200 OK`

```json
{
  "message": "Website deleted",
  "website": {
    "website_id": "generated-uuid",
    "url": "https://example.com"
  }
}
```

**Not found:** `404 Not Found` if the website does not exist.

## Other responses

Unsupported HTTP methods return `405 Method Not Allowed`.

JSON responses use the `Content-Type: application/json` header.

## Timing headers

| Header | Meaning |
|---|---|
| `X-DynamoDB-Write-Time-Ms` | Time around the DynamoDB write call |
| `X-DynamoDB-Read-Time-Ms` | Time around the individual DynamoDB read call |

The timings include AWS SDK and network overhead; they do not measure only DynamoDB internal processing time.

## Technology

- Amazon API Gateway
- AWS Lambda (Python)
- Amazon DynamoDB
- AWS CDK

## Notes

The actual API Gateway invoke URL depends on the deployed environment. Check the API Gateway console or deployment outputs before making requests.
