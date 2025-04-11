from pymongo.collection import Collection
from bson import ObjectId

class VideoRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def save_video(self, video_data: dict):
        """Save video metadata to the database."""
        result = self.collection.insert_one(video_data)
        return str(result.inserted_id)

    def get_video(self, video_id: str) -> dict:
        """Retrieve video metadata by ID."""
        return self.collection.find_one({"_id": ObjectId(video_id)})

    def update_status(self, video_id: str, status: str):
        self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"status": status}}
        )

    def add_transcript(self, video_id: str, transcript: list):
        self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"transcript": transcript}}
        )
    
    def delete_video(self, video_id: str):
        self.collection.delete_one({"_id": ObjectId(video_id)})

    def get_all_videos(self):
        return list(self.collection.find())

    def get_transcript(self, video_id: str) -> dict:
        """Retrieve transcript by video ID."""
        return self.collection.find_one({"_id": ObjectId(video_id)})