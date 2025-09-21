from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME", "mecaflow")
MONGO_URL = "mongodb+srv://islem:enpooran31@cluster0.yjykiin.mongodb.net/mecaflow"

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
courses_collection = db["courses"]
exercises_collection = db["exercises"]
submissions_collection = db["submissions"]

