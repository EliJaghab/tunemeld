import { cacheAlbumCovers, createJsonResponse, fetchFromMongoDB, handleError } from "./utils";

// Cache configuration for different data types
const CACHE_TIMES = {
  GRAPH_DATA: 1800, // 30 minutes - view count data changes frequently
  PLAYLIST_DATA: 3600, // 1 hour - playlist data is relatively stable
  LAST_UPDATED: 300, // 5 minutes - timestamps need to be fresh
  HEADER_ART: 7200, // 2 hours - images rarely change
};

export async function handleGraphData(searchParams: URLSearchParams, env: any): Promise<Response> {
  const genre = searchParams.get("genre");
  if (!genre) {
    return new Response("Genre is required", { status: 400, headers: { "Access-Control-Allow-Origin": "*" } });
  }

  try {
    const playlists = await fetchFromMongoDB("view_counts_playlists", { genre_name: genre }, env);

    // Extract ISRCs and associated track details
    const isrcList = playlists
      .flatMap(playlist =>
        playlist.tracks.map((track: any) => ({
          isrc: track.isrc,
          track_name: track.track_name,
          artist_name: track.artist_name,
          youtube_url: track.youtube_url,
          album_cover_url: track.album_cover_url,
        }))
      )
      .filter(track => track.isrc);

    if (isrcList.length === 0) {
      return new Response("No ISRCs found for the specified genre", {
        status: 404,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    // Fetch view counts for the ISRCs
    const trackViewsQuery = {
      isrc: { $in: isrcList.map(track => track.isrc) },
    };
    const trackViews = await fetchFromMongoDB("historical_track_views", trackViewsQuery, env);

    // Map track views to the corresponding track details
    const responseData = isrcList.map(track => {
      const viewData = trackViews.find(view => view.isrc === track.isrc);

      const spotifyViews =
        viewData?.view_counts?.Spotify?.map((entry: any) => [entry.current_timestamp, entry.delta_count]) || [];
      const youtubeViews =
        viewData?.view_counts?.Youtube?.map((entry: any) => [entry.current_timestamp, entry.delta_count]) || [];

      return {
        isrc: track.isrc,
        track_name: track.track_name,
        artist_name: track.artist_name,
        youtube_url: track.youtube_url,
        album_cover_url: track.album_cover_url,
        view_counts: {
          Spotify: spotifyViews,
          Youtube: youtubeViews,
        },
      };
    });

    return createJsonResponse(responseData, CACHE_TIMES.GRAPH_DATA);
  } catch (error) {
    return handleError(error);
  }
}

export async function handleServicePlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
  const genre = searchParams.get("genre");
  const service = searchParams.get("service");

  if (!genre || !service) {
    return new Response("Genre and service are required", {
      status: 400,
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  }

  try {
    const data = await fetchFromMongoDB("transformed_playlists", { genre_name: genre, service_name: service }, env);
    await cacheAlbumCovers(data);
    return createJsonResponse(data, CACHE_TIMES.PLAYLIST_DATA);
  } catch (error) {
    return handleError(error);
  }
}

export async function handleMainPlaylist(searchParams: URLSearchParams, env: any): Promise<Response> {
  const genre = searchParams.get("genre");
  if (!genre) {
    return new Response("Genre is required", { status: 400, headers: { "Access-Control-Allow-Origin": "*" } });
  }

  try {
    const data = await fetchFromMongoDB("view_counts_playlists", { genre_name: genre }, env);
    await cacheAlbumCovers(data);
    return createJsonResponse(data, CACHE_TIMES.PLAYLIST_DATA);
  } catch (error) {
    return handleError(error);
  }
}

export async function handleLastUpdated(searchParams: URLSearchParams, env: any): Promise<Response> {
  const genre = searchParams.get("genre");
  if (!genre) {
    return new Response("Genre is required", { status: 400, headers: { "Access-Control-Allow-Origin": "*" } });
  }

  try {
    const data = await fetchFromMongoDB("view_counts_playlists", { genre_name: genre }, env);
    if (data.length === 0) {
      return new Response("No data found for the specified genre", {
        status: 404,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    const lastUpdated = data[0].insert_timestamp;
    return createJsonResponse({ lastUpdated }, CACHE_TIMES.LAST_UPDATED);
  } catch (error) {
    return handleError(error);
  }
}

export async function handleHeaderArt(searchParams: URLSearchParams, env: any): Promise<Response> {
  const genre = searchParams.get("genre");
  if (!genre) {
    return new Response("Genre is required", { status: 400, headers: { "Access-Control-Allow-Origin": "*" } });
  }

  try {
    const data = await fetchFromMongoDB("raw_playlists", { genre_name: genre }, env);
    const formattedData = formatPlaylistData(data);

    await cacheAlbumCovers(Object.values(formattedData));

    return createJsonResponse(formattedData, CACHE_TIMES.HEADER_ART);
  } catch (error) {
    return handleError(error);
  }
}

export async function handleCacheStatus(searchParams: URLSearchParams, env: any): Promise<Response> {
  try {
    const cache = caches.default;

    // Test cache functionality
    const testKey = "cache-test-" + Date.now();
    const testValue = { test: true, timestamp: new Date().toISOString() };
    const testRequest = new Request(`https://test.example.com/${testKey}`);
    const testResponse = new Response(JSON.stringify(testValue), {
      headers: { "Content-Type": "application/json" },
    });

    // Put test value in cache
    await cache.put(testRequest, testResponse.clone());

    // Try to retrieve it
    const cachedResponse = await cache.match(testRequest);
    const isCacheWorking = cachedResponse !== undefined;

    // Clean up test cache entry
    await cache.delete(testRequest);

    const status = {
      cache_working: isCacheWorking,
      cloudflare_edge_caching: true,
      cache_configuration: {
        graph_data_ttl: `${CACHE_TIMES.GRAPH_DATA}s (${CACHE_TIMES.GRAPH_DATA / 60}min)`,
        playlist_data_ttl: `${CACHE_TIMES.PLAYLIST_DATA}s (${CACHE_TIMES.PLAYLIST_DATA / 60}min)`,
        last_updated_ttl: `${CACHE_TIMES.LAST_UPDATED}s (${CACHE_TIMES.LAST_UPDATED / 60}min)`,
        header_art_ttl: `${CACHE_TIMES.HEADER_ART}s (${CACHE_TIMES.HEADER_ART / 60}min)`,
      },
      cache_headers_enabled: true,
      test_performed: new Date().toISOString(),
    };

    return createJsonResponse(status, 60); // Cache status for 1 minute
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
        playlist_url: item.playlist_url,
      };
    }
  });

  return result;
}
