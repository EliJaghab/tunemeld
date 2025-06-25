from pymongo import MongoClient

from django_backend.core import settings

default_app_config = "core.apps.CoreConfig"

mongo_client = MongoClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB_NAME]

transformed_playlists_collection = mongo_db["transformed_playlists"]
raw_playlists_collection = mongo_db["raw_playlists"]
playlists_collection = mongo_db["view_counts_playlists"]
historical_track_views = mongo_db["historical_track_views"]
