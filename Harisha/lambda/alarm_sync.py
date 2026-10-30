"""Keeps CloudWatch alarms in step with the website list.

The TargetWebsiteTable has a DynamoDB Stream. Every time the CRUD API adds,
changes or removes a website, DynamoDB sends a stream record here:

    INSERT -> create an availability alarm and a latency alarm
    MODIFY -> if the URL changed, point both alarms at the new URL
    REMOVE -> delete both alarms

The starting websites in targets.json already get alarms from CDK, so they
are skipped here to avoid two alarms for the same site.
"""
import json
import os
from pathlib import Path

import boto3

cloudwatch = boto3.client("cloudwatch")

TARGETS_FILE = Path(__file__).resolve().parent / "targets.json"
STARTING_IDS = {site["website_id"] for site in json.loads(TARGETS_FILE.read_text())}


def site_alarm_names(website_id):
    prefix = os.environ.get("ALARM_PREFIX", "WebHealth")
    return [
        f"{prefix}-site-{website_id}-availability",
        f"{prefix}-site-{website_id}-latency",
    ]


def put_site_alarms(website_id, url):
    availability_name, latency_name = site_alarm_names(website_id)
    common = {
        "Namespace": "WebHealth",
        "Dimensions": [{"Name": "Website", "Value": url}],
        "Statistic": "Average",
        "Period": 1800,
        "EvaluationPeriods": 1,
        "AlarmActions": [os.environ["TOPIC_ARN"]],
    }
    cloudwatch.put_metric_alarm(
        AlarmName=availability_name,
        MetricName="Availability",
        Threshold=1,
        ComparisonOperator="LessThanThreshold",
        **common,
    )
    cloudwatch.put_metric_alarm(
        AlarmName=latency_name,
        MetricName="Latency",
        Threshold=2,
        ComparisonOperator="GreaterThanThreshold",
        **common,
    )


def text_value(image, field):
    return (image or {}).get(field, {}).get("S")


def lambda_handler(event, context):
    created, deleted = [], []

    for record in event.get("Records", []):
        change = record.get("dynamodb", {})
        website_id = text_value(change.get("Keys"), "website_id")
        if not website_id or website_id in STARTING_IDS:
            continue

        action = record.get("eventName")
        new_url = text_value(change.get("NewImage"), "url")
        old_url = text_value(change.get("OldImage"), "url")

        if action == "INSERT" or (action == "MODIFY" and new_url != old_url):
            put_site_alarms(website_id, new_url)
            created.append(website_id)
        elif action == "REMOVE":
            cloudwatch.delete_alarms(AlarmNames=site_alarm_names(website_id))
            deleted.append(website_id)

    return {"created": created, "deleted": deleted}
