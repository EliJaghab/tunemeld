export async function fetchFromMongoDB(collection: string, query: object, env: any): Promise<any[]> {
  const requestPayload = {
    dataSource: "tunemeld",
    database: "playlist_etl",
    collection,
    filter: query,
  };

  const url = `${env.MONGO_DATA_API_ENDPOINT}/action/find`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "api-key": env.MONGO_DATA_API_KEY,
      },
      body: JSON.stringify(requestPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch from MongoDB. Status: ${response.status}, Response: ${errorText}`);
    }

    const data = await response.json();
    return data.documents;
  } catch (error) {
    throw new Error(`Error fetching from MongoDB: ${error.message}`);
  }
}

export async function cacheAlbumCovers(tracks: any[]): Promise<void> {
  for (const track of tracks) {
    if (track.playlist_cover_url) {
      await cacheImage(track.playlist_cover_url);
    }
  }
}

async function cacheImage(url: string): Promise<void> {
  const cache = caches.default;
  let response = await cache.match(url);
  if (!response) {
    response = await fetch(url);
    if (response.ok) {
      await cache.put(url, response.clone());
    }
  }
}

export function createJsonResponse(data: any, cacheMaxAge: number = 3600): Response {
  return new Response(JSON.stringify(data), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": `public, max-age=${cacheMaxAge}, s-maxage=${cacheMaxAge * 2}`,
      Vary: "Accept-Encoding",
    },
  });
}

export function handleError(error: Error): Response {
  console.error("Error handling request:", error);
  return new Response(`Error: ${error.message}`, {
    status: 500,
    headers: { "Access-Control-Allow-Origin": "*" },
  });
}

export function handleOptions(request: Request): Response {
  const headers = new Headers();
  headers.append("Access-Control-Allow-Origin", "*");
  headers.append("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  headers.append("Access-Control-Allow-Headers", "Content-Type, api-key");
  return new Response(null, { headers });
}
