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
        self.target_table = stack.target_table_output


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
                    # unit + functional tests block the pipeline before deploy
                    "python -m pytest -q tests/test_unit.py tests/test_crud.py tests/test_alarm_sync.py tests/functional",
                    "npm install -g aws-cdk",
                    "cdk synth",
                    "cp -R cdk.out ../cdk.out",
                ],
            ),
        )

        def test_step(stage, step_name, test_folder):
            """A CodeBuild step that runs one test folder against a deployed stage.
            If any test fails, the pipeline stops and the next stage never deploys."""
            return pipelines.CodeBuildStep(
                step_name,
                input=source,
                env_from_cfn_outputs={
                    "WEBHEALTH_FUNCTION_NAME": stage.function_name,
                    "API_URL": stage.api_url,
                    "TARGET_TABLE_NAME": stage.target_table,
                },
                role_policy_statements=[
                    iam.PolicyStatement(
                        actions=[
                            "lambda:InvokeFunction",
                            "cloudwatch:ListMetrics",
                            "dynamodb:GetItem",
                        ],
                        resources=["*"],
                    )
                ],
                commands=[
                    "cd Harisha",
                    "python -m pip install -r requirements.txt",
                    f"python -m pytest {test_folder} -q",
                ],
            )

        # Alpha: first deployment. A quick smoke test checks the API answers
        # and the target list was placed in DynamoDB.
        alpha = HarishaStage(self, "Alpha")
        pipeline.add_stage(
            alpha,
            post=[test_step(alpha, "AlphaSmokeTests", "tests/smoke")],
        )

        # Beta and Gamma: full integration tests against the real AWS resources.
        for name in ["Beta", "Gamma"]:
            stage = HarishaStage(self, name)
            pipeline.add_stage(
                stage,
                post=[test_step(stage, f"{name}IntegrationTests", "tests/integration")],
            )

        # Prod: a person must approve the release before production is changed.
        prod = HarishaStage(self, "Prod")
        pipeline.add_stage(
            prod,
            pre=[pipelines.ManualApprovalStep(
                "ReleaseToProduction",
                comment="Alpha, Beta and Gamma passed. Approve to deploy to Prod.",
            )],
            post=[test_step(prod, "ProdIntegrationTests", "tests/integration")],
        )