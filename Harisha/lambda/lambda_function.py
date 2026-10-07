import os
import urllib.request
import time
import boto3


dynamobd = boto3.resource("dynamodb")
cloudwatch = boto3.client("cloudwatch")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    result = table.scan()
    websites = result.get("Items",[])
    
    results = []
    
    for item in websites:
        url = item["url"]
        
        start_time = time.time()
        
        
        try:
            
            response = urllib.request.urlopen(
                url,
                timeout=10
            )
            
            response_time = round(
                time.time() - start_time,
                3
            )
            
            results.append({
                "website_id": item["website_id"],
                "website": url,
                "status_code": response.status,
                "response_time": response_time,
                "status": "UP",
            })
            
            cloudwatch.put_metric_data(
                Namespace="WebHealth",
                MetricData=[
                    {
                        
                        "MetricName": "Availability",
                        "Dimensions": [
                            {
                                
                                "Name": "Website",
                                "Value": url,
                            }
                        ],
                        "Value": 1,
                        "Unit": "Count",
                    },
                    {
                        
                        "MetricName": "Latency",
                        "Dimensions": [
                            {
                                
                                "Name": "Website",
                                "Value": url,
                                
                            }
                        ],
                        "Value": response_time,
                        "Unit": "Seconds",
                    },
                ],
            )
            
        except Exception as e:
        
            response_time = round(
                time.time() - start_time,
                3
            )  
        
            results.append({
                "website_id": item["website_id"],
                "website": url,
                "status_code": 0,
                "response_time": response_time,
                "status": "DOWN",
                "error": str(e)
            }) 
        
        
            cloudwatch.put_metric_data(
                Namespace="WebHealth",
                MetricData=[
                    {
                    
                        "MetricName": "Availability",
                        "Dimensions": [
                            {
                                "Name": "Website",
                                "Value": url,
                            }
                        ],
                        "Value": 0,
                        "Unit": "Count",
                    },
                    {
                        "MetricName": "Latency",
                        "Dimensions": [
                            {
                                
                                 "Name": "Website",
                                 "Value": url,
                                
                            }
                        ],
                        "Value": response_time,
                        "Unit": "Seconds",
                    },
                ],
                    
            )
              
            
    return {
        "statusCode":200,
        "results": results,
    
}    
                       