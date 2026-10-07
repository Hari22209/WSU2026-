import os

os.environ.setdefault("TABLE_NAME", "test-table")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")

import os
import sys

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "lambda")
    )
)


import pytest
from unittest.mock import patch

SEED_TARGETS = [
    {"website_id": "1", "website": "https://www.westernsydney.edu.au/", "url": "https://www.westernsydney.edu.au/"},
    {"website_id": "2", "website": "https://www.google.com/", "url": "https://www.google.com/"},
    {"website_id": "3", "website": "https://www.amazon.com/", "url": "https://www.amazon.com/"},
]


@pytest.fixture(autouse=True)
def mock_targets_table():
    import lambda_function
    with patch.object(lambda_function, "table") as fake_table:
        fake_table.scan.return_value = {"Items": SEED_TARGETS}
        yield fake_table
