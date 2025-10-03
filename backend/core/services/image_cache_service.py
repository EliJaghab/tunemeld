import io

import httpx
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import get_logger
from PIL import Image

logger = get_logger(__name__)

TARGET_SIZE = (300, 300)
JPEG_QUALITY = 85


async def cache_image(image_url: str, isrc: str) -> str | None:
    """
    Cache an image in CloudFlare and return cached URL.

    Args:
        image_url: Original image URL to download and cache
        isrc: Track ISRC identifier for cache key and URL generation

    Returns:
        Relative URL to cached image if successful, None if failed
    """
    if not image_url or not isrc:
        return None

    # Check if already cached
    cached_data = cloudflare_cache_get(CachePrefix.ALBUM_COVER_IMAGE, isrc)
    if cached_data:
        from django.conf import settings

        # Use environment-specific worker URL
        return f"{settings.WORKER_BASE_URL}/api/image/{isrc}"

    try:
        # Download and optimize
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()

        if response.headers.get("content-type", "").startswith("image/"):
            optimized_data = _optimize_image(response.content)
            if optimized_data:
                cloudflare_cache_set(CachePrefix.ALBUM_COVER_IMAGE, isrc, optimized_data)
                from django.conf import settings

                # Use environment-specific worker URL
                return f"{settings.WORKER_BASE_URL}/api/image/{isrc}"

    except Exception as e:
        logger.error(f"Failed to cache image for ISRC {isrc}: {e}")

    return None


def _optimize_image(image_data: bytes) -> bytes | None:
    """Optimize image by resizing and compressing."""
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize and center
            img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
            final_img = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
            x = (TARGET_SIZE[0] - img.size[0]) // 2
            y = (TARGET_SIZE[1] - img.size[1]) // 2
            final_img.paste(img, (x, y))

            # Save optimized
            output = io.BytesIO()
            final_img.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return output.getvalue()

    except Exception as e:
        logger.error(f"Image optimization failed: {e}")
        return None
