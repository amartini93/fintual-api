# Fintual
Desafío Fintual

## Description
Desafío para proceso de entrevista en Fintual

## Getting Started
### Dependencies
- Node.js 20.0.0
- Java Runtime Environment (JRE) 8 
- Python 3.10

### Installing locally
Create python virtual environment
```bash
python3.10 -m venv .venv
```

Activate python virtual environment
```bash
source .venv/bin/activate
```

Install requirements.txt in virtual environment (needs to be run from virtual environment)
```bash
pip install -r requirements.txt
```

Create the .env_config directory
```bash
mkdir -p .env_config
cp sample.env.json .env_config/dev.env.json
```

Install npm dependencies
```bash
npm install
```

Install DynamoDB (localhost:8000)
```bash
npx serverless dynamodb install -c serverless_dev.yml
```
If getting error to download dynamodb_local_latest.tar.gz:
Change protocol from http:// to https:// inside node_modules/dynamodb-localhost/dynamodb/config
Then http = require("https") inside node_modules/dynamodb-localhost/dynamodb/installer

### Linting
Run linting
```bash
flake8
```

### Executing project locally
Run docker to have SQS available
```bash
sudo docker run -p 9324:9324 softwaremill/elasticmq
```
In a DIFFERENT terminal, create de SQS queue
Might need to install AWS cli with sudo "snap install aws-cli --classic"
```bash
export AWS_ACCESS_KEY_ID=root
export AWS_SECRET_ACCESS_KEY=root
export AWS_REGION=us-west-2
aws --endpoint-url=http://localhost:9324 --region us-west-2 sqs create-queue --queue-name transactionQueue.fifo --attributes FifoQueue=true,ContentBasedDeduplication=true
aws --endpoint-url=http://localhost:9324 --region us-west-2 sqs create-queue --queue-name orderQueue.fifo --attributes FifoQueue=true,ContentBasedDeduplication=true
```
In the same terminal you created the queue, run serverless project offline for local debugging
```bash
npx serverless offline start -s dev -c serverless_dev.yml
```
