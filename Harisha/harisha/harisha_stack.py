from aws_cdk import ( 
    Stack,
    aws_lambda as lambda_,
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
       