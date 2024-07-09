import { config } from 'dotenv';

config();

export default {
    async fetch(request: Request, env: any): Promise<Response> {
        if (request.method === 'OPTIONS') {
            return handleOptions(request);
        }

        try {
            const url = new URL(request.url);
            const pathname = url.pathname;
            const searchParams = url.searchParams;

            switch (pathname) {
                case '/api/aggregated-playlist':
                    return await handleAggregatedPlaylist(searchParams, env);
                case '/api/transformed-playlist':
                    return await handleTransformedPlaylist(searchParams, env);
                case '/api/last-updated':
                    return await handleLastUpdated();
                default:
                    return new Response('Hello World!', {
                        headers: { 'Access-Control-Allow-Origin': '*' }
                    });
            }
        } catch (error) {
            console.error('Error handling request:', error);
            return new Response(`Error: ${error.message}`, {
                status: 500,
                headers: { 'Access-Control-Allow-Origin': '*' }
            });
        }
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

    console.log('Request Payload:', requestPayload); 

    const response = await fetch(`${env.MONGO_DATA_API_ENDPOINT}/action/find`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'api-key': env.MONGO_DATA_API_KEY,
        },
        body: JSON.stringify(requestPayload),
    });

    console.log('MongoDB Response Status:', response.status); // Add logging
    if (!response.ok) {
        throw new Error(`Failed to fetch from MongoDB. Status: ${response.status}`);
    }

    const data = await response.json();
    console.log('MongoDB Response Data:', data); // Add logging
    return data.documents;
}

async function handleAggregatedPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    const data = await fetchFromMongoDB('aggregated_playlists', { genre_name: genre }, env);
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
    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
}

async function handleLastUpdated(): Promise<Response> {
    const data = { lastUpdated: new Date().toISOString() };
    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    });
}
