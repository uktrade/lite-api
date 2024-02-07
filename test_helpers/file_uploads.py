from django.conf import settings

from api.documents.libraries.s3_operations import init_s3_client


def upload_file(s3_key, content=b"test"):
    """
    Emulates how the frontend does file uploads by uploading to the processed
    S3 bucket.
    TODO: When we switch the frontend to uploading to the staged bucket instead,
    we should change that here.
    """
    s3 = init_s3_client()["processed"]
    s3.put_object(
        Bucket=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_STORAGE_BUCKET_NAME"],
        Key=s3_key,
        Body=content,
    )
