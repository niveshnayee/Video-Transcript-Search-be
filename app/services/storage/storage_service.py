import uuid
from typing import Tuple
import boto3
from botocore.client import Config
from app.config import r2_config
from app.constants import Constants
from app.utils.validation_utils import validate_file_extension, validate_file_size


class StorageService:
    def __init__(self, bucket_name: str = None) -> None:
        self.bucket_name = bucket_name or r2_config.bucket_name
        self.account_id = r2_config.account_id
        self.access_key = r2_config.access_key_id
        self.secret_key = r2_config.secret_access_key

        self.client = boto3.client(
            's3',
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version=Constants.signature_version)
        )

    def generate_presigned_url(self, file_name: str, file_size: int, expiration: int = Constants.presigned_url_expiration_minutes) -> Tuple[str, str]:
        validate_file_extension(file_name)
        validate_file_size(file_size)

        object_name = f"{uuid.uuid4().hex}_{file_name}"
        upload_url = self.client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': object_name,
                'ContentType': Constants.content_type_video
            },
            ExpiresIn=expiration * 60
        )
        return upload_url, object_name

    def delete_file(self, object_name: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=object_name)

    def get_file_size(self, object_name: str) -> int:
        response = self.client.head_object(Bucket=self.bucket_name, Key=object_name)
        return response['ContentLength']

    def get_total_size(self) -> int:
        total_size = 0
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_size += obj['Size']
        return total_size

    def download_file(self, object_name: str, dest_path: str) -> None:
        """Download an object from R2 to a local path.

        Streams the object content to avoid loading into memory.
        """
        response = self.client.get_object(Bucket=self.bucket_name, Key=object_name)
        body = response['Body']
        with open(dest_path, 'wb') as f:
            for chunk in iter(lambda: body.read(8192), b''):
                f.write(chunk)