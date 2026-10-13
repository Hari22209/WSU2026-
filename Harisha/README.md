# WebHealth – Website Monitoring Project

## Overview

WebHealth is a serverless application built using AWS CDK and Python. It checks whether websites are working and records their availability and response time.

Amazon EventBridge runs the monitoring Lambda function every 30 minutes. The function checks each website and sends the results to Amazon CloudWatch. If a website has a problem or takes too long to respond, CloudWatch alarms can send notifications through Amazon SNS.

The project also uses DynamoDB to store website targets and alarm information. A REST API allows users to add, view, update and delete websites.

## AWS Services Used

This project uses the following AWS services:

- AWS Lambda – runs the application code.
- Amazon EventBridge – schedules the website checks.
- Amazon API Gateway – provides the CRUD API.
- Amazon DynamoDB – stores website targets and alarm information.
- Amazon CloudWatch – records metrics and monitors website health.
- Amazon SNS – sends alarm notifications.
- AWS CodePipeline and CodeBuild – automate testing and deployment.
- AWS CloudFormation – creates the AWS resources.
- AWS IAM – manages permissions.
- AWS CDK – defines the infrastructure using Python.

## Website Monitoring

The monitoring function checks the website URL, HTTP status code, response time and availability.

For example, a successful website check may return:

```json
{
  "website": "https://www.westernsydney.edu.au/",
  "status_code": 200,
  "response_time": 0.421,
  "status": "UP"
}
```

If a website cannot be reached, it is recorded as `DOWN`, and its availability metric is set to `0`.

## CloudWatch Monitoring

The application publishes two metrics under the `WebHealth` namespace.

 Metric           Description 
'Availability'    Records 1 when a website is available and 0    when it is unavilable 
'Latency'.        Records the website response time in seconds.


### CloudWatch Alarms

The project includes availability and latency alarms. The availability alarm can trigger when the availability value falls below `1`. The latency alarm can trigger when the response time exceeds two seconds.

When an alarm is triggered, Amazon SNS sends notifications to the configured recipients and services.

### CloudWatch Dashboard

The dashboard displays graphs for website availability and latency. These graphs help users check website performance and identify problems.

## SNS Notifications and DynamoDB

Amazon SNS handles notifications from CloudWatch alarms. Depending on the configuration, notifications can be sent by email and passed to the alarm-logging Lambda function.

The alarm-logging function saves alarm information in the `AlarmInformationTable` DynamoDB table. The stored information includes the alarm ID, timestamp and alarm message.

## Website Management API

The project includes a REST API built with Amazon API Gateway, Python Lambda and DynamoDB. It allows users to manage the list of websites being monitored.

The available endpoints are:

 Method    Endpoint                  Purpose 

 POST     `/websites`                Add a website. 
 GET      `/websites`                View all websites. 
 GET      `/websites/{website_id}`   View one website. 
 PUT      `/websites/{website_id}`   Update a website URL. 
 DELETE   `/websites/{website_id}`   Remove a website. 

The API returns HTTP `404` when a requested website cannot be found. Invalid requests can return HTTP `400`.

More details about the endpoints and requests are available in [`docs/API.md`](docs/API.md).

### DynamoDB Read and Write Timing

The API also includes timing information in response headers for successful create and individual-read operations.

- `X-DynamoDB-Write-Time-Ms` measures the time around a DynamoDB write call.
- `X-DynamoDB-Read-Time-Ms` measures the time around a DynamoDB read call.

These measurements include AWS SDK and network overhead, so they do not represent only DynamoDB's internal processing time.

## Project Structure

 File or folder             Purpose 

 `harisha/harisha_stack.py`     Defines the main AWS resources. 
 `harisha/pipeline_stack.py`    Defines the deployment pipeline   and stages. 
`lambda/`                       Contains the Lambda function code. 
`tests/`                        Contains unit, functional and integration tests. 
 `docs/API.md`                  Explains the CRUD API. 

## Testing

Testing is used to check that the application works as expected.

- **Unit tests** check individual functions and CRUD logic.
- **Functional tests** check the application infrastructure and configuration.
- **Integration tests** check interactions with the deployed API and AWS services.

To run the unit and functional tests locally, use:

```bash
python -m pytest tests/test_unit.py tests/test_crud.py tests/functional -q
```

To run integration tests against a deployed stage, set the required `API_URL` and `WEBHEALTH_FUNCTION_NAME` environment variables and run:

```bash
python -m pytest tests/integration -v
```

Integration tests need the correct configuration and AWS credentials. They may be skipped if the required environment variables are missing.

## CI/CD Pipeline

The project uses AWS CodePipeline to automate testing and deployment. The pipeline includes Beta, Gamma and Prod stages.

The pipeline runs the configured build and tests, creates the CloudFormation template, deploys each stage and runs integration tests after deployment. This helps identify problems before the application moves through the deployment stages.

## Deployment

The project uses AWS CDK to define and deploy the infrastructure.

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Generate the CloudFormation template:

```bash
npx cdk synth
```

The pipeline normally handles deployment after changes are pushed to the configured source branch. Before deploying manually, check the AWS account, region and possible costs.

## Troubleshooting

If a website is reported as `DOWN`, the following checks can help:

1. Check the monitoring Lambda logs in CloudWatch Logs.
2. Check the website's CloudWatch metrics.
3. Review the related CloudWatch alarm.
4. Check the SNS notification.
5. Check the `AlarmInformationTable` for the alarm record.

## Known Limitations

- The CRUD API is public and does not include authentication unless additional protection has been configured.
- If alarms and dashboard graphs are configured for a fixed list of websites, newly added websites may not automatically receive their own alarms or dashboard graphs.
- Integration test results depend on the deployed environment, configuration and AWS credentials.

## GitHub

The project source code is maintained in GitHub. Changes can be committed and pushed using Git after the updated files have been checked and saved.
