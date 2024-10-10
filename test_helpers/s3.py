from django.conf import settings

from api.documents.libraries.s3_operations import init_s3_client


class S3TesterHelper:
    def __init__(self):
        self.client = init_s3_client()
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        self.setup()

    def setup(self):
        self.client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={
                "LocationConstraint": settings.AWS_REGION,
            },
        )

    def _get_keys(self):
        objs = self.client.list_objects(Bucket=self.bucket_name)
        keys = [o["Key"] for o in objs.get("Contents", [])]
        return keys

    def get_object(self, s3_key):
        return self.client.get_object(Bucket=self.bucket_name, Key=s3_key)

    def add_test_file(self, key, body):
        return self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
        )

    def assert_file_in_s3(self, s3_key):
        assert s3_key in self._get_keys(), f"`{s3_key}` not found in S3"

    def assert_file_not_in_s3(self, s3_key):
        assert s3_key not in self._get_keys(), f"`{s3_key}` found in S3"

    def assert_file_body(self, s3_key, body):
        obj = self.client.get_object(
            Bucket=self.bucket_name,
            Key=s3_key,
        )
        assert obj["Body"].read() == body, f"`{s3_key}` body doesn't match"
