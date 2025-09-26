from core.constants import ServiceName
from core.models import Genre, Service
from core.models.playlist import Rank, RawPlaylistData


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
