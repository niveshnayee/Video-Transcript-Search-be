from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from app.config import app_config


class MongoDBClient:
    def __init__(self) -> None:
        self.database_name: str = app_config.database_name
        escaped_username = quote_plus(app_config.mongo_username)
        escaped_password = quote_plus(app_config.mongo_password)
        self.mongodb_uri: str = (
            f"mongodb+srv://{escaped_username}:{escaped_password}"
            f"@vt-cluster.x2jzy.mongodb.net/{self.database_name}"
            "?retryWrites=true&w=majority"
        )
        self.client: MongoClient = MongoClient(self.mongodb_uri)

    def get_database(self) -> Database:
        """Returns the database instance."""
        return self.client[self.database_name]

    def get_collection(self, collection_name: str) -> Collection:
        """Returns a specific collection from the database."""
        return self.get_database()[collection_name]
