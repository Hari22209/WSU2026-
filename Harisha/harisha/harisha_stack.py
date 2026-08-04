from aws_cdk import ( 
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct 

class HarishaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        hello_lambda =lambda_.Function(
            self,
            "HelloLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler" ,
            code=lambda_.Code.from_asset("lambda")
        )
       
        # Remove Lambda when is destroyed
        hello_lambda.apply_removal_policy(
           RemovalPolicy.DESTROY
        )

        # Run Lambda every 30 minutes
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
