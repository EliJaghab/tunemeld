import json
from datetime import datetime

from js import Response


def is_put_request(key, value):
    return key is not None and value is not None


def is_get_request(key, value):
    return key is not None and value is None


def create_response(data=None, message=None, status="success", status_code=200):
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


async def handle_put_request(env, key, value):
    await env.tunemeld_cache.put(key, value)
    return create_response(data={"key": key, "value": value}, message="Stored key-value pair successfully.")


async def handle_get_request(env, key):
    stored_value = await env.tunemeld_cache.get(key)
    if stored_value is not None:
        return create_response(data={"key": key, "value": stored_value}, message="Retrieved stored value.")
    else:
        return create_response(message="No value found for the provided key.", status="error", status_code=404)


async def handle_invalid_request():
    return create_response(
        message="Invalid request. Provide 'key' parameter, and optionally a 'value' parameter.",
        status="error",
        status_code=400,
    )


async def on_fetch(request, env):
    key = request.query.get("key")
    value = request.query.get("value")

    if is_put_request(key, value):
        return await handle_put_request(env, key, value)
    elif is_get_request(key, value):
        return await handle_get_request(env, key)
    else:
        return await handle_invalid_request()
