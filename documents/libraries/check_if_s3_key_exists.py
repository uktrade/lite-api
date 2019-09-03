from boto3 import Session

from conf.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_REGION


def s3_key_exists(s3_key):
    session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION)
    s3 = session.resource('s3')
    bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
    s3_keys = [file.key for file in bucket.objects.all()]
    return s3_key in s3_keys
