from core.models import ServiceTrackModel, TrackModel
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db.models import Q

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Backfill YouTube URLs from CloudflareKV cache for tracks missing them"

    def handle(self, *args, **options):
        playlist_isrcs = set(ServiceTrackModel.objects.values_list("isrc", flat=True).distinct())
        missing_youtube = TrackModel.objects.filter(
            isrc__in=playlist_isrcs,
        ).filter(Q(youtube_url__isnull=True) | Q(youtube_url=""))

        total = missing_youtube.count()
        backfilled = 0
        cache_hits = 0

        logger.info(f"Found {total} tracks missing YouTube URLs")

        for track in missing_youtube:
            key_data = f"{track.track_name}|{track.artist_name}"
            cached_url = cloudflare_cache_get(CachePrefix.YOUTUBE_URL, key_data)

            if cached_url:
                cache_hits += 1
                track.youtube_url = cached_url
                track.save()
                backfilled += 1
                if backfilled % 50 == 0:
                    logger.info(f"Backfilled {backfilled}/{cache_hits} cached URLs...")

        logger.info(f"Backfill complete: {backfilled} YouTube URLs restored from cache")
        logger.info(f"Cache hits: {cache_hits}/{total} ({cache_hits / total * 100:.1f}%)")
        logger.info(f"Still missing: {total - backfilled}")
