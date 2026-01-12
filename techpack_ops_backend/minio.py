import os
from minio import Minio


def get_minio_bucket_name()-> str:
    return os.getenv("MINIO_BUCKET")

def get_minio_client() -> Minio:
    client = Minio(
        os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
    bucket = get_minio_bucket_name()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    return client
