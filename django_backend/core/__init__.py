from pymongo import MongoClient

from . import settings

default_app_config = "core.apps.CoreConfig"

# Initialize MongoDB client only if MONGO_URI is provided
mongo_client = None
mongo_db = None
transformed_playlists_collection = None
raw_playlists_collection = None
playlists_collection = None
historical_track_views = None

if settings.MONGO_URI:
    try:
        mongo_client = MongoClient(settings.MONGO_URI)
        mongo_db = mongo_client[settings.MONGO_DB_NAME]

        transformed_playlists_collection = mongo_db["transformed_playlists"]
        raw_playlists_collection = mongo_db["raw_playlists"]
        playlists_collection = mongo_db["view_counts_playlists"]
        historical_track_views = mongo_db["historical_track_views"]
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
        print("Django will continue without MongoDB functionality.")
