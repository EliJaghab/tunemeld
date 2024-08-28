from pymongo import MongoClient
from django.conf import settings

mongo_client = MongoClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB_NAME]

playlists_collection = mongo_db['view_counts_playlists']
track_views_collection = mongo_db['historical_track_views']
