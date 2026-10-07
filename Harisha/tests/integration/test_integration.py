import json 
import os
import time

import boto3
import pytest

FUNCTION = os.environ.get("WEBHEALTH_FUNCTION_NAME")

pytestmark = pytest.mark.skipif(
    not FUNCTION,
    reason="WEBHEALTH_FUNCTION_NAME not set"
)

def invoke():
    response = boto3.client("lambda").invoke(
        FunctionName=FUNCTION
    )
    
    assert response["StatusCode"] ==200
    assert "FunctionError" not in response
    
    return json.loads(response["Payload"].read())

def test_deployed_lambda_checks_all_sites():
    payload = invoke()
    
    assert payload["statusCode"] == 200
    assert len(payload["results"]) == 3
    
def test_metrics_reach_cloudwatch():
    invoke()
    
    cloudwatch = boto3.client("cloudwatch")
    
    for _ in range(12):
        metrics = cloudwatch.list_metrics(
            Namespace="WebHealth",
            MetricName="Availability",
            Dimensions=[
                {
                    "Name": "Website",
                    "Value": "https://www.google.com/"
                }
            ],
            
        )["Metrics"]
        
        if metrics:
            return
        
        time.sleep(15)
        
    pytest.fail(
            "Availability metric not found in CloudWatch"
        )