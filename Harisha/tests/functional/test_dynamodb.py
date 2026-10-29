import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

import database_logger
import lambda_function


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield boto3.resource("dynamodb", region_name="us-east-1")


def test_crawler_reads_websites_from_dynamodb(aws, monkeypatch):
    table = aws.create_table(
        TableName="targets",
        KeySchema=[{"AttributeName": "website_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "website_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.put_item(Item={"website_id": "a", "url": "https://www.westernsydney.edu.au/"})
    table.put_item(Item={"website_id": "b", "url": "https://www.python.org/"})
    monkeypatch.setattr(lambda_function, "table", table)

    ok = MagicMock()
    ok.status = 200
    with patch("lambda_function.urllib.request.urlopen", return_value=ok), \
         patch("lambda_function.cloudwatch.put_metric_data"):
        result = lambda_function.lambda_handler({}, None)

    checked = sorted(r["website"] for r in result["results"])
    assert checked == ["https://www.python.org/", "https://www.westernsydney.edu.au/"]


def test_alarm_logger_saves_alarm_to_dynamodb(aws, monkeypatch):
    table = aws.create_table(
        TableName="alarms",
        KeySchema=[{"AttributeName": "alarm_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "alarm_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    monkeypatch.setattr(database_logger, "table", table)

    alarm = {
        "AlarmName": "LatencyAlarm0",
        "NewStateValue": "ALARM",
        "NewStateReason": "Threshold Crossed",
        "Trigger": {"MetricName": "Latency",
                    "Dimensions": [{"name": "Website", "value": "https://www.westernsydney.edu.au/"}]},
    }
    sns_event = {"Records": [{"Sns": {"Message": json.dumps(alarm),
                                      "Timestamp": "2026-11-01T10:00:00.000Z"}}]}

    result = database_logger.lambda_handler(sns_event, None)
    alarm_id = json.loads(result["body"])["alarm_ids"][0]

    saved = table.get_item(Key={"alarm_id": alarm_id})["Item"]
    assert saved["alarm_name"] == "LatencyAlarm0"
    assert saved["state"] == "ALARM"
    assert saved["website"] == "https://www.westernsydney.edu.au/"
    assert saved["timestamp"] == "2026-11-01T10:00:00.000Z"