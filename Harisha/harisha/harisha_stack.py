import json
from pathlib import Path
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_codedeploy as codedeploy,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    custom_resources as cr,
)
from constructs import Construct

# Email addresses that receive alarm notifications.
# Each person must click "Confirm subscription" in the AWS email.
# To add more people, add another line inside the list.
ALERT_EMAILS = [
    "22099290@westernsydney.edu.au",
]

# Automatic rollback uses AWS CodeDeploy. CodeDeploy is not available on
# the AWS Free plan, so it is switched off for this account. Set to True on
# an account with the paid plan to turn rollback on.
ENABLE_CODEDEPLOY_ROLLBACK = False

# The target list is kept in lambda/targets.json. It is placed in the
# DynamoDB table when the stack is deployed, and the same list is used to
# create the alarms and dashboard. To change the starting websites, edit the
# JSON file - no Python change needed.
TARGETS_FILE = Path(__file__).resolve().parents[1] / "lambda" / "targets.json"
TARGET_WEBSITES = json.loads(TARGETS_FILE.read_text())


class HarishaStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dashboard_name: str = "WebHealthDashboard",
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        lambda_code = lambda_.Code.from_asset(str(Path(__file__).resolve().parents[1] / "lambda"))

        # DynamoDB table for monitored websites
        target_table = dynamodb.Table(
            self,
            "TargetWebsiteTable",
            partition_key=dynamodb.Attribute(
                name="website_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Place the target list in DynamoDB when the stack is first deployed.
        # AwsCustomResource makes the AWS SDK call "BatchWriteItem" for us
        # during deployment, so the table is never empty.
        cr.AwsCustomResource(
            self,
            "SeedTargetWebsites",
            on_create=cr.AwsSdkCall(
                service="DynamoDB",
                action="batchWriteItem",
                parameters={
                    "RequestItems": {
                        target_table.table_name: [
                            {
                                "PutRequest": {
                                    "Item": {
                                        "website_id": {"S": site["website_id"]},
                                        "url": {"S": site["url"]},
                                    }
                                }
                            }
                            for site in TARGET_WEBSITES
                        ]
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of("SeedTargetWebsites"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=[target_table.table_arn]
            ),
        )

        # WebHealth monitoring Lambda
        webhealth_lambda = lambda_.Function(
            self,
            "WebHealthLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_code,
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": target_table.table_name,
            },
            # Lambda Insights publishes memory metrics
            insights_version=lambda_.LambdaInsightsVersion.VERSION_1_0_498_0,
        )

        # Allow monitoring Lambda to read websites
        target_table.grant_read_data(webhealth_lambda)

        # Allow Lambda to publish CloudWatch metrics
        webhealth_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"],
            )
        )

        # Alias "live". The schedule calls the alias, and
        # CodeDeploy moves the alias between versions -> this enables rollback.
        webhealth_alias = lambda_.Alias(
            self,
            "WebHealthLiveAlias",
            alias_name="live",
            version=webhealth_lambda.current_version,
        )

        self.function_name_output = CfnOutput(
            self,
            "WebHealthFunctionName",
            value=webhealth_lambda.function_name,
        )

        # CRUD Lambda
        crud_lambda = lambda_.Function(
            self,
            "CrudLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="crud_lambda.lambda_handler",
            code=lambda_code,
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": target_table.table_name,
            },
        )

        target_table.grant_read_write_data(crud_lambda)

        # API Gateway
        api = apigateway.RestApi(
            self,
            "WebHealthApi",
            rest_api_name="WebHealthWebsiteApi",
            description="CRUD API for monitored websites",
        )

        websites_resource = api.root.add_resource("websites")
        website_id_resource = websites_resource.add_resource("{website_id}")

        # POST /websites
        websites_resource.add_method("POST", apigateway.LambdaIntegration(crud_lambda))
        # GET /websites
        websites_resource.add_method("GET", apigateway.LambdaIntegration(crud_lambda))
        # GET /websites/{website_id}
        website_id_resource.add_method("GET", apigateway.LambdaIntegration(crud_lambda))
        # PUT /websites/{website_id}
        website_id_resource.add_method("PUT", apigateway.LambdaIntegration(crud_lambda))
        # DELETE /websites/{website_id}
        website_id_resource.add_method("DELETE", apigateway.LambdaIntegration(crud_lambda))

        self.api_url_output = CfnOutput(
            self,
            "WebHealthApiUrl",
            value=api.url,
        )

        # Table name output, so integration tests can check the REAL table
        self.target_table_output = CfnOutput(
            self,
            "TargetWebsiteTableName",
            value=target_table.table_name,
        )

        # Run WebHealth Lambda every 30 minutes (through the "live" alias)
        schedule = events.Rule(
            self,
            "WebsiteMonitorSchedule",
            schedule=events.Schedule.rate(
                Duration.minutes(30)
            ),
        )

        schedule.add_target(
            targets.LambdaFunction(webhealth_alias)
        )

        # DynamoDB table for alarm information
        alarm_table = dynamodb.Table(
            self,
            "AlarmInformationTable",
            partition_key=dynamodb.Attribute(
                name="alarm_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Lambda to save alarm information into DynamoDB
        database_lambda = lambda_.Function(
            self,
            "AlarmDatabaseLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="database_logger.lambda_handler",
            code=lambda_code,
            environment={
                "TABLE_NAME": alarm_table.table_name,
            },
        )

        alarm_table.grant_write_data(database_lambda)

        # SNS topic
        alarm_topic = sns.Topic(
            self,
            "alarmnotification",
            display_name="WebHealth Alarm Notifications",
        )

        # One email subscription for each email in ALERT_EMAILS
        for email in ALERT_EMAILS:
            alarm_topic.add_subscription(
                subscriptions.EmailSubscription(email)
            )

        # Send SNS messages to database lambda
        alarm_topic.add_subscription(
            subscriptions.LambdaSubscription(
                database_lambda
            )
        )

        sns_action = cloudwatch_actions.SnsAction(alarm_topic)

        # CloudWatch metrics and alarms
        websites = [site["url"] for site in TARGET_WEBSITES]

        availability_metrics = []
        latency_metrics = []
        for index, website in enumerate(websites):

            # Availability metric
            availability_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Availability",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average",
            )

            # Latency metric
            latency_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Latency",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average",
            )

            availability_metrics.append(availability_metric)
            latency_metrics.append(latency_metric)

            # Availability alarm
            availability_alarm = availability_metric.create_alarm(
                self,
                f"AvailabilityAlarm{index}",
                threshold=1,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator
                    .LESS_THAN_THRESHOLD
                ),
            )
            availability_alarm.add_alarm_action(sns_action)

            # Latency alarm
            latency_alarm = latency_metric.create_alarm(
                self,
                f"LatencyAlarm{index}",
                threshold=2,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator
                    .GREATER_THAN_THRESHOLD
                ),
            )
            latency_alarm.add_alarm_action(sns_action)


        # Operational metrics and alarms for the crawler

        # Errors: the crawler crashed at least once
        errors_alarm = webhealth_alias.metric_errors(
            period=Duration.minutes(5),
        ).create_alarm(
            self,
            "CrawlerErrorsAlarm",
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Duration (time to process one crawler run): above 80% of the 30 s timeout
        duration_alarm = webhealth_alias.metric_duration(
            period=Duration.minutes(5),
            statistic="Maximum",
        ).create_alarm(
            self,
            "CrawlerDurationAlarm",
            threshold=24000,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Memory: percentage of the Lambda's memory used (from Lambda Insights)
        memory_metric = cloudwatch.Metric(
            namespace="LambdaInsights",
            metric_name="memory_utilization",
            dimensions_map={"function_name": webhealth_lambda.function_name},
            period=Duration.minutes(5),
            statistic="Maximum",
        )
        memory_alarm = memory_metric.create_alarm(
            self,
            "CrawlerMemoryAlarm",
            threshold=80,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Invocations: the crawler did not run at all in the last hour
        invocations_alarm = webhealth_lambda.metric_invocations(
            period=Duration.minutes(60),
        ).create_alarm(
            self,
            "CrawlerNotRunningAlarm",
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
        )

        for alarm in [errors_alarm, duration_alarm, memory_alarm, invocations_alarm]:
            alarm.add_alarm_action(sns_action)

        # Automatic rollback.
        # A new version gets 10% of traffic for 5 minutes. If the errors,
        # duration or memory alarm goes off, CodeDeploy moves the "live"
        # alias back to the last working version.
        if ENABLE_CODEDEPLOY_ROLLBACK:
            codedeploy.LambdaDeploymentGroup(
                self,
                "CrawlerDeploymentGroup",
                alias=webhealth_alias,
                deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
                alarms=[errors_alarm, duration_alarm, memory_alarm],
                auto_rollback=codedeploy.AutoRollbackConfig(
                    failed_deployment=True,
                    stopped_deployment=True,
                    deployment_in_alarm=True,
                ),
            )

        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name=dashboard_name,
        )

        # Availability graph
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Website Availability",
                left=availability_metrics,
                width=12,
                height=6,
                left_y_axis=cloudwatch.YAxisProps(
                    min=0,
                    max=1,
                ),
            )
        )

        # Latency graph
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Website Latency",
                left=latency_metrics,
                width=12,
                height=6,
            )
        )

        # Crawler health graphs
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Crawler Invocations and Errors",
                left=[
                    webhealth_lambda.metric_invocations(period=Duration.minutes(5)),
                    webhealth_lambda.metric_errors(period=Duration.minutes(5)),
                ],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Crawler Run Duration (ms)",
                left=[webhealth_lambda.metric_duration(period=Duration.minutes(5))],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Crawler Memory Used (%)",
                left=[memory_metric],
                width=8,
                height=6,
            ),
        )