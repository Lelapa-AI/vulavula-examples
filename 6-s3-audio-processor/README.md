# S3 Audio Processor

This AWS Lambda function processes audio files stored in an S3 bucket by transcribing them with VulaVula's transcription API, translating the transcription with VulaVula's translation API, and storing the results in a destination S3 bucket.

## Overview

The S3 Audio Processor is designed for batch processing of audio calls stored in S3. It:

1. Scans a source S3 bucket for unprocessed audio files (.mp3, .wav, .opus)
2. Transcribes the audio using Vulavula's transcription API.
3. Translates the transcribed text to English
4. Stores the combined results (transcription + translation) in a destination S3 bucket

The Lambda function can be set up to run on a schedule or triggered by S3 events.

## Requirements

- AWS account with Lambda and S3 access
- VulaVula API key (from [lelapa.ai](https://platform.lelapa.ai))
- Python 3.8+
- Required Python packages (included in requirements.txt):
  - boto3
  - requests
  - python-dotenv (for local development)

## File Structure

- `deploy_lambda.sh`: Deployment script for the Lambda function
- `lambda_function.py`: AWS Lambda handler
- `processor.py`: Main processing logic
- `requirements.txt`: Python dependencies

## Setup & Deployment

### 1. Configure the deployment script

Edit `deploy_lambda.sh` and set the following variables:

```sh
FUNCTION_NAME="your-function-name"    # Name of your Lambda function
SOURCE_REGION="us-east-1"             # Region of source S3 bucket
DEST_REGION="us-east-1"               # Region of destination S3 bucket
SOURCE_BUCKET="source-bucket-name"    # Bucket containing audio files
DEST_BUCKET="dest-bucket-name"        # Bucket to store results
VULAVULA_API_KEY="your-api-key"       # Your VulaVula API key
CROSS_ACCOUNT_ROLE_ARN="arn:aws:iam::account-id:role/role-name"  # If buckets are in different accounts
```

### 2. Create the Lambda function (if it doesn't exist)

```sh
aws lambda create-function \
    --function-name your-function-name \
    --runtime python3.9 \
    --handler lambda_function.lambda_handler \
    --role arn:aws:iam::account-id:role/lambda-execution-role \
    --timeout 300 \
    --memory-size 512
```

### 3. Deploy the Lambda function

```sh
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

### 4. Set up Lambda triggers (optional)

You can set up the Lambda function to:

- Run on a schedule using CloudWatch Events
- Trigger when new files are uploaded to the source S3 bucket

## Cross-Account S3 Access

If your source and destination S3 buckets are in different AWS accounts, you'll need to:

1. Create an IAM role in the account with the S3 buckets
2. Configure trust relationships to allow the Lambda function to assume this role
3. Provide the ARN of this role in the `CROSS_ACCOUNT_ROLE_ARN` variable

## IAM Permissions

The Lambda function requires the following permissions:

- `s3:GetObject` on the source bucket
- `s3:PutObject` on the destination bucket
- `sts:AssumeRole` for using cross-account access

## Input/Output Format

### Input

Audio files in the source bucket should have a naming convention that includes the conversation ID:
```
path/to/file/conversation_id=12345.mp3
```

### Output

The processed results are stored as JSON files in the destination bucket:
```
12345.json
```

The JSON structure includes:

```json
{
  "conversation_id": "12345",
  "transcription": {
    "transcription_text": "...",
    "language_code": "eng",
    "transcription_status": "COMPLETED",
    ...
  },
  "translation": {
    "translated_text": "...",
    ...
  }
}
```

## Language Support

The processor currently supports the following languages:

- English (eng)
- Afrikaans (afr)
- isiZulu (zul)
- Sesotho/Southern Sotho (sot)

## Local Development and Testing

For local testing, create a `.env` file with the required environment variables:

```
SOURCE_BUCKET=source-bucket-name
DEST_BUCKET=dest-bucket-name
SOURCE_REGION=us-east-1
DEST_REGION=us-east-1
TRANSCRIBE_ENDPOINT=https://vulavula-services.lelapa.ai/api/v2alpha/transcribe/sync/file
TRANSLATE_ENDPOINT=https://vulavula-services.lelapa.ai/api/v1/translate/process
CROSS_ACCOUNT_ROLE_ARN=arn:aws:iam::account-id:role/role-name
VULAVULA_API_KEY=your-api-key
```

Then run the processor directly:

```sh
python processor.py
```

## Troubleshooting

- **"Access Denied" errors**: Check IAM permissions and cross-account role configuration
- **Timeout errors**: Increase Lambda timeout if processing large audio files
- **Memory errors**: Increase Lambda memory allocation