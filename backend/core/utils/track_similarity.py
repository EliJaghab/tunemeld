import numpy as np
from core.models.track import TrackFeatureModel, TrackModel

FEATURE_WEIGHTS = {
    "danceability": 2.0,
    "energy": 2.0,
    "valence": 1.5,
    "acousticness": 1.0,
    "instrumentalness": 0.8,
    "speechiness": 0.8,
    "liveness": 0.5,
    "tempo": 1.2,
    "loudness": 1.0,
}


def extract_features(feature_model: TrackFeatureModel) -> dict[str, float]:
    """Extract audio features from TrackFeatureModel into a dict."""
    return {
        "danceability": feature_model.danceability,
        "energy": feature_model.energy,
        "valence": feature_model.valence,
        "acousticness": feature_model.acousticness,
        "instrumentalness": feature_model.instrumentalness,
        "speechiness": feature_model.speechiness,
        "liveness": feature_model.liveness,
        "tempo": feature_model.tempo,
        "loudness": feature_model.loudness,
    }


def normalize_features(features: dict[str, float]) -> np.ndarray:
    """
    Normalize audio features to 0-1 range with feature weighting.

    Tempo and loudness are scaled to match other features (0-1 range),
    then all features are weighted based on their importance.
    """
    normalized = np.array(
        [
            features["danceability"] * FEATURE_WEIGHTS["danceability"],
            features["energy"] * FEATURE_WEIGHTS["energy"],
            features["valence"] * FEATURE_WEIGHTS["valence"],
            features["acousticness"] * FEATURE_WEIGHTS["acousticness"],
            features["instrumentalness"] * FEATURE_WEIGHTS["instrumentalness"],
            features["speechiness"] * FEATURE_WEIGHTS["speechiness"],
            features["liveness"] * FEATURE_WEIGHTS["liveness"],
            (features["tempo"] / 250.0) * FEATURE_WEIGHTS["tempo"],
            ((features["loudness"] + 60) / 60.0) * FEATURE_WEIGHTS["loudness"],
        ]
    )
    return normalized


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two feature vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate Euclidean distance between two feature vectors."""
    return float(np.linalg.norm(vec1 - vec2))


def hybrid_similarity(
    vec1: np.ndarray,
    vec2: np.ndarray,
    cosine_weight: float = 0.6,
    distance_weight: float = 0.4,
) -> float:
    """
    Calculate hybrid similarity combining cosine similarity and Euclidean distance.

    Higher score = more similar
    """
    cos_sim = cosine_similarity(vec1, vec2)
    eucl_dist = euclidean_distance(vec1, vec2)

    max_dist = 10.0
    normalized_dist = min(eucl_dist / max_dist, 1.0)
    distance_similarity = 1.0 - normalized_dist

    return (cosine_weight * cos_sim) + (distance_weight * distance_similarity)


def get_similar_tracks(
    isrc: str,
    limit: int = 10,
) -> list[dict[str, str | float]]:
    """
    Find tracks similar to the given track based on audio features.

    Pure audio feature matching - no genre filtering to encourage cross-genre discovery.

    Args:
        isrc: The ISRC of the source track
        limit: Maximum number of similar tracks to return

    Returns:
        List of dicts with track info and similarity score, sorted by similarity
    """
    try:
        source_feature = TrackFeatureModel.objects.get(isrc=isrc)
    except TrackFeatureModel.DoesNotExist:
        return []

    source_features_dict = extract_features(source_feature)
    source_vector = normalize_features(source_features_dict)

    all_features = TrackFeatureModel.objects.exclude(isrc=isrc).select_related()
    similarities: list[tuple[str, float]] = []

    for feature in all_features:
        candidate_features_dict = extract_features(feature)
        candidate_vector = normalize_features(candidate_features_dict)
        similarity = hybrid_similarity(source_vector, candidate_vector)
        similarities.append((feature.isrc, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    top_similar = similarities[:limit]

    results: list[dict[str, str | float]] = []
    for similar_isrc, similarity_score in top_similar:
        try:
            track = TrackModel.objects.get(isrc=similar_isrc)
            results.append(
                {
                    "isrc": similar_isrc,
                    "track_name": track.track_name,
                    "artist_name": track.artist_name,
                    "similarity_score": round(similarity_score, 4),
                }
            )
        except TrackModel.DoesNotExist:
            continue

    return results
