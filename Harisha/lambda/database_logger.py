import json
import os
import boto3
from datetime import datetime, timezone


dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]


def lambda_handler(event, context):

    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):

        sns_message = record["Sns"]["Message"]

        item = {
            "alarm_id": record["Sns"]["MessageId"],
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "alarm_message": sns_message,
        }

        table.put_item(
            Item=item
        )

    return {
        "statusCode": 200,
        "body": json.dumps(
            "Alarm information stored successfully"
        ),
    }