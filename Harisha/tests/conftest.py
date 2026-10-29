import os
import sys

os.environ.setdefault("TABLE_NAME", "test-table")
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Unit and functional tests must NEVER use my real AWS account, so they
# use fake keys instead of ~/.aws/credentials and work on any computer.
# Integration tests (API_URL is set) need the real AWS account, so they
# keep the real credentials.
if not os.environ.get("API_URL"):
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

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
    """UNIT tests: replace the crawler's table with a mock so the test checks
    ONLY my Python logic. Real DynamoDB behaviour is tested in
    tests/functional/test_dynamodb.py (moto) and tests/integration (real AWS)."""
    import lambda_function
    with patch.object(lambda_function, "table") as fake_table:
        fake_table.scan.return_value = {"Items": SEED_TARGETS}
        yield fake_table