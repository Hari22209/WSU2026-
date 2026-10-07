import os
import sys

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "lambda")
    )
)
