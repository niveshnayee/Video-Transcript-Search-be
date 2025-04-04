from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
from pymongo import MongoClient


class MongoDBClient:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Get MongoDB credentials
        self.raw_username = os.getenv("MONGO_USERNAME")
        self.raw_password = os.getenv("MONGO_PASSWORD")
        self.database_name = os.getenv("DATABASE_NAME")

        # Validate credentials
        if not self.raw_username or not self.raw_password:
            raise ValueError("MONGO_USERNAME and MONGO_PASSWORD must be set in the environment variables.")

        # Escape credentials for use in the MongoDB URI
        self.escaped_username = quote_plus(self.raw_username)
        self.escaped_password = quote_plus(self.raw_password)

        # Build MongoDB URI
        self.mongodb_uri = f"mongodb+srv://{self.escaped_username}:{self.escaped_password}@vt-cluster.x2jzy.mongodb.net/{self.database_name}?retryWrites=true&w=majority"

        # Initialize MongoDB client
        self.client = MongoClient(self.mongodb_uri)

    def get_database(self):
        """Returns the database instance."""
        return self.client[self.database_name]

    def get_collection(self, collection_name):
        """Returns a specific collection from the database."""
        return self.get_database()[collection_name]