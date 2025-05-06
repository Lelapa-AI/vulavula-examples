import json
from processor import S3AudioProcessor

def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes audio files from S3.
    
    This function is triggered by AWS Lambda and initializes the S3AudioProcessor
    to transcribe audio files, translate them, and store the results.
    
    Args:
        event (dict): The event data passed to the Lambda function
        context (object): The runtime information provided by AWS Lambda
        
    Returns:
        dict: Response with status code and message
    """
    try:
        # Initialize the processor and run the processing pipeline
        processor = S3AudioProcessor()
        processor.run()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Audio processing completed successfully'
            })
        }
        
    except Exception as e:
        # Return error information if processing fails
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error processing call: {str(e)}'
            })
        }