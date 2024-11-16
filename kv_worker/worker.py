from js import Response


async def on_fetch(request, env):
    key = request.query.get("key")
    value = request.query.get("value")

    if key and value:
        await env.tunemeld_cache.put(key, value)
        return Response.new(f"Stored {key}: {value}")
    elif key:
        stored_value = await env.tunemeld_cache.get(key)
        if stored_value is not None:
            return Response.new(f"The stored value is: {stored_value}")
        else:
            return Response.new(f"No value found for key: {key}")
    else:
        return Response.new("Please provide a 'key' parameter, and optionally a 'value' parameter.")
