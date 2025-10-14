import numpy as np
from core.models.track import TrackFeatureModel, TrackModel


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
    Normalize audio features to 0-1 range.

    Tempo and loudness are scaled to match other features (0-1 range).
    """
    return np.array(
        [
            features["danceability"],
            features["energy"],
            features["valence"],
            features["acousticness"],
            features["instrumentalness"],
            features["speechiness"],
            features["liveness"],
            features["tempo"] / 250.0,  # Typical max tempo ~250 BPM
            (features["loudness"] + 60) / 60.0,  # Loudness range: -60 to 0 dB
        ]
    )


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two feature vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return float(dot_product / (norm1 * norm2))


def get_similar_tracks(
    isrc: str,
    limit: int = 10,
) -> list[dict[str, str | float]]:
    """
    Find tracks similar to the given track based on audio features using cosine similarity.

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
        similarity = cosine_similarity(source_vector, candidate_vector)
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
