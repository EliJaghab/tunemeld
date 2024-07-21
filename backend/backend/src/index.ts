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
                    case '/api/service-playlist':
                        response = await handleServicePlaylist(searchParams, env);
                        break;
                    case '/api/main-playlist':
                        response = await handleMainPlaylist(searchParams, env);
                        break;
                    case '/api/last-updated':
                        response = await handleLastUpdated(searchParams, env);
                        break;
                    case '/api/header-art':
                        response = await handleHeaderArt(searchParams, env);
                        break;
                    default:
                        response = new Response('Not Found', {
                            status: 404,
                            headers: { 'Access-Control-Allow-Origin': '*' }
                        });
                }
                
                if (response.status === 200) {
                    await cache.put(request, response.clone());
                }

                return response;
            } catch (error) {
                return handleError(error);
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
    const requestPayload = {
        dataSource: 'tunemeld',
        database: 'playlist_etl',
        collection,
        filter: query,
    };

    const url = `${env.MONGO_DATA_API_ENDPOINT}/action/find`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'api-key': env.MONGO_DATA_API_KEY,
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

async function handleHeaderArt(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const data = await fetchFromMongoDB('raw_playlists', { genre_name: genre }, env);
        const formattedData = formatPlaylistData(data);

        // Cache images
        await cacheAlbumCovers(Object.values(formattedData));

        return createJsonResponse(formattedData);
    } catch (error) {
        return handleError(error);
    }
}

function formatPlaylistData(data: any[]): any {
    const result: any = {};

    data.forEach(item => {
        if (!result[item.service_name]) {
            result[item.service_name] = {
                playlist_cover_url: item.playlist_cover_url,
                playlist_cover_description_text: item.playlist_cover_description_text,
                playlist_name: item.playlist_name,
                playlist_url: item.playlist_url
            };
        }
    });

    return result;
}

async function handleMainPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const data = await fetchFromMongoDB('view_counts_playlists', { genre_name: genre }, env);
        await cacheAlbumCovers(data);
        return createJsonResponse(data);
    } catch (error) {
        return handleError(error);
    }
}

async function handleServicePlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    const service = searchParams.get('service');

    if (!genre || !service) {
        return new Response('Genre and service are required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const data = await fetchFromMongoDB('transformed_playlists', { genre_name: genre, service_name: service }, env);
        await cacheAlbumCovers(data);
        return createJsonResponse(data);
    } catch (error) {
        return handleError(error);
    }
}

async function handleLastUpdated(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const data = await fetchFromMongoDB('view_counts_playlists', { genre_name: genre }, env);
        if (data.length === 0) {
            return new Response('No data found for the specified genre', { status: 404, headers: { 'Access-Control-Allow-Origin': '*' } });
        }

        const lastUpdated = data[0].insert_timestamp;
        return createJsonResponse({ lastUpdated });
    } catch (error) {
        return handleError(error);
    }
}

async function cacheAlbumCovers(tracks: any[]): Promise<void> {
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

function createJsonResponse(data: any): Response {
    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
}

function handleError(error: Error): Response {
    console.error('Error handling request:', error);
    return new Response(`Error: ${error.message}`, {
        status: 500,
        headers: { 'Access-Control-Allow-Origin': '*' }
    });
}
