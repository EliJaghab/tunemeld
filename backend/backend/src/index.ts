export default {
    async fetch(request: Request, env: any): Promise<Response> {
        const url = new URL(request.url);
        const pathname = url.pathname;

        if (pathname.startsWith('/api/')) {
            if (request.method === 'OPTIONS') {
                return handleOptions(request);
            }

            const cache = caches.default;
            let response = await cache.match(request);
            if (response) {
                return response;
            }

            try {
                const searchParams = url.searchParams;
                switch (pathname) {
                    case '/api/aggregated-playlist':
                        response = await handleAggregatedPlaylist(searchParams, env);
                        break;
                    case '/api/transformed-playlist':
                        response = await handleTransformedPlaylist(searchParams, env);
                        break;
                    case '/api/last-updated':
                        response = await handleLastUpdated(searchParams, env);
                        break;
                    default:
                        response = new Response('Not Found', {
                            status: 404,
                            headers: { 'Access-Control-Allow-Origin': '*' }
                        });
                }

                await cache.put(request, response.clone());
                return response;
            } catch (error) {
                console.error('Error handling request:', error);
                return new Response(`Error: ${error.message}`, {
                    status: 500,
                    headers: { 'Access-Control-Allow-Origin': '*' }
                });
            }
        }

        return fetch(request);
    },
};

function handleOptions(request: Request): Response {
    const headers = new Headers();
    headers.append('Access-Control-Allow-Origin', '*');
    headers.append('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    headers.append('Access-Control-Allow-Headers', 'Content-Type, api-key');
    return new Response(null, { headers });
}

async function fetchFromMongoDB(collection: string, query: object, env: any): Promise<any[]> {
    console.log('Fetching from MongoDB:', collection, query);

    const requestPayload = {
        dataSource: 'tunemeld',
        database: 'playlist_etl',
        collection,
        filter: query,
    };

    const url = `${env.MONGO_DATA_API_ENDPOINT}/action/find`;

    console.log('Request Payload:', requestPayload);

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'api-key': env.MONGO_DATA_API_KEY,
        },
        body: JSON.stringify(requestPayload),
    });

    console.log('MongoDB Response Status:', response.status);
    if (!response.ok) {
        throw new Error(`Failed to fetch from MongoDB. Status: ${response.status}`);
    }

    const data = await response.json();
    console.log('MongoDB Response Data:', data);
    return data.documents;
}

async function handleAggregatedPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    const data = await fetchFromMongoDB('aggregated_playlists', { genre_name: genre }, env);

    for (const track of data) {
        await cacheImage(track.album_cover_url);
    }

    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
}

async function handleTransformedPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    const service = searchParams.get('service');
    if (!genre || !service) {
        return new Response('Genre and service are required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    const data = await fetchFromMongoDB('transformed_playlists', { genre_name: genre, service_name: service }, env);

    // Cache album cover URLs
    for (const track of data) {
        await cacheImage(track.album_cover_url);
    }

    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
}

async function handleLastUpdated(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    const data = await fetchFromMongoDB('aggregated_playlists', { genre_name: genre }, env);
    if (data.length === 0) {
        return new Response('No data found for the specified genre', { status: 404, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    const lastUpdated = data[0].insert_timestamp;
    return new Response(JSON.stringify({ lastUpdated }), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
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
