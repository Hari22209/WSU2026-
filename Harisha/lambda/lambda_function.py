import urllib.request
import json
import time
import boto3

cloudwatch = boto3.client("cloudwatch")


def lambda_handler(event, context):

    with open("websites.json", "r") as file:
        data = json.load(file)

    results = []

    for url in data["websites"]:

        start_time = time.time()

        try:
            response = urllib.request.urlopen(url, timeout=10)
            end_time = time.time()

            response_time = round(end_time - start_time, 3)

            results.append({
                "website": url,
                "status_code": response.status,
                "response_time": response_time,
                "status": "UP"
            })

            # Publish availability metric
            cloudwatch.put_metric_data(
                Namespace="WebHealth",
                MetricData=[
                    {
                        "MetricName": "Availability",
                        "Dimensions": [
                            {
                                "Name": "Website",
                                "Value": url
                            }
                        ],
                        "Value": 1,
                        "Unit": "Count"
                    }
                ]
            )

            # Publish latency metric
            cloudwatch.put_metric_data(
                Namespace="WebHealth",
                MetricData=[
                    {
                        "MetricName": "Latency",
                        "Dimensions": [
                            {
                                "Name": "Website",
                                "Value": url
                            }
                        ],
                        "Value": response_time,
                        "Unit": "Seconds"
                    }
                ]
            )

        except Exception as e:

            results.append({
                "website": url,
                "status": "DOWN",
                "error": str(e)
            })

            # Publish unavailable metric
            cloudwatch.put_metric_data(
                Namespace="WebHealth",
                MetricData=[
                    {
                        "MetricName": "Availability",
                        "Dimensions": [
                            {
                                "Name": "Website",
                                "Value": url
                            }
                        ],
                        "Value": 0,
                        "Unit": "Count"
                    }
                ]
            )

    return {
        "results": results
    }