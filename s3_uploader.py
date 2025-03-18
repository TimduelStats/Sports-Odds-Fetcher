import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Read the list of existing buckets
def list_buckets():
    try:
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        if response:
            for bucket in response['Buckets']:
                print(f'Bucket: {bucket["Name"]}')
    except Exception as e:
        logger.error(e)
        return False
    return True

# Upload a file to S3
def upload_to_s3(file_path, bucket_name, object_name):
    try:
        s3 = boto3.client('s3')
        s3.upload_file(file_path, bucket_name, object_name)
    except Exception as e:
        logger.error(e)
        return False
    return True

# Delete file from S3
def delete_from_s3(bucket, key_name):
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket, Key=key_name)
    except Exception as e:
        logger.error(e)
        return False
    return True

# Get an object from a bucket
def get_object(bucket, key):
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket, Key=key)
        print(response)
        if response:
            return response['Body'].read()
    except Exception as e:
        logger.error(e)
        return False

# Download an object from a bucket
def download_object(bucket, key, file_path):
    try:
        s3 = boto3.client('s3')
        s3.download_file(bucket, key, file_path)
    except Exception as e:
        logger.error(e)
        return False
    return True

