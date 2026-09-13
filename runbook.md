WebHealth Monitoring Runbook

1. purpose 

this runbook wxplains how to monitor and troubleshoot the webhealth website monitoring system.

the system chceks websites every 30 minutes and records website availability and response time in Amazon CloudWatch 

2. Main Components

the webhealth system uses:

AWS Lambda
Amazon EventBridge
Amazon CloudWatch
CloudWatch Alarms
CloudWatch Alarms
CloudWatch Dashboard
Amazon SNS
Amazon DynamoDB

3. chheck Website monitoring 

open the AWS console
open Lambda
open the webhealthlambda function
check the latest function execution 
open cloudwatch logs and check for errors
check that the lambda is running every 30 minutes through eventbridge.

4. check clouwatch metrics

open cloudwatch then metrics and seletcs teh webhealth namespace.

check 
availability - 1 means the website is available and 0 means unavailable.

latency - webiste response time in seconds

the webhealthDashboard can also opened to view website avilability and latency graphs.

5. check cloudwatch alarms

if a website has a problem:

open cloudwatch then alarms
check the availability alarm.
check the latency alarm.
confirm whther the alarm is in alarm, ok, or insufficient_data state.

the availability alarm is triggered when availability is below 1.

the latency alarm is triggred when latency is greter than 2 seconds.

6. check SNS notifications

if an alarm is triggered 

open Amazon SNS
open the alarmnotification topic.
check the configured subscriptions.
check whether teh alarm notification was sent successfully.

7. check DynamoDB alarm Records 

alaram notifications are stored in teh alarminformationtable dynamodb table

check that the table contains:

alarm ID
timestamp
alarm message 

8. Troublshooting 

website is reported as Down 
check the wenhealth lambda function
check the lambda cloudwatch logs 
check the website URL.
check the cloudwatch availibility metric.
check the related cloudwatch alarm.
chcek SNS otification
check teh DynamoDB alarm record.

 ## website latency is too high 

 check the cloudwatch latency metric.
 check the latency alarm
 check the lambda logs
 check the website response time.

 ## alarm notification is not received
 check the cloudwatch alarm state
 check the SNS topic
 check the SNS subscription
 check whether the notifiaction was delivered.

 alarm information is not stored

 open the alarminformationtable
 check the database logging lambda
 check the lambda cloudwatch logs.check the SNS subscription to the database logging lambda.

 9. deployemnt 

Activate virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Synthesize CloudFormation template:

```bash
cdk synth
```

Deploy AWS resources:

```bash
cdk deploy
```

10. removing resources 

when the project is no longer required, resources can be removed using 

```bash
cdk destroy
```

