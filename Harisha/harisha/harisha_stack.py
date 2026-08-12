from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
)
from constructs import Construct


class HarishaStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        hello_lambda = lambda_.Function(
            self,
            "HelloLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda")
        )

        hello_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )

        hello_lambda.apply_removal_policy(
            RemovalPolicy.DESTROY
        )

        schedule = events.Rule(
            self,
            "WebsiteMonitorSchedule",
            schedule=events.Schedule.rate(
                Duration.minutes(30)
            )
        )

        schedule.add_target(
            targets.LambdaFunction(hello_lambda)
        )

        websites = [
            "https://www.westernsydney.edu.au/",
            "https://www.google.com/",
            "https://www.amazon.com/"
        ]

        for website in websites:

            availability_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Availability",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average"
            )

            latency_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Latency",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average"
            )

            availability_metric.create_alarm(
                self,
                f"AvailabilityAlarm{websites.index(website)}",
                threshold=1,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
                )
            )

            latency_metric.create_alarm(
                self,
                f"LatencyAlarm{websites.index(website)}",
                threshold=2,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
                )
            )

        dashboard = cloudwatch.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name="WebHealthDashboard"
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Website Availability",
                left=[
                    cloudwatch.Metric(
                        namespace="WebHealth",
                        metric_name="Availability",
                        period=Duration.minutes(30),
                        statistic="Average"
                    )
                ],
                width=12
            )
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Website Latency",
                left=[
                    cloudwatch.Metric(
                        namespace="WebHealth",
                        metric_name="Latency",
                        period=Duration.minutes(30),
                        statistic="Average"
                    )
                ],
                width=12
            )
        )