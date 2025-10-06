from datetime import datetime

from core.constants import GenreName, ServiceName
from core.models import GenreModel, ServiceModel, ServiceTrackModel
from core.models.playlist import PlaylistModel, RankModel, RawPlaylistDataModel
from core.models.track import TrackModel
from domain_types.types import Genre, Rank, RawPlaylistData, Service, Track


def get_service(name: ServiceName) -> Service | None:
    """Get service domain object by name."""
    try:
        django_service = ServiceModel.objects.get(name=name.value)
        return Service.from_django_model(django_service)
    except ServiceModel.DoesNotExist:
        return None


def get_genre(name: GenreName) -> Genre | None:
    """Get genre domain object by name."""
    try:
        django_genre = GenreModel.objects.get(name=name.value)
        return Genre.from_django_model(django_genre)
    except GenreModel.DoesNotExist:
        return None


def get_genre_by_id(genre_id: int) -> Genre | None:
    """Get genre domain object by ID."""
    try:
        django_genre = GenreModel.objects.get(id=genre_id)
        return Genre.from_django_model(django_genre)
    except GenreModel.DoesNotExist:
        return None


def get_track_by_isrc(isrc: str) -> Track | None:
    """Get track domain object by ISRC, returning the most recent one if multiple exist."""
    django_track = TrackModel.objects.filter(isrc=isrc).order_by("-id").first()
    if django_track:
        return Track.from_django_model(django_track)
    return None


def get_rank(name: str) -> Rank | None:
    """Get rank domain object by name."""
    try:
        django_rank = RankModel.objects.get(name=name)
        return Rank.from_django_model(django_rank)
    except RankModel.DoesNotExist:
        return None


def get_all_genres() -> list[Genre]:
    """Get all genre domain objects."""
    django_genres = GenreModel.objects.all()
    return [Genre.from_django_model(genre) for genre in django_genres]


def get_all_services() -> list[Service]:
    """Get all service domain objects."""
    django_services = ServiceModel.objects.all()
    return [Service.from_django_model(service) for service in django_services]


def get_all_ranks() -> list[Rank]:
    """Get all rank domain objects."""
    django_ranks = RankModel.objects.all().order_by("id")
    return [Rank.from_django_model(rank_model) for rank_model in django_ranks]


def get_raw_playlist_data_by_genre_service(genre_name: GenreName, service_name: ServiceName) -> RawPlaylistData | None:
    """Get raw playlist data domain object by genre and service."""
    try:
        django_genre = GenreModel.objects.get(name=genre_name.value)
        django_service = ServiceModel.objects.get(name=service_name.value)
    except (GenreModel.DoesNotExist, ServiceModel.DoesNotExist):
        return None

    django_raw_playlist = (
        RawPlaylistDataModel.objects.filter(genre=django_genre, service=django_service).order_by("-id").first()
    )
    if django_raw_playlist:
        return RawPlaylistData.from_django_model(django_raw_playlist)
    return None


def get_all_raw_playlist_data_by_genre(genre_name: GenreName) -> list[RawPlaylistData]:
    """Get all raw playlist data for a genre in a single optimized query."""
    try:
        django_genre = GenreModel.objects.get(name=genre_name.value)
    except GenreModel.DoesNotExist:
        return []

    # Get the latest raw playlist for each service in a single query
    raw_playlists = (
        RawPlaylistDataModel.objects.filter(genre=django_genre)
        .select_related("service")
        .order_by("service_id", "-id")
        .distinct("service_id")
    )

    return [RawPlaylistData.from_django_model(raw_playlist) for raw_playlist in raw_playlists]


def is_track_seen_on_service(isrc: str, genre_name: GenreName, service_name: ServiceName) -> bool:
    """Check if a track with given ISRC was seen on a specific service for a genre."""
    try:
        django_genre = GenreModel.objects.get(name=genre_name.value)
    except GenreModel.DoesNotExist as err:
        raise ValueError(f"Genre '{genre_name.value}' not found") from err

    return ServiceTrackModel.objects.filter(isrc=isrc, genre=django_genre, service__name=service_name.value).exists()


def get_track_rank_by_track_object(track: Track, genre_name: GenreName, service_name: ServiceName) -> int | None:
    """Get track position using Track domain object for any service playlist."""
    playlist_entry = (
        PlaylistModel.objects.filter(isrc=track.isrc, genre__name=genre_name.value, service__name=service_name.value)
        .order_by("position")
        .first()
    )
    return playlist_entry.position if playlist_entry else None


def get_playlist_tracks_by_genre_service(genre_name: GenreName, service_name: ServiceName) -> list[tuple[str, int]]:
    """Get list of (isrc, position) tuples for a genre/service playlist."""
    playlist_models = PlaylistModel.objects.filter(
        genre__name=genre_name.value, service__name=service_name.value
    ).order_by("position")
    return [(p.isrc, p.position) for p in playlist_models if p.isrc]


def get_tunemeld_playlist_updated_at(genre_name: GenreName) -> datetime | None:
    """Get the update timestamp of the TuneMeld playlist for a genre."""
    playlist_entry = (
        PlaylistModel.objects.filter(genre__name=genre_name.value, service__name=ServiceName.TUNEMELD.value)
        .select_related("service_track__track")
        .first()
    )

    if playlist_entry and playlist_entry.service_track and playlist_entry.service_track.track:
        return playlist_entry.service_track.track.updated_at

    return None


def get_tracks_by_isrcs(
    isrcs: list[str], genre: GenreName | None = None, service: ServiceName | None = None
) -> dict[str, Track]:
    """Batch fetch tracks by ISRCs in a single query. Returns dict mapping ISRC -> Track domain object.

    If genre and service are provided, tracks will be enriched with service sources, ranks, and button labels.
    This enrichment uses static service metadata and does NOT hit the database for service lookups.
    """
    if not isrcs:
        return {}

    django_tracks = TrackModel.objects.filter(isrc__in=isrcs).order_by("-id")

    isrc_to_track = {}
    for django_track in django_tracks:
        if django_track.isrc not in isrc_to_track:
            isrc_to_track[django_track.isrc] = Track.from_django_model(django_track, genre=genre, service=service)

    return isrc_to_track
