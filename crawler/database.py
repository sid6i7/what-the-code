import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.environ['MONGO_URI']

class Database:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient(uri)
        self.test_connection()
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def test_connection(self):
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
    
    def insert_page(self, page_data):
        """Insert a single page document into the MongoDB collection."""
        try:
            self.collection.insert_one(page_data)
        except Exception as e:
            print(f"Error inserting document: {e}")

    def insert_pages(self, pages_data):
        """Insert multiple page documents into the MongoDB collection."""
        try:
            self.collection.insert_many(pages_data)
        except Exception as e:
            print(f"Error inserting documents: {e}")

    def close(self):
        self.client.close()