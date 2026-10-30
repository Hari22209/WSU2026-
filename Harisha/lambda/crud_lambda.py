from urllib.parse import urlparse
import json
import os
import uuid
import time 
import boto3


dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def response(status_code, body, extra_headers=None):
    headers = {
        "Content-Type": "application/json"
    }
    
    if extra_headers:
        headers.update(extra_headers)
        
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    method = event.get("httpMethod")
    path_parameters = event.get("pathParameters") or {}
    website_id = path_parameters.get("website_id")

    if method == "POST":
        return create_website(event)

    if method == "GET":
        if website_id:
            return get_website(website_id)
        return get_websites()

    if method == "PUT":
        return update_website(event, website_id)

    if method == "DELETE":
        return delete_website(website_id)

    return response(
        405,
        {"error": "Method not allowed"}
    )



def is_valid_url(url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and "." in parsed.hostname
            and not any(c.isspace() for c in url)
        )
    except ValueError:
        return False



def website_url_exists(url, exclude_id=None):
    result = table.scan()
    while True:
        for item in result.get("Items", []):
            if (
                item.get("url") == url
                and item.get("website_id") != exclude_id
            ):
                return True

        if "LastEvaluatedKey" not in result:
            return False

        result = table.scan(
            ExclusiveStartKey=result["LastEvaluatedKey"]
        )


def create_website(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(
            400,
            {"error": "Invalid JSON"}
        )

    url = body.get("url")

    if not url:
        return response(
            400,
            {"error": "url is required"}
        )

    if not is_valid_url(url):
        return response(
            400,
            {"error": "Invalid website URL"}
        )

    if website_url_exists(url):
        return response(409, {"error": "Website URL already exists"})

    website_id = str(uuid.uuid4())

    item = {
        "website_id": website_id,
        "url": url
    }

    start_time = time.perf_counter()
    table.put_item(Item=item)
    write_time_ms = (time.perf_counter() - start_time) * 1000

    return response(
        201,
        item,
        {"X-DynamoDB-Write-Time-Ms": str(round(write_time_ms, 3))}
    )


def get_websites():
    result = table.scan()

    return response(
        200,
        {"websites": result.get("Items", [])}
    )


def get_website(website_id):
    start_time = time.perf_counter()
    result = table.get_item(
        Key={"website_id": website_id}
    )
    read_time_ms = (time.perf_counter() - start_time) * 1000

    item = result.get("Item")

    if not item:
        return response(404, {"error": "Website not found"})

    return response(
        200,
        item,
        {"X-DynamoDB-Read-Time-Ms": str(round(read_time_ms, 3))}
    )


def update_website(event, website_id):
    if not website_id:
        return response(
            400,
            {"error": "website_id is required"}
        )

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(
            400,
            {"error": "Invalid JSON"}
        )

    url = body.get("url")

    if not url:
        return response(
            400,
            {"error": "url is required"}
        )

    if not is_valid_url(url):
        return response(
            400,
            {"error": "Invalid website URL"}
        )

    if website_url_exists(url, exclude_id=website_id):
        return response(409, {"error": "Website URL already exists"})

    existing = table.get_item(
        Key={
            "website_id": website_id
        }
    )

    if "Item" not in existing:
        return response(
            404,
            {"error": "Website not found"}
        )

    start_time = time.perf_counter()
    result = table.update_item(
        Key={
            "website_id": website_id
        },
        UpdateExpression="SET #url = :url",
        ExpressionAttributeNames={
            "#url": "url"
        },
        ExpressionAttributeValues={
            ":url": url
        },
        ReturnValues="ALL_NEW"
    )

    write_time_ms = (time.perf_counter() - start_time) * 1000

    return response(
        200,
        result["Attributes"],
        {"X-DynamoDB-Write-Time-Ms": str(round(write_time_ms, 3))}
    )


def delete_website(website_id):
    if not website_id:
        return response(
            400,
            {"error": "website_id is required"}
        )

    start_time = time.perf_counter()
    result = table.delete_item(
        Key={
            "website_id": website_id
        },
        ReturnValues="ALL_OLD"
    )
    write_time_ms = (time.perf_counter() - start_time) * 1000

    if "Attributes" not in result:
        return response(
            404,
            {"error": "Website not found"}
        )

    return response(
        200,
        {
            "message": "Website deleted",
            "website": result["Attributes"]
        },
        {"X-DynamoDB-Write-Time-Ms": str(round(write_time_ms, 3))}
    )
