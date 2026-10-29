import json
import os
import uuid
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def read_alarm(sns_message):
    """SNS sends the CloudWatch alarm as a JSON string. Pull out the useful parts."""
    try:
        alarm = json.loads(sns_message)
    except (TypeError, ValueError):
        alarm = {}

    website = ""
    trigger = alarm.get("Trigger") or {}
    for dimension in trigger.get("Dimensions") or []:
        if dimension.get("name") == "Website":
            website = dimension.get("value", "")

    return {
        "alarm_name": alarm.get("AlarmName", "Unknown"),
        "state": alarm.get("NewStateValue", "Unknown"),
        "reason": alarm.get("NewStateReason", ""),
        "website": website,
    }


def lambda_handler(event, context):
    saved_ids = []

    # SNS can deliver more than one message in one event
    for record in event.get("Records", []):
        sns = record.get("Sns", {})
        alarm_id = str(uuid.uuid4())

        item = {
            "alarm_id": alarm_id,
            "timestamp": sns.get("Timestamp") or datetime.now(timezone.utc).isoformat(),
            "alarm_message": sns.get("Message", ""),
        }
        item.update(read_alarm(sns.get("Message")))

        table.put_item(Item=item)
        saved_ids.append(alarm_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Alarm information saved",
            "alarm_ids": saved_ids,
        }),
    }