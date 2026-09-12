# Website Monitoring Lambda Project

## Overview

This project uses AWS CDK (Cloud Development Kit) to deploy a serverless website monitoring application.

An AWS Lambda function is triggered every 30 minutes using Amazon EventBridge. The Lambda function checks a web resource and records the website status, HTTP response code, and response time.

cloudWatch alrams monitor the website metrics. When an alarms threshold is reached, Amazon SNS sends a notification. Alarm information is also stored in Amazon DynamoDB.

## AWS Services Used

- AWS Lambda
- Amazon EventBridge
- AWS CloudWatch
- CloudWatch Alarms
- ClouWatch Dashboard
- Amazon SNS
- Amazon DynamoDB
- AWS CloudFormation
- AWS IAM
- AWS CDK

## Functionality

The Lambda function monitors:

- Website URL
- HTTP status code
- Response time
- Website availability status

Example output:

```json
{
  "website": "https://www.westernsydney.edu.au/",
  "status_code": 200,
  "response_time": 0.421,
  "status": "UP"
}
```
if a website cannot be reached, the application records it as DOWN and publishes an avalibility value of 0 to CloudWatch.

## CloudWatch Monitoring 

The Lambda function publishes two metrics to CloudWatch under the webHealth namespace.

Availability -1 when the website is available and 0 when it is unavailable.

Latency - the website response time measured in seconds.

## CloudWatch Alarms
ClouWatch alarms are configured for each monitored website.

## Availability Alarm

The Availability alarm is triggered when avalibility falls below 1.

## Latency Alarm

the latency alarm is triggered when latency is greter than 2 seconds.

Both alrms send notifications through the SNS topic.

## CloudWatch Dashboard 

A CloudWatch dashboard named webHealthDashboard is used to monitor website health.

## The dashboard contains

Website Availability graph 
Website Latency graph

## SNS notification

Amazon SNS is used to send notifications when Cloudwatch alarms are triggred.

## The SNS topic is used for:

Email notifications
sending alarm messages to the database logging Lambda 

## DynamoDB Alarm Logging 

Alarm notifications are sored in the AlarmInformationTable DynamoDB table

the database logging lambda stores 

Alarm ID 
Timestamp
Alarm message

## Infrastructure

The project is deployed using AWS CDK Infrastructure as Code (IaC).

Components created:

- Lambda function for website monitoring
- EventBridge scheduled rule (runs every 30 minutes)
- IAM role for Lambda permissions
- Alarm database Lambda function 
- ClouWatch metrics
- CloudWatch alarms
- CloudWatch dashboard
- SNS notification topic 
- DynamoDB alarm table
- IAM permissions

## Deployment

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

Destroy AWS resources after completing work:

```bash
cdk destroy
```

## Monitoring and Troubleshooting 

if a website is reported as DOWN 

check the webhealth lambda in the AWS console 
check the lambda logs in cloudwatch logs.
check the webhealth metrics in cloudwatch
check the realted cloudwatch alarm.
check the SNS notification
check the Dynamo table for the alarm record.

## Git Version Control

The project source code is managed using GitHub.

Changes can be committed using:

```bash
git add .
git commit -m "Update website monitoring project"
git push
```