import os
import urllib.request
import time
import boto3


cloudwatch = boto3.client("cloudwatch")

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def get_websites():
    """Read ALL websites from the DynamoDB table.
    scan() returns at most 1 MB per call, so keep reading
    while DynamoDB says there is more (LastEvaluatedKey).
    """
    result = table.scan()
    websites = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = table.scan(ExclusiveStartKey=result["LastEvaluatedKey"])
        websites.extend(result.get("Items", []))
    return websites


def publish_metrics(url, availability, response_time):
    cloudwatch.put_metric_data(
        Namespace="WebHealth",
        MetricData=[
            {
                "MetricName": "Availability",
                "Dimensions": [{"Name": "Website", "Value": url}],
                "Value": availability,
                "Unit": "Count",
            },
            {
                "MetricName": "Latency",
                "Dimensions": [{"Name": "Website", "Value": url}],
                "Value": response_time,
                "Unit": "Seconds",
            },
        ],
    )


def lambda_handler(event, context):
    websites = get_websites()
    results = []

    for item in websites:
        url = item["url"]
        start_time = time.time()
        try:
            response = urllib.request.urlopen(url, timeout=10)
            response_time = round(time.time() - start_time, 3)
            results.append({
                "website_id": item["website_id"],
                "website": url,
                "status_code": response.status,
                "response_time": response_time,
                "status": "UP",
            })
            availability = 1
        except Exception as e:
            response_time = round(time.time() - start_time, 3)
            results.append({
                "website_id": item["website_id"],
                "website": url,
                "status_code": 0,
                "response_time": response_time,
                "status": "DOWN",
                "error": str(e)
            })
            availability = 0

        # Publish OUTSIDE the try, so a CloudWatch problem can never
        # make a working website look DOWN.
        publish_metrics(url, availability, response_time)

    return {
        "statusCode": 200,
        "results": results,
    }