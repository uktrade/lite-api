## Running MinIO instead of using AWS S3

This describes how you can run the django app with MinIO instead of using AWS S3
Docker Compose to provide services like the database, elasticsearch and redis

- use following values in .env:
  - `AWS_ACCESS_KEY_ID=AKIAIEXAMPLE`
  - `AWS_SECRET_ACCESS_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
  - `AWS_STORAGE_BUCKET_NAME=lite-document-store-test`
  - `AWS_REGION=eu-west-2`
  - `S3_LOCAL_ENDPOINT_URL=http://lite-minio-s3:9000`
- With docker:
  - Start stack with docker: `docker-compose up`
- Without docker:
  - run local without docker: `docker-compose up -d redis db elasticsearch minio`
  - Run the application `pipenv run ./manage.py runserver 8100`

You can view the bucket on MinIO at `http://localhost:9000/minio/lite-document-store-test/`.
You will have to use above access key and secret to log into MinIO.
