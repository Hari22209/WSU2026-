import json
import os
import uuid

import boto3

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)



def lambda_handler(event, context):
    alarm_id = str(uuid.uuid4())
        
    item ={
        "alarm_id": alarm_id,
        "alarm_message": json.dumps(event, default=str),
    }
        
    table.put_item(
        Item=item
        )
        
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Alarm information saved",
                "alarm_id": alarm_id,
         }
            
        ),
      
  }      
        