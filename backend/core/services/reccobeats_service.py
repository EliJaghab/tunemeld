import requests
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import get_logger

logger = get_logger(__name__)

RECCOBEATS_BASE_URL = "https://api.reccobeats.com/v1"


def fetch_reccobeats_track_id(spotify_id: str) -> str | None:
    """
    Lookup ReccoBeats track ID from Spotify ID with Cloudflare caching.
    Returns None if track not found in ReccoBeats.
    """
    cache_key = f"track_id:{spotify_id}"
    cached = cloudflare_cache_get(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key)
    if cached is not None:
        return cached if cached != "NOT_FOUND" else None

    try:
        response = requests.get(
            f"{RECCOBEATS_BASE_URL}/track?ids={spotify_id}",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("content") and len(data["content"]) > 0:
            reccobeats_id = str(data["content"][0]["id"])
            cloudflare_cache_set(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key, reccobeats_id)
            return reccobeats_id
        else:
            cloudflare_cache_set(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key, "NOT_FOUND")
            logger.info(f"Track not found in ReccoBeats: {spotify_id}")
            return None

    except Exception as e:
        logger.warning(f"ReccoBeats lookup failed for {spotify_id}: {e}")
        return None


def fetch_reccobeats_audio_features(spotify_id: str) -> dict | None:
    """
    Fetch audio features from ReccoBeats with Cloudflare caching.
    Returns None if track not found.

    Handles 2-step process:
    1. Lookup ReccoBeats ID from Spotify ID
    2. Fetch audio features from ReccoBeats ID
    """
    cache_key = f"audio_features:{spotify_id}"
    cached = cloudflare_cache_get(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key)
    if cached is not None:
        return cached if cached != "NOT_FOUND" else None

    reccobeats_id = fetch_reccobeats_track_id(spotify_id)
    if not reccobeats_id:
        cloudflare_cache_set(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key, "NOT_FOUND")
        return None

    try:
        response = requests.get(
            f"{RECCOBEATS_BASE_URL}/track/{reccobeats_id}/audio-features",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            cloudflare_cache_set(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key, "NOT_FOUND")
            return None

        features = {
            "danceability": data.get("danceability"),
            "energy": data.get("energy"),
            "valence": data.get("valence"),
            "acousticness": data.get("acousticness"),
            "instrumentalness": data.get("instrumentalness"),
            "speechiness": data.get("speechiness"),
            "liveness": data.get("liveness"),
            "tempo": data.get("tempo"),
            "loudness": data.get("loudness"),
        }

        cloudflare_cache_set(CachePrefix.RECCOBEATS_AUDIO_FEATURES, cache_key, features)
        return features

    except Exception as e:
        logger.warning(f"ReccoBeats audio features failed for {spotify_id}: {e}")
        return None
