from core.constants import ServiceName
from core.models import Genre, Service, ServiceTrack
from core.models.playlist import Playlist, Rank, RawPlaylistData


def get_service(name: str | ServiceName) -> Service | None:
    if isinstance(name, ServiceName):
        name = name.value
    try:
        return Service.objects.get(name=name)
    except Service.DoesNotExist:
        return None


def get_genre(name: str) -> Genre | None:
    try:
        return Genre.objects.get(name=name)
    except Genre.DoesNotExist:
        return None


def get_genre_by_id(genre_id: int) -> Genre | None:
    try:
        return Genre.objects.get(id=genre_id)
    except Genre.DoesNotExist:
        return None


def get_rank(name: str) -> Rank | None:
    try:
        return Rank.objects.get(name=name)
    except Rank.DoesNotExist:
        return None


def get_all_genres() -> list[Genre]:
    return list(Genre.objects.all())


def get_all_services() -> list[Service]:
    return list(Service.objects.all())


def get_raw_playlist_data_by_genre_service(genre_name: str, service_name: str) -> RawPlaylistData | None:
    genre_obj = get_genre(genre_name)
    service_obj = get_service(service_name)
    if not genre_obj or not service_obj:
        return None
    return RawPlaylistData.objects.filter(genre=genre_obj, service=service_obj).order_by("-id").first()


def is_track_seen_on_service(isrc: str, genre_name: str, service_name: ServiceName) -> bool:
    """Check if a track with given ISRC was seen on a specific service for a genre."""
    genre_obj = get_genre(genre_name)
    if not genre_obj:
        raise ValueError(f"Genre '{genre_name}' not found")

    return ServiceTrack.objects.filter(isrc=isrc, genre=genre_obj, service__name=service_name.value).exists()


def get_track_rank_by_track_object(track, genre_name: str, service_name: str) -> int | None:
    """Get track position using Track model object for any service playlist."""
    try:
        playlist_entry = (
            Playlist.objects.select_related("service_track")
            .filter(service_track__track=track, genre__name=genre_name, service__name=service_name)
            .order_by("position")
            .first()
        )
        return playlist_entry.position if playlist_entry else None
    except Exception:
        return None
