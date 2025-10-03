import hashlib
import json
from datetime import datetime
from typing import Any

from js import Response


def is_put_request(key: str | None, value: str | None) -> bool:
    return key is not None and value is not None


def is_get_request(key: str | None, value: str | None) -> bool:
    return key is not None and value is None


def create_response(
    data: dict[str, Any] | None = None,
    message: str | None = None,
    status: str = "success",
    status_code: int = 200,
) -> Response:
    return Response.new(
        json.dumps(
            {
                "status": status,
                "message": message,
                "data": data,
                "meta": {"timestamp": datetime.utcnow().isoformat()},
            }
        ),
        status_code=status_code,
        headers={"Content-Type": "application/json"},
    )


async def handle_put_request(env: Any, key: str, value: str) -> Response:
    await env.tunemeld_cache.put(key, value)
    return create_response(data={"key": key, "value": value}, message="Stored key-value pair successfully.")


async def handle_get_request(env: Any, key: str) -> Response:
    stored_value = await env.tunemeld_cache.get(key)
    if stored_value is not None:
        return create_response(data={"key": key, "value": stored_value}, message="Retrieved stored value.")
    else:
        return create_response(message="No value found for the provided key.", status="error", status_code=404)


async def handle_invalid_request() -> Response:
    return create_response(
        message="Invalid request. Provide 'key' parameter, and optionally a 'value' parameter.",
        status="error",
        status_code=400,
    )


async def handle_image_request(env: Any, isrc: str) -> Response:
    """Handle image serving requests for /api/image/{isrc}"""
    # Use same cache key format as Django: md5("album_cover_image:{isrc}")
    full_key = f"album_cover_image:{isrc}"
    cache_key = hashlib.md5(full_key.encode()).hexdigest()
    image_data = await env.tunemeld_cache.get(cache_key, "arrayBuffer")

    if image_data is not None:
        return Response.new(
            image_data,
            status_code=200,
            headers={
                "Content-Type": "image/jpeg",
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": f'"{isrc}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    else:
        return Response.new("Image not found", status_code=404)


async def on_fetch(request: Any, env: Any) -> Response:
    url = request.url
    path = url.split("?")[0]  # Remove query parameters
    path_parts = path.split("/")

    # Handle image serving: /api/image/{isrc}
    if len(path_parts) >= 4 and path_parts[-3] == "api" and path_parts[-2] == "image":
        isrc = path_parts[-1]
        if isrc:
            return await handle_image_request(env, isrc)
        return Response.new("Invalid ISRC", status_code=400)

    # Handle original KV API functionality
    key = request.query.get("key")
    value = request.query.get("value")

    if is_put_request(key, value):
        return await handle_put_request(env, key, value)
    elif is_get_request(key, value):
        return await handle_get_request(env, key)
    else:
        return await handle_invalid_request()
