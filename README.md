# WSU2026 – Harisha Udayakumar (22099290)

COMP2029 DevOps, Western Sydney University.

## Applied Project: WebHealth

My project is in the **[`Harisha`](Harisha/)** folder.

WebHealth checks whether websites are up and how fast they respond. The list of websites is stored in **Amazon DynamoDB**, and users manage it through a public **CRUD API** built with Amazon API Gateway and AWS Lambda. Everything is deployed with AWS CDK through a CodePipeline with Alpha, Beta, Gamma and Prod stages.

## Documents

- [Harisha/README.md](Harisha/README.md): architecture diagram, DynamoDB design, monitoring, alarms, pipeline, tests and setup
- [Harisha/docs/API.md](Harisha/docs/API.md): every API route with examples and status codes

## Main files

- `Harisha/harisha/harisha_stack.py`: DynamoDB tables, Lambdas, API Gateway, CloudWatch and SNS
- `Harisha/harisha/pipeline_stack.py`: CI/CD pipeline and test steps
- `Harisha/lambda/crud_lambda.py`: CRUD operations on DynamoDB
- `Harisha/lambda/lambda_function.py`: website checker (reads the list from DynamoDB)
- `Harisha/lambda/targets.json`: starting websites, loaded into DynamoDB on deploy
- `Harisha/tests/`: unit, functional, integration and smoke tests

## Quick check

```bash
curl https://wnq06hjc72.execute-api.ap-southeast-2.amazonaws.com/prod/websites
```
