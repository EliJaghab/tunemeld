from core.constants import ServiceName
from core.models import Genre, Service
from core.models.playlist import Rank, RawPlaylistData
from core.utils.utils import get_logger

logger = get_logger(__name__)


def get_service(name: str | ServiceName) -> Service | None:
    """Get the most recent Service by name, handling duplicates."""
    if isinstance(name, ServiceName):
        name = name.value

    service = Service.objects.filter(name=name).order_by("-id").first()
    if not service:
        logger.warning(f"Service not found: {name}")
    return service


def get_genre(name: str) -> Genre | None:
    """Get the most recent Genre by name, handling duplicates."""
    genre = Genre.objects.filter(name=name).order_by("-id").first()
    if not genre:
        logger.warning(f"Genre not found: {name}")
    return genre


def get_genre_by_id(genre_id: int) -> Genre | None:
    """Get the most recent Genre by ID, handling duplicates."""
    return Genre.objects.filter(id=genre_id).order_by("-id").first()


def get_rank(name: str) -> Rank | None:
    """Get the most recent Rank by name, handling duplicates."""
    return Rank.objects.filter(name=name).order_by("-id").first()


def get_or_create_service(name: str | ServiceName) -> tuple[Service, bool]:
    """Get or create a Service, always returning the most recent if duplicates exist."""
    if isinstance(name, ServiceName):
        name = name.value

    service = get_service(name)
    if service:
        return service, False

    service = Service.objects.create(name=name)
    return service, True


def get_or_create_genre(name: str) -> tuple[Genre, bool]:
    """Get or create a Genre, always returning the most recent if duplicates exist."""
    genre = get_genre(name)
    if genre:
        return genre, False

    genre = Genre.objects.create(name=name)
    return genre, True


def get_raw_playlist_data_by_genre_service(genre_name: str, service_name: str) -> RawPlaylistData | None:
    """Get the most recent RawPlaylistData by genre and service, handling duplicates."""
    genre_obj = get_genre(genre_name)
    service_obj = get_service(service_name)

    if not genre_obj or not service_obj:
        return None

    return RawPlaylistData.objects.filter(genre=genre_obj, service=service_obj).order_by("-id").first()
