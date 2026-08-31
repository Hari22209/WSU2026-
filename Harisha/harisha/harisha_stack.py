from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class HarishaStack(Stack):
    
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        
        super() .__init__(scope, construct_id, **kwargs)
        
        # WebHealth Lambda
        webhealth_lambda = lambda_.Function(
            self,
            "WebHealthLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
        )
        
        #Allow WebHealth Lambda to publish metrics to CloudWatch
        webhealth_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"],
            )
        )
        
        #Run WebHealth Lambda every 30 minutes
        schedule = events.Rule(
            self,
            "WebsiteMonitorSchedule",
            schedule=events.Schedule.rate(
            Duration.minutes(30)
        ),
        
        )
        
        schedule.add_target(
            targets.LambdaFunction(webhealth_lambda)
        )
        
        #Websites to monitor
        websites = [
            "https://www.westernsydney.edu.au/",
            "https://www.google.com/",
            "https://www.amazon.com/",
        ]
        
        
        availability_metrics = []
        latency_metrics = []
        
        
        #DynamoDB table for alarm GetSummaryInformation
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
        
        
        #Lambda for storing alarm information in DynamoDB
        fn_database = lambda_.Function(
            self,
            "AlarmDatabaseLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="database_logger.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": alarm_table.table_name
            },
        )
        
        #Give database Lambda permission to write to DynamoDB
        alarm_table.grant_write_data(fn_database)
        
        # SNS topic
        alarm_topic = sns.Topic(
            self,
            "alarmnotification",
            display_name="WebHealth Alarm Notifications",
            
        )
        
        # Email subscription
        alarm_topic.add_subscription(
            subscriptions.EmailSubscription(
                "22099290@westernsydney.edu.au"
            )
        )
        
        # Send SNS messages to database lambda
        alarm_topic.add_subscription(
            subscriptions.LambdaSubscription(
                fn_database
            )
        )
        
        #Create Cloudwatch metrics and alarms
        for index, website in enumerate(websites):
            
            #Availability metric
            availability_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Availability",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average",
            )
            
            # Latency metrics
            latency_metric = cloudwatch.Metric(
                namespace="WebHealth",
                metric_name="Latency",
                dimensions_map={
                    "Website": website
                },
                period=Duration.minutes(30),
                statistic="Average",
            )
            
            availability_metrics.append(
                availability_metric
            )
            
            latency_metrics.append(
                latency_metric
            )
            
            # Availability alarm
            availability_alarm = availability_metric.create_alarm(
                self,
                f"AvailabilityAlarm{index}",
                threshold=1,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
                ),
            )
            
            availability_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(
                    alarm_topic
                )
            )
            
            
            #Latency alarm
            latency_alarm = latency_metric.create_alarm(
                self,
                f"LatencyAlarm{index}",
                threshold=2,
                evaluation_periods=1,
                comparison_operator=(
                    cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD   
               ),
            ) 
            
            latency_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(
                    alarm_topic
                )
            )
            
            
        #CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name="WebHealthDashboard",
            
        ) 
        
        
        #Avalibility grapgh
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