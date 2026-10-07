import json
import os
import uuid

import boto3

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)

def response(status_code, body):
    return{
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }
    

def lambda_handler(event, context):
    method = event.get("httpMethod")
    path_parameters = event.get("pathParameters") or {}
    website_id = path_parameters.get("website_id")
    
    if method == "POST":
        return create_website(event)
    
    if method == "GET":
        if website_id:
            return get_website(website_id)
        return get_website()
    
    
    if method == "PUT":
        return update_website(event, website_id)
    
    if method == "DELETE":
        return delete_website(website_id)
    
    return response(
        405,
        {"error": "Method not allowed"}
    )
    
def create_website(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(
            400,
            {"error": "Invalid JSON"}
        )
    
    url = body.get("url")
    
    if not url:
        return response(
            400,
            {"error": "url is required"}
        )
        
    website_id = str(uuid.uuid4())
    
    item = {
        "website_id": website_id,
        "url": url
    }
    
    table.put_item(Item=item)
    
    return response(
        201,
        item
    )
    
def get_websites():
    result = table.scan()
    
    return response(
        200,
        {
            "websites": result.get("Items", [])
        }
    )
    
def get_website(website_id):
    result = table.get_item(
        Key={
            "website_id": website_id
        }
    )
    
    item = result.get("Item")
    
    if not item:
        return response(
            404,
            {"error": "Website not found"}
        )
        
        return response(
            200,
            item
        )
        
def update_website(event, website_id):
    if not website_id:
        return response(
            400,
            {"error": "website_id is required"}
        )
        
    try:
        body = json.loads(event(event.get("body") or "{}"))
    except json.JSONDecodeError:
        return response(
            400,
            {"error": "Invalid JSON"}
        )
        
    url = body.get("url")
    
    if not url:
        return response(
            400,
            {"error": "url is required"}
        )
    
    existing = table.get_item(
        Key={
            "website_id": website_id
        }
    )
    
    if "Item" not in existing:
        return response(
            404,
            {"error": "Website not found"}
        )
        
    result = table.update_item(
        Key={
            "website_id": website_id
        },
        UpdateExpression="SET #url = :url",
        ExpressionAttributesName={
            "#url": "url"
        },
        ExpressionAttributeValue={
            ":url": url
        },
        ReturnValues="ALL_NEW"
    )
    
    return response(
        200,
        result["Attributes"]
    )
    
def delete_website(website_id):
    if not website_id:
        return response(
            400,
            {"error": "website_id is required"}
        )
        
    result = table.delete_item(
        Key={
            "website_id": website_id
        },
        ReturnValues="ALL_OLD"
    )
    
    if "Attributes" not in result:
        return response(
            404,
             {"error": "Website not found"}
            
        )
        
    return response(
        200,
        {
            "message": "Website deleted",
            "website": result["Attributes"]
        }
    )
    
