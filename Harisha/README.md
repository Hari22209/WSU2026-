# Website Monitoring Lambda Project

## Overview

This project uses AWS CDK (Cloud Development Kit) to deploy a serverless website monitoring application on AWS.

An AWS Lambda function runs every 30 minutes using Amazon EventBridge. It checks the website status, HTTP response code and response time. CloudWatch monitors the website metrics, and SNS sends notifications when an alarm is triggered. Alarm information is also saved in DynamoDB.

The project also includes a CRUD API that allows users to add, view, update and delete website targets using Amazon API Gateway.


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

# CRUD API for Website Management

The application provides a REST API through Amazon API Gateway. The API uses a Python Lambda function to manage website targets stored in DynamoDB.

Users can create new website targets, view the website list, update website details and delete targets that are no longer needed.

# API Endpoints

Method    Endpoint                Purpose
POST      /websites               Add a website
GET       /websites               View the website list
GET       /websites/{website_id}  View one website
PUT       /websites/{website_id}  Update a website
DELETE    /websites/{website_id}  Delete a website

# Reading, Updating and Deleting Websites
Users can retrieve a website using its ID, update its URL or delete it from DynamoDB. If a website cannot be found, the API returns HTTP 404.

# DynamoDB Read and Write Timing
The API includes timing headers for successful create and individual read operations.

X-DynamoDB-Write-Time-Ms measures the time around the DynamoDB write call.
X-DynamoDB-Read-Time-Ms measures the time around the DynamoDB read call.

These timings include AWS SDK and network overhead, rather than measuring only DynamoDB's internal processing time.

## Infrastructure

The project is deployed using AWS CDK Infrastructure as Code (IaC).

Components created:

- Lambda function for website monitoring, alarm logging and website CRUD operations
- EventBridge scheduled rule (runs every 30 minutes)
- DynamoDB tables for website targets and alarm information
- API Gateway routes for CRUD operations
- CloudWatch metrics, alarms and dashboard
- SNS notification
- IAM roles and permission.#

## Deployment

Activate virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```
Generate the CloudFormation template:

```bash
npx cdk synth
```
Deploy the project using the appropriate CDK stack and AWS profile. for example, to deploy the Beta stack:

npx cdk deploy PipelineStack/Beta/HarishaStack --profile academy

Only deploy resources when required. Check the selected AWS account and enviroenment before running deployement commands.

# Running Tests

To run the complete test suite, use:

python -m pytest -v

The tests cover Lambda behaviour, CRUD operations, API Gateway configuration, DynamoDB timing headers and integration with the deployed API.

In the latest full test run, all 34 tests passed.

## Monitoring and Troubleshooting

if a website is reported as DOWN

check the website lambda in the AWS console
check the lambda logs in CloudWatch logs.
check the Website metrics in CloudWatch
check the related CloudWatch alarm.
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
