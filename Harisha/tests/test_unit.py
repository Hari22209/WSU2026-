import json 
from unittest.mock import patch, MagicMock

from lambda_function import lambda_handler

    
            
def test_lambda_returns_success_status():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
            "lambda_function.cloudwatch.put_metric_data"
        ):
        
            result = lambda_handler({}, None)
            
    assert result["statusCode"] == 200
        
def test_lambda_returns_three_results():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
        ), patch(
            "lambda_function.cloudwatch.put_metric_data"
        ):
            
            result = lambda_handler({}, None)
            
    assert len(result["results"]) == 3

def test_successful_website_status_is_up():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
        
        result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert website["status"] == "UP"
        
def test_successful_response_has_status_code():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
         result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert website["status_code"] == 200
        

def test_response_time_is_number():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
         result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert isinstance(website["response_time"], (int, float))
        
def test_cloudwatch_metrics_are_published():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    )as mock_metrics:
        
        lambda_handler({}, None)
        
    assert mock_metrics.call_count == 3
    
    
def test_availability_metric_is_one_when_website_is_up():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    )as mock_metrics:
        
        lambda_handler({}, None)
        
        for call in mock_metrics.call_args_list:
            metric_data = call.kwargs["MetricData"]
            availabilty = metric_data[0]
            
            assert availabilty["MetricName"] == "Availability"
            assert availabilty["Value"] == 1
            
            
    
def test_latency_metric_is_published_in_seconds():
    mock_response = MagicMock()
    mock_response.status = 200
    
    with patch(
        "lambda_function.urllib.request.urlopen",
        return_value=mock_response
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    )as mock_metrics:
        
        lambda_handler({}, None)
        
        for call in mock_metrics.call_args_list:
                metric_data = call.kwargs["MetricData"]
                latency = metric_data[1]
            
        assert latency["MetricName"] == "Latency"
        assert latency["Unit"] == "Seconds"
            
            
def test_failed_webiste_status_is_down():
    with patch(
        "lambda_function.urllib.request.urlopen",
        side_effect=Exception("Website is unavailable")
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
         result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert website["status"] == "DOWN"
    
def test_availability_metric_is_zero_when_website_is_down():
    with patch(
        "lambda_function.urllib.request.urlopen",
        side_effect=Exception("Website is unavailable")
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ) as mock_metrics:
        
        lambda_handler({}, None)
        
    for call in mock_metrics.call_args_list:
            metric_data = call.kwargs["MetricData"]
            availabilty = metric_data[0]
            
            assert availabilty["MetricName"] == "Availability"
            assert availabilty["Value"] == 0
            
            
def test_down_website_has_status_code_zero():
    with patch(
        "lambda_function.urllib.request.urlopen",
        side_effect=Exception("Website is unavailable")
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
         result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert website["status_code"] == 0
        
def test_down_website_contains_error_message():
    with patch(
        "lambda_function.urllib.request.urlopen",
        side_effect=Exception("Website is unavailable")
    ), patch(
        "lambda_function.cloudwatch.put_metric_data"
    ):
         result = lambda_handler({}, None)
        
    for website in result["results"]:
        assert "error" in website 
        assert website["error"] == "Website is unavailable"
        

            
            
    
        
    
        
        

    
    
        
        

    
                   
    
    
    
          