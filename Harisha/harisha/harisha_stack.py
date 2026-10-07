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
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
)
from constructs import Construct


class HarishaStack(Stack):
    
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dashboard_name: str = "WebHealthDashboard",
        **kwargs
    ) -> None:
        
        super().__init__(scope, construct_id, **kwargs)
        
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
        
        
        # WebHealth monitoring Lambda
        webhealth_lambda = lambda_.Function(
            self,
            "WebHealthLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": target_table.table_name,
            },
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
            code=lambda_.Code.from_asset("lambda"),
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
        
        website_id_resource = websites_resource.add_resource(
            "{website_id}"
        )
        
        #POST /websites
        websites_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(crud_lambda),
        )
        
        # GET /websites
        websites_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(crud_lambda),
        )
           
        # GET /websites/{website_id},
        website_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(crud_lambda),
        )
        
         # PUT /websites/{website_id},
        website_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(crud_lambda),
        )
        
         # DELETE /websites/{website_id},
        website_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(crud_lambda),
        )
        
        CfnOutput(
            self,
            "WebHealthApiUrl",
            value=api.url,
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
            code=lambda_.Code.from_asset("lambda"),
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
        
        # Email subscription
        alarm_topic.add_subscription(
            subscriptions.EmailSubscription(
                "22099290@westernsydney.edu.au"
            )
        )
        
        # Send SNS messages to database lambda
        alarm_topic.add_subscription(
            subscriptions.LambdaSubscription(
                database_lambda
            )
        )
        # CloudWatch metrics and alarms
        websites = [
             "https://www.westernsydney.edu.au/",
            "https://www.google.com/",
            "https://www.amazon.com/",
        ]
        
        availability_metrics = []
        latency_metrics = []
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
                    cloudwatch.ComparisonOperator
                    .LESS_THAN_THRESHOLD
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
                    cloudwatch.ComparisonOperator
                    .GREATER_THAN_THRESHOLD   
               ),
            ) 
            
            latency_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(
                    alarm_topic
                )
            )
            
            
        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name=dashboard_name,
            
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