import { cacheAlbumCovers, createJsonResponse, fetchFromMongoDB, handleError } from './utils';

export async function handleGraphData(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const playlists = await fetchFromMongoDB('view_counts_playlists', { genre_name: genre }, env);

        // Extract ISRCs and associated track details
        const isrcList = playlists.flatMap(playlist => 
            playlist.tracks.map((track: any) => ({
                isrc: track.isrc,
                track_name: track.track_name,
                artist_name: track.artist_name,
                youtube_url: track.youtube_url,
                album_cover_url: track.album_cover_url
            }))
        ).filter(track => track.isrc); 

        if (isrcList.length === 0) {
            return new Response('No ISRCs found for the specified genre', { status: 404, headers: { 'Access-Control-Allow-Origin': '*' } });
        }

        // Fetch view counts for the ISRCs
        const trackViewsQuery = {
            isrc: { $in: isrcList.map(track => track.isrc) }
        };
        const trackViews = await fetchFromMongoDB('track_views', trackViewsQuery, env);

        // Map track views to the corresponding track details
        const responseData = isrcList.map(track => {
            const viewData = trackViews.find(view => view.isrc === track.isrc);

            const spotifyViews = viewData?.view_counts?.Spotify?.map((entry: any) => [entry.timestamp, entry.view_count]) || [];
            const youtubeViews = viewData?.view_counts?.Youtube?.map((entry: any) => [entry.timestamp, entry.view_count]) || [];

            return {
                isrc: track.isrc,
                track_name: track.track_name,
                artist_name: track.artist_name,
                youtube_url: track.youtube_url,
                album_cover_url: track.album_cover_url,
                view_counts: {
                    Spotify: spotifyViews,
                    Youtube: youtubeViews
                }
            };
        });

        return createJsonResponse(responseData);
    } catch (error) {
        return handleError(error);
    }
}


export async function handleServicePlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
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

export async function handleMainPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
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

export async function handleLastUpdated(searchParams: URLSearchParams, env: any): Promise<Response> {
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

export async function handleHeaderArt(searchParams: URLSearchParams, env: any): Promise<Response> {
    const genre = searchParams.get('genre');
    if (!genre) {
        return new Response('Genre is required', { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } });
    }

    try {
        const data = await fetchFromMongoDB('raw_playlists', { genre_name: genre }, env);
        const formattedData = formatPlaylistData(data);

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
