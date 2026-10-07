import aws_cdk as cdk
from aws_cdk.assertions import Template

from harisha.harisha_stack import HarishaStack

def get_template():
    app = cdk.App()
    stack = HarishaStack(app, "TestStack")
    return Template.from_stack(stack)

def _template():
    return Template.from_stack(
        HarishaStack(cdk.App(), "FunctionalExtraStack")
    )

def test_two_python_lambdas():
    template = get_template()
    
    template.resource_count_is(
        "AWS::Lambda::Function",
        2
    )
    
def test_dynamodb_table_exists():
    template = get_template()
    
    template.resource_count_is(
        "AWS::DynamoDB::Table",
        1
    )
    
def test_sns_topic_exists():
    template = get_template()
    
    template.resource_count_is(
        "AWS::SNS::Topic",
        1
    )
    
def test_eventbridge_rule_exists():
    template = get_template()
    
    template.resource_count_is(
        "AWS::Events::Rule",
        1
    )
    
def test_cloudwatch_dashboard_exists():
    template = get_template()
    
    template.resource_count_is(
        "AWS::CloudWatch::Dashboard",
        1
    )
    
def test_schedule_runs_every_30_minutes():
        _template().has_resource_properties(
            "AWS::Events::Rule",
            {
                "ScheduleExpression": "rate(30 minutes)"
            }
        )
        
def test_six_alarms_created():
     _template().resource_count_is(
        "AWS::CloudWatch::Alarm",
        6
    )
     
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
                                              