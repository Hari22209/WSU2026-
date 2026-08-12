# Website Monitoring Lambda Project

## Overview

This project is a serverless website monitoring application developed using AWS CDK.

The application uses an AWS Lambda function to monitor multiple websites. The Lambda function reads a custom list of websites from a JSON configuration file, checks each website, records its availability and response latency, and publishes monitoring metrics to Amazon CloudWatch.

The application is scheduled to run automatically using Amazon EventBridge.

## Project Objectives

The main objectives of this project are:

- Build a serverless application using AWS Lambda.
- Use AWS CDK for Infrastructure as Code (IaC).
- Monitor multiple websites automatically.
- Store website URLs in a JSON configuration file.
- Measure website availability.
- Measure website response latency.
- Publish metrics to Amazon CloudWatch.
- Create CloudWatch dashboards for monitoring.
- Configure CloudWatch alarms for website health.
- Use Boto3 SDK to publish CloudWatch metrics.
- Manage the project using Git and GitHub.

## AWS Services Used

The project uses the following AWS services:

- AWS Lambda
- Amazon CloudWatch
- CloudWatch Metrics
- CloudWatch Dashboard
- CloudWatch Alarms
- Amazon EventBridge
- AWS IAM
- AWS CloudFormation
- AWS CDK


## Project Structure

- **app.py** – Entry point for the AWS CDK application.
- **cdk.json** – AWS CDK configuration file.
- **README.md** – Project documentation and instructions.
- **requirements.txt** – Python project dependencies.
- **requirements-dev.txt** – Development and testing dependencies.
- **harisha/** – Contains the AWS CDK infrastructure code.
- **harisha/harisha_stack.py** – Defines the AWS resources and infrastructure.
- **lambda/** – Contains the Lambda function code and configuration.
- **lambda/lambda_function.py** – Website monitoring Lambda function.
- **lambda/websites.json** – Contains the list of websites monitored by the application.
- **tests/** – Contains project tests.
- **tests/unit/test_harisha_stack.py** – Unit tests for the CDK stack.
- **.gitignore** – Specifies files that should not be tracked by Git.