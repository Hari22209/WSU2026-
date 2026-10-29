import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from harisha.harisha_stack import HarishaStack, ALERT_EMAILS, TARGET_WEBSITES, ENABLE_CODEDEPLOY_ROLLBACK


def get_template():
    app = cdk.App()
    stack = HarishaStack(app, "TestStack")
    return Template.from_stack(stack)


def _template():
    return Template.from_stack(
        HarishaStack(cdk.App(), "FunctionalExtraStack")
    )


def test_three_python_lambdas():
    # crawler, CRUD and alarm logger (the seeding helper is Node.js, made by CDK)
    template = get_template()
    python = template.find_resources(
        "AWS::Lambda::Function", {"Properties": {"Runtime": "python3.11"}}
    )
    assert len(python) == 3


def test_two_dynamodb_tables():
    template = get_template()
    template.resource_count_is("AWS::DynamoDB::Table", 2)


def test_sns_topic_exists():
    template = get_template()
    template.resource_count_is("AWS::SNS::Topic", 1)


def test_eventbridge_rule_exists():
    template = get_template()
    template.resource_count_is("AWS::Events::Rule", 1)


def test_cloudwatch_dashboard_exists():
    template = get_template()
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)


def test_schedule_runs_every_30_minutes():
    _template().has_resource_properties(
        "AWS::Events::Rule",
        {"ScheduleExpression": "rate(30 minutes)"}
    )


def test_ten_alarms_created():
    # 3 websites x 2 (availability + latency) = 6
    # + 4 crawler alarms (errors, duration, memory, not running) = 10
    _template().resource_count_is("AWS::CloudWatch::Alarm", 10)


def test_availability_alarm_config():
    _template().has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "Namespace": "WebHealth",
            "MetricName": "Availability",
            "Threshold": 1,
            "ComparisonOperator": "LessThanThreshold",
        }
    )


def test_crud_api_routes_are_configured():
    template = get_template()
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    template.resource_count_is("AWS::ApiGateway::Resource", 2)
    template.resource_count_is("AWS::ApiGateway::Method", 5)


def test_crud_api_supports_get_and_post_methods():
    template = get_template()
    template.has_resource_properties("AWS::ApiGateway::Method", {"HttpMethod": "GET"})
    template.has_resource_properties("AWS::ApiGateway::Method", {"HttpMethod": "POST"})


def test_crud_api_supports_put_and_delete_methods():
    template = get_template()
    template.has_resource_properties("AWS::ApiGateway::Method", {"HttpMethod": "PUT"})
    template.has_resource_properties("AWS::ApiGateway::Method", {"HttpMethod": "DELETE"})


def test_email_subscriptions_match_alert_emails():
    template = get_template()
    emails = template.find_resources(
        "AWS::SNS::Subscription", {"Properties": {"Protocol": "email"}}
    )
    endpoints = sorted(s["Properties"]["Endpoint"] for s in emails.values())
    assert endpoints == sorted(ALERT_EMAILS)


def test_crawler_has_rollback_on_alarm():
    template = get_template()
    # the alias "live" always exists (rollback moves this alias between versions)
    template.has_resource_properties("AWS::Lambda::Alias", {"Name": "live"})
    if ENABLE_CODEDEPLOY_ROLLBACK:
        template.has_resource_properties("AWS::CodeDeploy::DeploymentGroup", {
            "AutoRollbackConfiguration": {
                "Enabled": True,
                "Events": Match.array_with(["DEPLOYMENT_STOP_ON_ALARM"]),
            },
            "AlarmConfiguration": {"Enabled": True, "Alarms": Match.any_value()},
        })
    else:
        # CodeDeploy is switched off (AWS Free plan), so no deployment group
        template.resource_count_is("AWS::CodeDeploy::DeploymentGroup", 0)


def test_crawler_memory_alarm_exists():
    template = get_template()
    template.has_resource_properties("AWS::CloudWatch::Alarm", {
        "Namespace": "LambdaInsights",
        "MetricName": "memory_utilization",
        "Threshold": 80,
    })


def test_target_list_is_placed_in_dynamodb_on_deploy():
    template = get_template()
    seeds = template.find_resources("Custom::AWS")
    assert len(seeds) == 1
    create_call = str(list(seeds.values())[0]["Properties"]["Create"])
    assert "batchWriteItem" in create_call
    for site in TARGET_WEBSITES:
        assert site["url"] in create_call