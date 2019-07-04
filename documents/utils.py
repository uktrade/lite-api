import boto3 as boto3
from django.conf import settings


class S3Wrapper(object):
    _s3_client = None

    @classmethod
    def get_client(cls):
        if not cls._s3_client:
            # logger.info('Instantiating S3 client')
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        return cls._s3_client


def s3_client():
    print("S3 CLIENT - USING", settings.S3_CLIENT)
    if settings.S3_CLIENT == 'boto3':
        return S3Wrapper.get_client()
    # else:
    #     # TODO: not yet there:
    #     return Minio(
    #         'localhost:9000',
    #         secure=True)
