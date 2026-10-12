from aws_cdk import (
    Stack,
    Stage,
    pipelines,
    SecretValue,
    aws_iam as iam,
)
from constructs import Construct

from harisha.harisha_stack import HarishaStack


class HarishaStage(Stage):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack = HarishaStack(
            self,
            "HarishaStack",
            dashboard_name=f"{construct_id}-WebHealthDashboard",
        )

        self.function_name = stack.function_name_output
        self.api_url = stack.api_url_output


class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.git_hub(
            "Hari22209/WSU2026-",
            "main",
            authentication=SecretValue.secrets_manager("github-token"),
        )

        pipeline = pipelines.CodePipeline(
            self,
            "WebHealthPipeline",
            pipeline_name="WebHealthPipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=source,
                commands=[
                    "cd Harisha",
                    "python -m pip install -r requirements.txt",
                    "python -m pytest -q tests/test_unit.py tests/test_crud.py",
                    "npm install -g aws-cdk",
                    "cdk synth",
                    "cp -R cdk.out ../cdk.out",
                ],
            ),
        )

        for name in ["Beta", "Gamma", "Prod"]:
            stage = HarishaStage(self, name)
            pipeline.add_stage(
                stage,
                post=[
                    pipelines.CodeBuildStep(
                        f"{name}IntegrationTests",
                        input=source,
                        env_from_cfn_outputs={
                            "WEBHEALTH_FUNCTION_NAME": stage.function_name,
                            "API_URL": stage.api_url,
                        },
                        role_policy_statements=[
                            iam.PolicyStatement(
                                actions=[
                                    "lambda:InvokeFunction",
                                    "cloudwatch:ListMetrics",
                                ],
                                resources=["*"],
                            )
                        ],
                        commands=[
                            "cd Harisha",
                            "python -m pip install -r requirements.txt",
                            "python -m pytest tests/integration -q",
                        ],
                    )
                ],
            )
