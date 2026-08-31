#!/usr/bin/env python3
import aws_cdk as cdk


from harisha.harisha_stack import HarishaStack

app = cdk.App()

HarishaStack(
    app,
    "HarishaStack",
)

app.synth()