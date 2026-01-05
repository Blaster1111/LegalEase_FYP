# db.py
from pymongo import MongoClient
from config import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DB_NAME]

users_col = db["users"]
documents_col = db["documents"]
chats_col = db["chats"]

users_col.create_index("email", unique=True)
