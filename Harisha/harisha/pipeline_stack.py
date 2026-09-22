from aws_cdk import (
    Stack,
    Stage,
    pipelines,
    SecretValue,
)
from constructs import Construct

from harisha.harisha_stack import HarishaStack


class HarishaStage(Stage):
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        
        super().__init__(
            scope,
            construct_id,
            **kwargs
        )
        
        HarishaStack(
            self,
            "HarishaStack" ,
            dashboard_name=f"{construct_id}-WebHealthDashboard",
        )
        
class PipelineStack(Stack):
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        
        super().__init__(
            scope,
            construct_id,
            **kwargs
        )
        
        ##Github source
        source = pipelines.CodePipelineSource.git_hub(
            "Hari22209/WSU2026-",
            "main",
            authentication=SecretValue.secrets_manager(
                "github-token"
            ),
        )
        
        # pipeline
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
                    "npm install -g aws-cdk",
                    "cdk synth",
                ],
            ),
        )
        
        # Beta /Gamma Stage
        pipeline.add_stage(
            HarishaStage(
                self,
                "BetaGamma"
            )
        )
        
        # Production stage 
        pipeline.add_stage(
            HarishaStage(
                self,
                "Prod"
            )
        )