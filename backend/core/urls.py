from core.api import cache_api, debug_cache_api, events_api, health_api, redis_debug_api
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from gql.schema import schema

# API-only endpoints - frontend served by Cloudflare Pages
urlpatterns = [
    path("api/health/", health_api.health, name="health"),
    path("health/", health_api.health, name="health_legacy"),
    path(
        "api/edm-events/",
        events_api.get_edm_events,
        name="get_edm_events",
    ),
    path(
        "edm-events/",
        events_api.get_edm_events,
        name="get_edm_events_legacy",
    ),
    path(
        "api/clear-redis-cache/",
        csrf_exempt(cache_api.clear_redis_cache),
        name="clear_redis_cache",
    ),
    path(
        "clear-redis-cache/",
        csrf_exempt(cache_api.clear_redis_cache),
        name="clear_redis_cache_legacy",
    ),
    path(
        "api/gql/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True)),
        name="graphql",
    ),
    path(
        "gql/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True)),
        name="graphql_legacy",
    ),
    # Custom GraphQL endpoint names for better Network tab debugging
    path(
        "api/GetInitialPageData/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_initial_page_data",
    ),
    path(
        "api/GetServicePlaylists/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_service_playlists",
    ),
    path(
        "api/GetAvailableGenres/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_available_genres",
    ),
    path(
        "api/GetPlaylistMetadata/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_playlist_metadata",
    ),
    path(
        "api/GetPlaylistTracks/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_playlist_tracks",
    ),
    path(
        "api/GetPlaylistRanks/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_playlist_ranks",
    ),
    path(
        "api/GetPlayCounts/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_play_counts",
    ),
    path(
        "api/GetServiceConfigs/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_service_configs",
    ),
    path(
        "api/GetIframeConfigs/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_iframe_configs",
    ),
    path(
        "api/GenerateIframeUrl/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_generate_iframe_url",
    ),
    path(
        "api/GetRankButtonLabels/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_rank_button_labels",
    ),
    path(
        "api/GetMiscButtonLabels/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False)),
        name="graphql_misc_button_labels",
    ),
    path(
        "api/debug-cache/",
        debug_cache_api.debug_cache_keys,
        name="debug_cache_keys",
    ),
    path(
        "api/redis-debug/",
        redis_debug_api.test_redis_cache,
        name="redis_debug_test",
    ),
    path(
        "api/clear-playlist-cache/",
        redis_debug_api.clear_playlist_cache,
        name="clear_playlist_cache",
    ),
    path(
        "api/check-individual-playlist-cache/",
        redis_debug_api.check_individual_playlist_cache,
        name="check_individual_playlist_cache",
    ),
]
