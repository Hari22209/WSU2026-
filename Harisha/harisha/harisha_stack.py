from aws_cdk import (
    Stack,
    Duration,
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

        webhealth_lambda = lambda_.Function(
            self,
            "WebHealthLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda")
        )

        webhealth_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )

        schedule = events.Rule(
            self,
            "WebsiteMonitorSchedule",
            schedule=events.Schedule.rate(
                Duration.minutes(30)
            )
        )

        schedule.add_target(
            targets.LambdaFunction(webhealth_lambda)
        )

        websites = [
            "https://www.westernsydney.edu.au/",
            "https://www.google.com/",
            "https://www.amazon.com/"
        ]

        availability_metrics = []
        latency_metrics = []

        for index, website in enumerate(websites):

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

            availability_metrics.append(
                availability_metric
            )

            latency_metrics.append(
                latency_metric
            )

            availability_metric.create_alarm(
                self,
                f"AvailabilityAlarm{index}",
                threshold=1,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
                )
            )

            latency_metric.create_alarm(
                self,
                f"LatencyAlarm{index}",
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
                left=availability_metrics,
                width=12,
                height=6,
                left_y_axis=cloudwatch.YAxisProps(
                    min=0,
                    max=1
                )
            )
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Website Latency",
                left=latency_metrics,
                width=12,
                height=6
            )
        )