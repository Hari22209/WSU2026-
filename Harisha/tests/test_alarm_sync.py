"""Unit tests for lambda/alarm_sync.py.

CloudWatch is replaced by a MagicMock, so these tests only check which
alarms the Lambda asks CloudWatch to create or delete for each stream record.
"""
from unittest.mock import patch, MagicMock

import alarm_sync

PYTHON = "https://www.python.org/"
PYTHON_DOCS = "https://docs.python.org/"


def record(action, website_id, new_url=None, old_url=None):
    change = {"Keys": {"website_id": {"S": website_id}}}
    if new_url:
        change["NewImage"] = {"website_id": {"S": website_id}, "url": {"S": new_url}}
    if old_url:
        change["OldImage"] = {"website_id": {"S": website_id}, "url": {"S": old_url}}
    return {"eventName": action, "dynamodb": change}


def run(*records):
    mock_cloudwatch = MagicMock()
    with patch.object(alarm_sync, "cloudwatch", mock_cloudwatch), \
         patch.dict("os.environ", {"TOPIC_ARN": "arn:aws:sns:ap-southeast-2:111111111111:alerts",
                                   "ALARM_PREFIX": "Beta-HarishaStack"}):
        result = alarm_sync.lambda_handler({"Records": list(records)}, None)
    return mock_cloudwatch, result


def test_new_website_gets_availability_and_latency_alarms():
    mock_cloudwatch, result = run(record("INSERT", "abc", new_url=PYTHON))
    calls = mock_cloudwatch.put_metric_alarm.call_args_list
    assert [c.kwargs["MetricName"] for c in calls] == ["Availability", "Latency"]
    for c in calls:
        assert c.kwargs["Dimensions"] == [{"Name": "Website", "Value": PYTHON}]
        assert c.kwargs["AlarmActions"] == ["arn:aws:sns:ap-southeast-2:111111111111:alerts"]
        assert c.kwargs["AlarmName"].startswith("Beta-HarishaStack-site-abc-")
    assert result["created"] == ["abc"]


def test_removed_website_has_its_alarms_deleted():
    mock_cloudwatch, result = run(record("REMOVE", "abc", old_url=PYTHON))
    mock_cloudwatch.delete_alarms.assert_called_once_with(AlarmNames=[
        "Beta-HarishaStack-site-abc-availability",
        "Beta-HarishaStack-site-abc-latency",
    ])
    assert result["deleted"] == ["abc"]


def test_changed_url_moves_alarms_to_new_url():
    mock_cloudwatch, _ = run(record("MODIFY", "abc", new_url=PYTHON_DOCS, old_url=PYTHON))
    for c in mock_cloudwatch.put_metric_alarm.call_args_list:
        assert c.kwargs["Dimensions"] == [{"Name": "Website", "Value": PYTHON_DOCS}]


def test_same_url_modify_changes_nothing():
    mock_cloudwatch, _ = run(record("MODIFY", "abc", new_url=PYTHON, old_url=PYTHON))
    mock_cloudwatch.put_metric_alarm.assert_not_called()
    mock_cloudwatch.delete_alarms.assert_not_called()


def test_starting_websites_are_skipped():
    # sites 1, 2, 3 come from targets.json and already have CDK alarms
    mock_cloudwatch, result = run(record("INSERT", "1", new_url="https://www.westernsydney.edu.au/"))
    mock_cloudwatch.put_metric_alarm.assert_not_called()
    assert result == {"created": [], "deleted": []}
