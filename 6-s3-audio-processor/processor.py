#processor.py
import boto3
import json
import os
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Mapping between transcription language codes and translation language codes
transcribe_to_translate_map = {
    "eng": "eng_Latn",  # RSA English
    "afr": "afr_Latn",  # Afrikaans
    "zul": "zul_Latn",  # isiZulu
    "sot": "sot_Latn",  # Sesotho (Southern Sotho)
}


class S3AudioProcessor:
    """
    A class that processes audio files stored in an S3 bucket by:
    1. Finding audio files that haven't been processed yet
    2. Transcribing them using VulaVula's transcription API
    3. Translating the transcription using VulaVula's translation API
    4. Storing the results in a destination S3 bucket
    """
    
    def __init__(self):
        """
        Initialize the S3AudioProcessor with environment variables and AWS clients.
        Sets up cross-account access to S3 buckets if needed.
        """
        # Load configuration from environment variables
        self.transcribe_endpoint = os.environ["TRANSCRIBE_ENDPOINT"]
        self.translate_endpoint = os.environ["TRANSLATE_ENDPOINT"]
        self.api_key = os.environ["VULAVULA_API_KEY"]
        self.cross_account_role_arn = os.environ["CROSS_ACCOUNT_ROLE_ARN"]
        self.source_bucket = os.environ["SOURCE_BUCKET"]
        self.dest_bucket = os.environ["DEST_BUCKET"]

        # Create S3 clients with assumed role credentials for cross-account access
        if self.cross_account_role_arn:
            creds = self.assume_cross_account_role("LambdaSession")
            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
            )
        else:
            session = boto3.Session()

        # Initialize S3 clients for source and destination regions
        self.source_s3 = session.client("s3", region_name=os.environ["SOURCE_REGION"])
        self.dest_s3 = session.client("s3", region_name=os.environ["DEST_REGION"])

    def assume_cross_account_role(self, session_name: str):
        """
        Assume a cross-account IAM role to access resources in different AWS accounts.
        
        Args:
            session_name (str): Name for the temporary session
            
        Returns:
            dict: Credentials for the assumed role
        """
        sts_client = boto3.client("sts", region_name=os.environ["DEST_REGION"])
        assumed_role = sts_client.assume_role(
            RoleArn=self.cross_account_role_arn, RoleSessionName=session_name
        )
        return assumed_role["Credentials"]

    def get_recent_files(self) -> list[str]:
        """
        Find audio files in the source bucket that haven't been processed yet.
        
        Returns:
            list[str]: List of S3 keys for unprocessed audio files
        """
        try:
            # Get all audio files from source bucket
            print("Fetching audio files from source bucket...")
            source_response = self.source_s3.list_objects_v2(Bucket=self.source_bucket)
            audio_files = [
                obj["Key"]
                for obj in source_response.get("Contents", [])
                if obj["Key"].endswith((".opus", ".mp3", ".wav"))
            ]
            
            # Get all transcription files from destination bucket
            print("Fetching transcription files from destination bucket...")
            dest_response = self.dest_s3.list_objects_v2(Bucket=self.dest_bucket)
            transcribed_files = {
                obj["Key"].replace(".json", "")
                for obj in dest_response.get("Contents", [])
                if obj["Key"].endswith(".json")
            }
            
            # Filter out already transcribed files
            print("Filtering out already transcribed files...")
            new_files = []
            for audio_file in audio_files:
                conversation_id = audio_file.split("conversation_id=")[-1].strip("/")
                if conversation_id not in transcribed_files:
                    new_files.append(audio_file)

            print(
                f"Found {len(new_files)} new files to process out of {len(audio_files)} total files"
            )
            return new_files

        except ClientError as e:
            print(f"Error listing files: {str(e)}")
            raise

    def transcribe_audio(self, s3_key: str) -> dict:
        """
        Transcribe an audio file using VulaVula's transcription API.
        
        Args:
            s3_key (str): S3 key of the audio file to transcribe
            
        Returns:
            dict: Transcription result from VulaVula
        """
        try:
            # Get the audio file from S3 using assumed role credentials
            response = self.source_s3.get_object(Bucket=self.source_bucket, Key=s3_key)
            audio_content = response["Body"].read()
            
            # Set transcription parameters
            params = {
                "lang_code": "eng",  # Default language code (English)
                "diarise": 1,        # Enable speaker diarization
                "music": 1,          # Enable music detection
            }

            # Call VulaVula transcription endpoint
            response = requests.post(
                self.transcribe_endpoint,
                files={"file": ("audio.wav", audio_content, "audio/wav")},
                headers={
                    "X-CLIENT-TOKEN": self.api_key,
                },
                params=params
            )

            if response.status_code != 200:
                raise Exception(
                    f"Transcription failed with status {response.status_code}, response: {response}"
                )

            return response.json()

        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            raise

    def translate_text(self, text: str, language_code: str) -> dict:
        """
        Translate text using VulaVula's translation API.
        
        Args:
            text (str): Text to translate
            language_code (str): Source language code
            
        Returns:
            dict: Translation result from VulaVula
        """
        try:
            # Map the transcription language code to translation language code
            source_lang = transcribe_to_translate_map[language_code]
            
            # Call VulaVula translation endpoint
            response = requests.post(
                self.translate_endpoint,
                json={
                    "input_text": text,
                    "source_lang": source_lang,
                    "target_lang": "eng_Latn",  # Always translate to English
                },
                headers={
                    "Content-Type": "application/json",
                    "X-CLIENT-TOKEN": self.api_key,
                },
            )
            if response.status_code != 200:
                raise Exception(
                    f"Translation failed with status {response.status_code}"
                )

            return response.json()
        except Exception as e:
            print(f"Error in translation: {str(e)}")
            raise

    def process_call(self, s3_key: str):
        """
        Process a single audio file: transcribe, translate, and store results.
        
        Args:
            s3_key (str): S3 key of the audio file to process
        """
        try:
            print(f"Processing {s3_key}")
            
            # Step 1: Transcribe the audio file
            transcription = self.transcribe_audio(s3_key)
            if transcription["transcription_status"] == "FAILED":
                raise Exception(f"Transcription failed with error  {transcription}")
            print("Transcription successful!")
            
            # Step 2: Translate the transcription text
            translation = self.translate_text(
                transcription["transcription_text"], transcription["language_code"]
            )
            print("Translation successful!")
            
            # Extract conversation ID from the S3 key
            conversation_id = s3_key.split("conversation_id=")[-1].strip("/")
            
            # Prepare the final result object
            result = {
                "conversation_id": conversation_id,
                "transcription": transcription,
                "translation": translation,
            }
            
            # Step 3: Upload result to destination bucket
            self.dest_s3.put_object(
                Bucket=self.dest_bucket,
                Key=f"{conversation_id}.json",
                Body=json.dumps(result),
                ContentType="application/json",
            )
            print(f"Uploaded {conversation_id}.json to destination bucket.")

        except Exception as e:
            print(f"Error processing {e}")

    def run(self):
        """
        Main processing method that finds and processes all unprocessed audio files.
        """
        # Get list of files that need processing
        files = self.get_recent_files()
        
        # Process each file
        for f in files:
            self.process_call(f)


if __name__ == "__main__":
    # Allow the script to be run directly for testing
    processor = S3AudioProcessor()
    processor.run()
