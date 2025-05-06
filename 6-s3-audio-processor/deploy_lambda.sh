#!/bin/bash

# Configuration
FUNCTION_NAME="your-function-name"           # The name of your Lambda function
SOURCE_REGION=""                             # AWS region where source S3 bucket is located
DEST_REGION=""                               # AWS region where destination S3 bucket is located
SOURCE_BUCKET=""                             # S3 bucket containing the audio files to process
DEST_BUCKET=""                               # S3 bucket where processed results will be stored
TRANSCRIBE_ENDPOINT="https://vulavula-services.lelapa.ai/api/v2alpha/transcribe/sync/file"  # VulaVula transcription API endpoint
TRANSLATE_ENDPOINT="https://vulavula-services.lelapa.ai/api/v1/translate/process"           # VulaVula translation API endpoint
VULAVULA_API_KEY=""                          # Your VulaVula API key
CROSS_ACCOUNT_ROLE_ARN=""                    # ARN of the role for cross-account access to S3 buckets

# Create deployment package
echo "Creating deployment package..."
pip install -r requirements.txt --target ./package    # Install dependencies to a local directory
cp lambda_function.py processor.py ./package/         # Copy function code to the package
cd package
zip -r ../deployment.zip .                            # Create ZIP archive for Lambda deployment
cd ..

# Deploy Lambda function
echo "Deploying Lambda function..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://deployment.zip \
    
# Update environment variables
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment "Variables={
        SOURCE_BUCKET=$SOURCE_BUCKET,
        DEST_BUCKET=$DEST_BUCKET,
        SOURCE_REGION=$SOURCE_REGION,
        DEST_REGION=$DEST_REGION,
        TRANSCRIBE_ENDPOINT=$TRANSCRIBE_ENDPOINT,
        TRANSLATE_ENDPOINT=$TRANSLATE_ENDPOINT,
        CROSS_ACCOUNT_ROLE_ARN=$CROSS_ACCOUNT_ROLE_ARN,
        VULAVULA_API_KEY=$VULAVULA_API_KEY
    }" \

# Clean up
echo "Cleaning up..."
rm -rf package deployment.zip               # Remove temporary files

echo "Deployment complete!" 
