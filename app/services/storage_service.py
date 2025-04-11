from google.cloud import storage
from datetime import timedelta

class StorageService:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def generate_upload_url(self, object_name: str, expiration: int = 15) -> str:
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expiration),
            method="PUT",
            content_type="video/mp4"
        )

    def delete_file(self, object_name: str) -> None:
        blob = self.client.bucket(self.bucket_name).blob(object_name)
        blob.delete()
        print(f"Deleted {file_name} from {bucket_name}")