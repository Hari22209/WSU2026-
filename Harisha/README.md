# Website Monitoring Lambda Project

## Overview

This project uses AWS CDK (Cloud Development Kit) to deploy a serverless website monitoring application.

An AWS Lambda function is triggered every 30 minutes using Amazon EventBridge. The Lambda function checks a web resource and records the website status, HTTP response code, and response time.

## AWS Services Used

- AWS Lambda
- Amazon EventBridge
- AWS CloudFormation
- AWS IAM

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

## Infrastructure

The project is deployed using AWS CDK Infrastructure as Code (IaC).

Components created:

- Lambda function for website monitoring
- EventBridge scheduled rule (runs every 30 minutes)
- IAM role for Lambda permissions

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

## Git Version Control

The project source code is managed using GitHub.

Changes can be committed using:

```bash
git add .
git commit -m "Update website monitoring project"
git push
```